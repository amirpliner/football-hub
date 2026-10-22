#!/usr/bin/env python3
"""בודק רשימת פידי RSS: האם קיים, האם מתפרש, כמה כתבות, מתי הכתבה האחרונה, האם יש תמונות.

שימוש:
    python3 tools/check_feeds.py                # בודק את כל המועמדים
    python3 tools/check_feeds.py --league la_liga
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import email.utils
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

UA = "Mozilla/5.0 (compatible; PersonalFootballReader/1.0)"


class _Redirect308(urllib.request.HTTPRedirectHandler):
    """Python 3.9 לא עוקב אחרי הפניות 308 לבד."""
    def http_error_308(self, req, fp, code, msg, headers):
        return self.http_error_302(req, fp, 302, msg, headers)


urllib.request.install_opener(urllib.request.build_opener(_Redirect308))
TIMEOUT = 20

# (liga, שם מקור, סוג, כתובת)   סוג: general = חדשות כלליות, fan = בלוג אוהדים, tactics = ניתוח טקטי
CANDIDATES = [
    # ---- פרמייר ליג ----
    ("premier_league", "BBC Sport", "general", "https://feeds.bbci.co.uk/sport/football/premier-league/rss.xml"),
    ("premier_league", "Guardian", "general", "https://www.theguardian.com/football/premierleague/rss"),
    ("premier_league", "Sky Sports", "general", "https://www.skysports.com/rss/12040"),
    ("premier_league", "Arseblog", "fan", "https://arseblog.com/feed/"),
    ("premier_league", "The Liverpool Offside", "fan", "https://www.theliverpooloffside.com/feed/"),
    ("premier_league", "Stretty News (Man Utd)", "fan", "https://strettynews.com/feed/"),
    ("premier_league", "We Ain't Got No History (Chelsea)", "fan", "https://weaintgotnohistory.sbnation.com/rss/index.xml"),
    ("premier_league", "Cartilage Free Captain (Spurs)", "fan", "https://www.cartilagefreecaptain.com/rss/index.xml"),
    ("premier_league", "Cityzens Eyes? / Bitter and Blue", "fan", "https://www.bitterandblue.com/rss/index.xml"),
    # ---- לה ליגה ----
    ("la_liga", "Guardian", "general", "https://www.theguardian.com/football/laligafootball/rss"),
    ("la_liga", "AS English", "general", "https://en.as.com/rss/tags/ultimas_noticias.xml"),
    ("la_liga", "Marca English", "general", "https://e00-marca.uecdn.es/rss/en/football/la-liga.xml"),
    ("la_liga", "Barca Blaugranes", "fan", "https://www.barcablaugranes.com/rss/index.xml"),
    ("la_liga", "Managing Madrid", "fan", "https://www.managingmadrid.com/rss/index.xml"),
    ("la_liga", "Into the Calderon (Atleti)", "fan", "https://www.intothecalderon.com/rss/index.xml"),
    ("la_liga", "Sport (Barca news)", "general", "https://www.sport.es/en/rss/football/rss.xml"),
    # ---- סרייה A ----
    ("serie_a", "Guardian", "general", "https://www.theguardian.com/football/serieafootball/rss"),
    ("serie_a", "Football Italia", "general", "https://football-italia.net/feed/"),
    ("serie_a", "Black & White & Read All Over (Juve)", "fan", "https://www.bwwsports.com/feed/"),
    ("serie_a", "Black & White (SBN Juve)", "fan", "https://www.blackwhitereadallover.com/rss/index.xml"),
    ("serie_a", "Forza Italian Football", "general", "https://forzaitalianfootball.com/feed/"),
    ("serie_a", "The Laziali / Lazio", "fan", "https://www.thelaziali.com/feed/"),
    ("serie_a", "Gazzetta dello Sport", "general", "https://www.gazzetta.it/rss/calcio.xml"),
    # ---- בונדסליגה ----
    ("bundesliga", "Guardian (Bundesliga)", "general", "https://www.theguardian.com/football/bundesligafootball/rss"),
    ("bundesliga", "Bavarian Football Works", "fan", "https://www.bavarianfootballworks.com/rss/index.xml"),
    ("bundesliga", "Der Spielmacher? / Get German Football News", "general", "https://www.getfootballnewsgermany.com/feed/"),
    ("bundesliga", "Bundesliga.com", "general", "https://www.bundesliga.com/en/bundesliga/news/rss"),
    ("bundesliga", "kicker", "general", "https://newsfeed.kicker.de/news/aktuell"),
    ("bundesliga", "Fear The Wall (Dortmund)", "fan", "https://www.fearthewall.com/rss/index.xml"),
    ("bundesliga", "Sportschau Fussball", "general", "https://www.sportschau.de/fussball/index~rss2.xml"),
    # ---- ליג 1 ----
    ("ligue_1", "Guardian (Ligue 1)", "general", "https://www.theguardian.com/football/ligue1football/rss"),
    ("ligue_1", "Get French Football News", "general", "https://www.getfootballnewsfrance.com/feed/"),
    ("ligue_1", "Get French Football News (alt)", "general", "https://www.getfrenchfootballnews.com/feed/"),
    ("ligue_1", "Canal Supporters (PSG)", "fan", "https://canal-supporters.com/feed/"),
    ("ligue_1", "L'Equipe Football", "general", "https://dwh.lequipe.fr/api/edito/rss?path=/Football/"),
    ("ligue_1", "France Football? / Foot Mercato", "general", "https://www.footmercato.net/rss"),
    ("ligue_1", "Peoples PSG (Paris United)", "fan", "https://www.psg-talk.com/feed/"),
    # ---- צ'מפיונשיפ ----
    ("championship", "BBC Sport", "general", "https://feeds.bbci.co.uk/sport/football/championship/rss.xml"),
    ("championship", "Sky Sports", "general", "https://www.skysports.com/rss/12206"),
    ("championship", "Guardian (EFL)", "general", "https://www.theguardian.com/football/championship/rss"),
    ("championship", "Leeds Rhinos? / Leeds United (Square Ball)", "fan", "https://www.thesquareball.net/feed/"),
    ("championship", "Fosse Posse? / Blog Leicester", "fan", "https://www.foxestalk.co.uk/feed/"),
    ("championship", "Football League World", "general", "https://www.footballleagueworld.co.uk/feed/"),
    # ---- ליגה פורטוגלית ----
    ("liga_portugal", "Guardian (Portugal)", "general", "https://www.theguardian.com/football/portugal/rss"),
    ("liga_portugal", "A Bola", "general", "https://www.abola.pt/rss"),
    ("liga_portugal", "Record", "general", "https://www.record.pt/rss"),
    ("liga_portugal", "O Jogo", "general", "https://www.ojogo.pt/rss"),
    ("liga_portugal", "Maisfutebol", "general", "https://maisfutebol.iol.pt/rss"),
    ("liga_portugal", "Portuguese Football Zone? / Sporting Online", "fan", "https://www.portuguesesoccer.com/feed/"),
    ("liga_portugal", "Portugoal / Portugal Football", "general", "https://www.portugalfootball.net/feed/"),
    # ---- ארדיביזי ----
    ("eredivisie", "NOS Voetbal", "general", "https://feeds.nos.nl/nosvoetbal"),
    ("eredivisie", "Voetbalzone", "general", "https://www.voetbalzone.nl/rss/nieuws.asp"),
    ("eredivisie", "Voetbal International", "general", "https://www.vi.nl/rss/nieuws"),
    ("eredivisie", "Dutch Soccer Podcast? / Dutch Football", "general", "https://dutchsoccer.net/feed/"),
    ("eredivisie", "Guardian (Dutch)", "general", "https://www.theguardian.com/football/eredivisie/rss"),
    ("eredivisie", "Ajax Daily", "fan", "https://ajaxdaily.com/feed/"),
    ("eredivisie", "Ajax Life / Eredivisie English", "general", "https://eredivisie.nl/en/rss"),
    # ---- ליגת האלופות ----
    ("champions_league", "Guardian", "general", "https://www.theguardian.com/football/championsleague/rss"),
    ("champions_league", "BBC Sport", "general", "https://feeds.bbci.co.uk/sport/football/champions-league/rss.xml"),
    ("champions_league", "Sky Sports", "general", "https://www.skysports.com/rss/12040"),
    ("champions_league", "UEFA.com", "general", "https://www.uefa.com/rssfeed/uefachampionsleague/rss.xml"),
    # ---- טקטיקה / ניתוח (כללי) ----
    ("tactics", "Zonal Marking", "tactics", "https://www.zonalmarking.net/feed/"),
    ("tactics", "Total Football Analysis", "tactics", "https://totalfootballanalysis.com/feed"),
    ("tactics", "Spielverlagerung", "tactics", "https://spielverlagerung.com/feed/"),
    ("tactics", "The Analyst", "tactics", "https://theanalyst.com/feed"),
    ("tactics", "Tifo Football", "tactics", "https://tifofootball.com/feed/"),
    ("tactics", "Outside of the Boot", "tactics", "https://outsideoftheboot.com/feed/"),
    ("tactics", "Training Ground Guru", "tactics", "https://trainingground.guru/feed"),
    ("tactics", "Coaches' Voice", "tactics", "https://www.coachesvoice.com/feed/"),
    ("tactics", "Statsbomb", "tactics", "https://statsbomb.com/feed/"),
    ("tactics", "The Athletic (football)", "tactics", "https://theathletic.com/rss-feed/"),
    ("tactics", "Guardian Football (כללי)", "general", "https://www.theguardian.com/football/rss"),
    ("tactics", "BBC Football (כללי)", "general", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
]


def strip_ns(tag):
    return tag.split("}", 1)[-1]


def parse_date(text):
    if not text:
        return None
    text = text.strip()
    try:
        d = email.utils.parsedate_to_datetime(text)
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d
    except Exception:
        pass
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def inspect_feed(root):
    """מחזיר (מספר פריטים, תאריך אחרון, יש תמונות, יש תקציר, כותרת הפיד)."""
    kind = strip_ns(root.tag)
    items = []
    if kind == "rss":
        items = [e for e in root.iter() if strip_ns(e.tag) == "item"]
    elif kind == "feed":
        items = [e for e in root.iter() if strip_ns(e.tag) == "entry"]
    elif kind == "RDF":
        items = [e for e in root.iter() if strip_ns(e.tag) == "item"]
    else:
        return None
    title = ""
    for e in root.iter():
        if strip_ns(e.tag) == "title":
            title = (e.text or "").strip()
            break
    newest = None
    has_img = 0
    has_desc = 0
    for it in items:
        xml = ET.tostring(it, encoding="unicode")
        if re.search(r"<(\w+:)?(thumbnail|content|enclosure)[^>]+(url|href)=", xml) or "<img" in xml or ".jpg" in xml or ".png" in xml or ".webp" in xml:
            has_img += 1
        for ch in it:
            n = strip_ns(ch.tag)
            if n in ("pubDate", "published", "updated", "date"):
                d = parse_date(ch.text)
                if d and (newest is None or d > newest):
                    newest = d
            if n in ("description", "summary") and (ch.text or "").strip():
                has_desc += 1
    return len(items), newest, has_img, has_desc, title


def check(candidate):
    league, name, kind, url = candidate
    res = {"league": league, "name": name, "kind": kind, "url": url}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read()
            res["http"] = r.status
            res["final_url"] = r.geturl()
    except Exception as e:
        res["ok"] = False
        res["error"] = f"{type(e).__name__}: {e}"[:120]
        return res
    try:
        root = ET.fromstring(body)
    except Exception as e:
        res["ok"] = False
        res["error"] = f"לא XML תקין ({str(e)[:50]}); תחילת התוכן: {body[:60]!r}"
        return res
    info = inspect_feed(root)
    if info is None:
        res["ok"] = False
        res["error"] = f"XML אבל לא פיד (root={strip_ns(root.tag)})"
        return res
    n, newest, img, desc, title = info
    now = dt.datetime.now(dt.timezone.utc)
    res.update(ok=n > 0, items=n, with_images=img, with_summary=desc, feed_title=title[:60])
    if newest:
        res["newest"] = newest.astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
        res["age_days"] = round((now - newest).total_seconds() / 86400, 1)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--league")
    ap.add_argument("--out", default="tools/feed_check_report.json")
    args = ap.parse_args()
    cands = [c for c in CANDIDATES if not args.league or c[0] == args.league]
    with cf.ThreadPoolExecutor(max_workers=12) as ex:
        results = list(ex.map(check, cands))
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    cur = None
    for r in results:
        if r["league"] != cur:
            cur = r["league"]
            print(f"\n=== {cur} ===")
        if r.get("ok"):
            age = r.get("age_days")
            stale = " (ישן!)" if age is not None and age > 14 else ""
            print(f"  OK   {r['name']:<42} {r['items']:>3} כתבות | תמונות {r['with_images']}/{r['items']} | תקציר {r['with_summary']}/{r['items']} | אחרונה לפני {age} ימים{stale}")
        else:
            print(f"  FAIL {r['name']:<42} {r.get('error')}")
    ok = sum(1 for r in results if r.get("ok"))
    print(f"\nסה\"כ: {ok}/{len(results)} עובדים")


if __name__ == "__main__":
    sys.exit(main())
