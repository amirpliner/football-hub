#!/usr/bin/env python3
"""אוסף כתבות מפידי RSS לפי config/config.json ושומר ל-data/articles.json.

שימוש:
    python3 scripts/collect.py                 # הרצה רגילה
    python3 scripts/collect.py --dry-run       # בלי לכתוב קבצים
    python3 scripts/collect.py --only bbc-pl   # רק מקור אחד (לבדיקות)

הסקריפט משתמש רק בספריית הסטנדרט של Python, אין מה להתקין.
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import email.utils
import hashlib
import html
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "config.json"
DATA_DIR = ROOT / "data"
ARTICLES_PATH = DATA_DIR / "articles.json"
STATUS_PATH = DATA_DIR / "status.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


class _Redirect308(urllib.request.HTTPRedirectHandler):
    """Python 3.9 לא עוקב אחרי הפניות 308 לבד."""
    def http_error_308(self, req, fp, code, msg, headers):
        return self.http_error_302(req, fp, 302, msg, headers)


urllib.request.install_opener(urllib.request.build_opener(_Redirect308))

NOW = dt.datetime.now(dt.timezone.utc)


# ---------- עזרים ----------

def local(tag):
    return tag.split("}", 1)[-1] if isinstance(tag, str) else ""


def parse_date(text):
    if not text:
        return None
    text = text.strip()
    try:
        d = email.utils.parsedate_to_datetime(text)
    except Exception:
        d = None
    if d is None:
        try:
            d = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        except Exception:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in ("p", "br", "div", "li"):
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def html_to_text(raw):
    if not raw:
        return ""
    p = _TextExtractor()
    try:
        p.feed(raw)
        p.close()
        text = "".join(p.parts)
    except Exception:
        text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    # שאריות נפוצות של וורדפרס
    text = re.sub(r"\s*The post .{0,200}? appeared first on .{0,100}$", "", text)
    text = re.sub(r"\s*(Continue reading|Read more|Read the full story)[^a-zA-Z]*$", "", text, flags=re.I)
    return text.strip()


def truncate(text, limit):
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(" ,.;:-–—") + "…"


def ts(iso):
    """'2026-10-22T10:00:00Z' -> datetime (פייתון 3.9 לא מכיר Z)."""
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))


def canonical_link(url):
    try:
        u = urllib.parse.urlsplit(url.strip())
    except Exception:
        return url
    q = [(k, v) for k, v in urllib.parse.parse_qsl(u.query)
         if not k.lower().startswith(("utm_", "fbclid", "gclid", "ref", "cmp", "ito", "xtor"))]
    path = u.path.rstrip("/") or "/"
    scheme = "https" if u.scheme in ("http", "https") else u.scheme
    return urllib.parse.urlunsplit((scheme, u.netloc.lower(), path, urllib.parse.urlencode(q), ""))


def item_id(link):
    return hashlib.sha1(canonical_link(link).encode("utf-8")).hexdigest()[:12]


def fix_image(url, base):
    if not url:
        return None
    url = html.unescape(url.strip())
    if url.startswith("data:"):
        return None
    url = urllib.parse.urljoin(base, url)
    if url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    return url


# ---------- הורדה ופענוח ----------

def fetch(url, timeout):
    last = None
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*;q=0.5",
            })
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(1.5)
    raise last


_BAD_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f]")


def parse_xml(body):
    try:
        return ET.fromstring(body)
    except ET.ParseError:
        text = body.decode("utf-8", errors="replace")
        text = _BAD_XML.sub("", text)
        text = re.sub(r"^\s*<\?xml[^>]*\?>", "", text)
        # אמפרסנד שבור שלא הפך לישות
        text = re.sub(r"&(?!(?:[a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);)", "&amp;", text)
        return ET.fromstring(text.encode("utf-8"))


_CDATA = re.compile(r"^\s*<!\[CDATA\[(.*?)\]\]>\s*$", re.S)


def child_text(el, *names):
    for ch in el:
        if local(ch.tag) in names and (ch.text or "").strip():
            text = ch.text.strip()
            m = _CDATA.match(text)  # יש פידים שמעטפת CDATA מגיעה בתוכם כטקסט רגיל
            return m.group(1).strip() if m else text
    return ""


def extract_image(el, body_html, base):
    for ch in el.iter():
        n = local(ch.tag)
        if n == "thumbnail" and ch.get("url"):
            return fix_image(ch.get("url"), base)
    for ch in el.iter():
        n = local(ch.tag)
        if n == "content" and ch.get("url"):
            typ = (ch.get("type") or ch.get("medium") or "").lower()
            if typ.startswith("image") or re.search(r"\.(jpe?g|png|webp|gif)(\?|$)", ch.get("url"), re.I):
                return fix_image(ch.get("url"), base)
        if n == "enclosure" and ch.get("url"):
            typ = (ch.get("type") or "").lower()
            if typ.startswith("image") or re.search(r"\.(jpe?g|png|webp|gif)(\?|$)", ch.get("url"), re.I):
                return fix_image(ch.get("url"), base)
    m = re.search(r"<img[^>]+src=[\"']([^\"']+)[\"']", body_html or "", re.I)
    if m:
        return fix_image(m.group(1), base)
    return None


def parse_feed(root, source, summary_max):
    kind = local(root.tag)
    entries = []
    if kind in ("rss", "RDF"):
        entries = [e for e in root.iter() if local(e.tag) == "item"]
    elif kind == "feed":
        entries = [e for e in root.iter() if local(e.tag) == "entry"]
    else:
        raise ValueError(f"לא פיד (root={kind})")

    out = []
    for e in entries:
        title = html_to_text(child_text(e, "title"))
        link = child_text(e, "link")
        if not link:  # Atom
            for ch in e:
                if local(ch.tag) == "link" and ch.get("href") and ch.get("rel", "alternate") == "alternate":
                    link = ch.get("href")
                    break
        if not title or not link:
            continue
        link = link.strip()
        desc_raw = child_text(e, "description", "summary")
        content_raw = child_text(e, "encoded", "content")
        body_html = content_raw or desc_raw
        summary = html_to_text(desc_raw or content_raw)
        if summary.lower() == title.lower():
            summary = ""
        published = parse_date(child_text(e, "pubDate", "published", "updated", "date"))
        out.append({
            "title": title,
            "link": link,
            "summary": truncate(summary, summary_max),
            "image": extract_image(e, body_html, link),
            "published": published,
        })
    return out


# ---------- זיהוי קבוצות וליגות ----------

class Matcher:
    def __init__(self, cfg):
        self.replacements = cfg.get("text_replacements", {})
        self.cl_re = self._compile(cfg.get("champions_league_keywords", []))
        self.team_re = {}      # team_id -> regex
        self.team_league = {}  # team_id -> league_id
        for lid, league in cfg["leagues"].items():
            for tid, team in league.get("teams", {}).items():
                if tid in self.team_re:
                    raise SystemExit(f"מזהה קבוצה כפול בקובץ ההגדרות: {tid}")
                self.team_re[tid] = self._compile(team["aliases"])
                self.team_league[tid] = lid

    @staticmethod
    def _compile(words):
        if not words:
            return None
        alt = "|".join(re.escape(w) for w in sorted(set(words), key=len, reverse=True))
        # רגיש לאותיות גדולות/קטנות בכוונה: "Sporting" ולא "sporting director"
        return re.compile(r"(?<!\w)(?:%s)(?!\w)" % alt)

    def analyze(self, text):
        for old, new in self.replacements.items():
            text = text.replace(old, new)
        teams = [tid for tid, rx in self.team_re.items() if rx.search(text)]
        is_cl = bool(self.cl_re and self.cl_re.search(text))
        return teams, is_cl


# ---------- איחוד כפילויות ----------

_STOP = set("""the and for with from this that has have are was were will its his her their after before over into out
 not but who what when how why new vs de la le el il lo los las les du des di da del della dei van het een der die das
 und von mit zu im ein eine para por con una uno che per sul sui sulla dopo avant apres pour dans sur une est les
 dos das uma que com nos nas sao em ao aos voor met bij naar over
 champions league premier liga serie bundesliga ligue uefa happened live blog liveblog prediction preview""".split())

_PREVIEW = re.compile(r"\b(prediction|preview|odds|tips|vorschau|pronostic|pron[oó]stico|previa|anteprima|voorbeschouwing|probable)\b", re.I)
_LIVE = re.compile(r"(as it happened|live ?blog|minute by minute|\blive\b|en directo|diretta|\bdirect\b|ao minuto)", re.I)


def title_kind(title):
    if _PREVIEW.search(title):
        return "preview"
    if _LIVE.search(title):
        return "live"
    return "news"


def title_tokens(title):
    t = unicodedata.normalize("NFKD", title.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return {w for w in re.findall(r"[a-z0-9]+", t) if len(w) > 2 and w not in _STOP}


def similar(a, b):
    if len(a) < 3 or len(b) < 3:
        return False
    inter = len(a & b)
    return (inter >= 3 and inter / len(a | b) >= 0.6) or (inter >= 5 and inter / min(len(a), len(b)) >= 0.7)


def dedupe(items, window_hours, priority):
    """מסמן dup_of בכפילויות ומוסיף also לפריט הראשי.

    משווים כל כתבה רק לכתבה הראשונה (הוותיקה) בכל קבוצה, כדי שלא יווצרו שרשראות
    של כתבות שדומות רק זו לזו. מאחדים רק בין מקורות שונים ורק מאותו סוג
    (חדשות / תחזית-תצוגה מקדימה / לייב), כי "תחזית" ו"סיכום" של אותו משחק הם לא כפילות.
    """
    for it in items:
        it["dup_of"] = None
        it.pop("also", None)
    window = dt.timedelta(hours=window_hours).total_seconds()
    groups = []  # כל קבוצה: dict(seed, tokens, kind, ts, members)
    for it in sorted(items, key=lambda i: i["published"]):
        t = ts(it["published"]).timestamp()
        toks = title_tokens(it["title"])
        kind = title_kind(it["title"])
        link = canonical_link(it["link"])
        teams = set(it["teams"])
        home = None
        for g in groups:
            if t - g["ts"] > window or g["kind"] != kind:
                continue
            if any(m["source_id"] == it["source_id"] for m in g["members"]):
                continue
            # אם בשתיהן זוהו קבוצות, חייבת להיות ביניהן חפיפה (נגד כותרות-תבנית כמו "How to watch")
            if g["teams"] and teams and not (g["teams"] & teams):
                continue
            if link == g["link"] or similar(toks, g["tokens"]):
                home = g
                break
        if home:
            home["members"].append(it)
        else:
            groups.append({"tokens": toks, "kind": kind, "ts": t, "link": link, "teams": teams, "members": [it]})
    n_dups = 0
    for g in groups:
        members = g["members"]
        if len(members) == 1:
            continue
        members.sort(key=lambda i: (priority.get(i["source_id"], 5), i["published"]))
        main = members[0]
        main["also"] = []
        for other in members[1:]:
            other["dup_of"] = main["id"]
            main["also"].append({"source": other["source"], "title": other["title"], "link": other["link"]})
            n_dups += 1
    return n_dups


# ---------- הרצה ראשית ----------

def process_source(src, cfg, matcher):
    s = cfg["settings"]
    res = {"id": src["id"], "name": src["name"], "url": src["url"], "ok": False}
    try:
        body = fetch(src["url"], s["fetch_timeout_seconds"])
        root = parse_xml(body)
        entries = parse_feed(root, src, s["summary_max_chars"])
    except Exception as e:
        res["error"] = f"{type(e).__name__}: {e}"[:200]
        return res, []

    res["ok"] = True
    res["fetched"] = len(entries)
    cutoff = NOW - dt.timedelta(days=s["keep_days"])
    fixed_leagues = set(src.get("leagues", []))
    match_leagues = set(src.get("match_leagues", []))
    kept = []
    for e in entries:
        published = e["published"] or NOW
        if published > NOW + dt.timedelta(hours=2):
            published = NOW
        if published < cutoff:
            continue
        teams, is_cl = matcher.analyze(e["title"] + " " + e["summary"])
        leagues = set(fixed_leagues)
        if match_leagues:
            matched = [t for t in teams if matcher.team_league[t] in match_leagues]
            if not matched:
                continue
            leagues |= {matcher.team_league[t] for t in matched}
            teams = matched + [t for t in teams if t not in matched]
        elif not fixed_leagues:  # keep_unmatched / ניתוח: ליגות לפי הקבוצות שהוזכרו
            leagues |= {matcher.team_league[t] for t in teams}
        if is_cl:
            leagues.add("champions_league")
        for t in src.get("teams", []):
            if t not in teams:
                teams.insert(0, t)
        kept.append({
            "id": item_id(e["link"]),
            "title": e["title"],
            "summary": e["summary"],
            "link": e["link"],
            "image": e["image"],
            "published": published.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_id": src["id"],
            "source": src["name"],
            "category": src.get("category", "news"),
            "lang": src.get("lang", "en"),
            "leagues": sorted(leagues),
            "teams": teams,
        })
    res["kept"] = len(kept)
    newest = max((e["published"] for e in entries if e["published"]), default=None)
    res["newest"] = newest.strftime("%Y-%m-%dT%H:%M:%SZ") if newest else None
    return res, kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="מזהה מקור אחד (id) להרצה")
    args = ap.parse_args()

    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    s = cfg["settings"]
    matcher = Matcher(cfg)

    sources = [x for x in cfg["sources"] if x.get("enabled", True)]
    ids = [x["id"] for x in cfg["sources"]]
    if len(ids) != len(set(ids)):
        raise SystemExit("יש id כפול ברשימת המקורות")
    for x in sources:
        for lid in x.get("leagues", []) + x.get("match_leagues", []):
            if lid not in cfg["leagues"]:
                raise SystemExit(f"מקור {x['id']}: ליגה לא מוכרת {lid}")
    if args.only:
        sources = [x for x in sources if x["id"] == args.only]
        if not sources:
            raise SystemExit(f"אין מקור פעיל בשם {args.only}")

    priority = {x["id"]: x.get("priority", 5) for x in cfg["sources"]}

    with cf.ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(lambda x: process_source(x, cfg, matcher), sources))

    # מיזוג עם מה ששמור מהריצות הקודמות
    existing = {}
    if ARTICLES_PATH.exists():
        try:
            old = json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))
            for it in old.get("items", []):
                existing[it["id"]] = it
        except Exception as e:
            print(f"אזהרה: לא הצלחתי לקרוא articles.json הקיים ({e}); מתחיל מחדש")

    active_ids = {x["id"] for x in cfg["sources"] if x.get("enabled", True)}
    merged = {k: v for k, v in existing.items() if v["source_id"] in active_ids}

    new_count = 0
    for res, kept in results:
        for it in kept:
            prev = merged.get(it["id"])
            it["first_seen"] = prev["first_seen"] if prev else NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
            if not prev:
                new_count += 1
            merged[it["id"]] = it

    cutoff = NOW - dt.timedelta(days=s["keep_days"])
    items = [it for it in merged.values()
             if ts(it["published"]) >= cutoff]
    n_dups = dedupe(items, s["dedup_window_hours"], priority)
    items.sort(key=lambda i: i["published"], reverse=True)

    ok = [r for r, _ in results if r["ok"]]
    failed = [r for r, _ in results if not r["ok"]]
    stamp = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"מקורות: {len(ok)} הצליחו, {len(failed)} נכשלו")
    for r in failed:
        print(f"  נכשל: {r['id']:<22} {r['error']}")
    print(f"כתבות חדשות בריצה: {new_count} | סה\"כ שמורות: {len(items)} | כפילויות שאוחדו: {n_dups}")
    for r, _ in sorted(results, key=lambda x: x[0]["id"]):
        if r["ok"] and r["kept"] == 0:
            print(f"  שים לב: {r['id']} החזיר {r['fetched']} אבל 0 נשמרו (סינון/ישן)")

    if args.dry_run:
        return 0
    if not ok:
        print("כל המקורות נכשלו, לא דורס את הקבצים הקיימים")
        return 1

    DATA_DIR.mkdir(exist_ok=True)
    ARTICLES_PATH.write_text(json.dumps(
        {"generated_at": stamp, "keep_days": s["keep_days"], "items": items},
        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    # סטטוס של כל מקור; בהרצה חלקית משמרים את השאר
    prev_status = {}
    if args.only and STATUS_PATH.exists():
        try:
            prev_status = {r["id"]: r for r in json.loads(STATUS_PATH.read_text(encoding="utf-8")).get("sources", [])}
        except Exception:
            pass
    for r, _ in results:
        r["checked_at"] = stamp
        prev_status[r["id"]] = r
    STATUS_PATH.write_text(json.dumps(
        {"generated_at": stamp, "sources": sorted(prev_status.values(), key=lambda r: r["id"])},
        ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
