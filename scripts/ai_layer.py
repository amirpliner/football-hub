#!/usr/bin/env python3
"""שכבת Claude: תקצירים בעברית, "על מה לשים לב", ניתוח משחק, ומושג טקטי שבועי.

כותב ל-data/ai.json ול-data/ai_usage.json (מונה עלות אמיתי לפי חודש).
מושבת עד שב-config/config.json מוגדר ai.enabled=true ויש ANTHROPIC_API_KEY.

שימוש:
    python3 scripts/ai_layer.py --estimate         # הערכת עלות חודשית מהנתונים האמיתיים (בלי קריאות API)
    python3 scripts/ai_layer.py --dry-run          # בונה את הפרומפטים ומדפיס גודל, בלי קריאות API
    python3 scripts/ai_layer.py --mock             # כותב טקסטים מזויפים ל-ai.json, לבדיקת האתר בלבד
    python3 scripts/ai_layer.py                    # הרצה אמיתית (עולה כסף)
    python3 scripts/ai_layer.py --only summaries   # משימה אחת: summaries / preview / analysis / concept
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import collect  # noqa: E402

DATA = collect.DATA_DIR
AI_PATH = DATA / "ai.json"
USAGE_PATH = DATA / "ai_usage.json"
ESPN_CODES = {
    "premier_league": "eng.1", "la_liga": "esp.1", "serie_a": "ita.1", "bundesliga": "ger.1",
    "ligue_1": "fra.1", "championship": "eng.2", "liga_portugal": "por.1", "eredivisie": "ned.1",
    "champions_league": "uefa.champions",
}
JOBS = ("summaries", "preview", "analysis", "concept")

# ---------- פרומפטים ----------
COMMON = (
    "You write for a single Hebrew-speaking football fan who wants depth and angles other people miss. "
    "Write in natural, concise Hebrew (names of players/clubs in their common Hebrew spelling, or Latin script if unsure). "
    "Use ONLY the facts in the data you are given. Never invent lineups, quotes, formations, injuries, or events. "
    "If the data cannot support a claim, say so or leave it out. Prefer specific observations over generic phrases."
)
SYS_SUMMARY = COMMON + (
    " Task: for each article (title + feed snippet, often in another language) write a 1-2 sentence neutral Hebrew summary "
    "of what the article says. No opinions, no added facts. Return JSON only."
)
SYS_PREVIEW = COMMON + (
    " Task: a pre-match note titled 'what to watch'. Give 3 specific points grounded in the standings, recent form "
    "(form string: newest result on the right, W/D/L) and the recent news snippets. Each point: a short title and 1-2 sentences. "
    "Do not predict a score."
)
SYS_ANALYSIS = COMMON + (
    " Task: a short tactical/statistical read of a finished match from the box-score stats, key events and match-report snippets. "
    "Explain what the numbers and event timeline suggest (control vs. efficiency, game state effects, set pieces, discipline). "
    "You cannot see the match: state clearly in 'caveat' what the data cannot show, and do not claim specific tactical shapes unless the data says so."
)
SYS_CONCEPT = COMMON + (
    " Task: 'tactical concept of the week'. Pick ONE tactical concept (e.g. pressing triggers, half-spaces, rest defence, low block) "
    "that the supplied data from this week's matches and analysis articles can illustrate. Explain it simply, then give an example "
    "taken ONLY from the supplied match facts (cite the match and minute from the key events if you use one) and say honestly how "
    "well the data supports the link. Add 'how_to_spot': what to look for when watching."
)

SCHEMAS = {
    "summaries": {"type": "object", "properties": {"summaries": {"type": "array", "items": {
        "type": "object", "properties": {"id": {"type": "string"}, "he": {"type": "string"}},
        "required": ["id", "he"], "additionalProperties": False}}}, "required": ["summaries"], "additionalProperties": False},
    "preview": {"type": "object", "properties": {
        "headline": {"type": "string"},
        "points": {"type": "array", "items": {"type": "object", "properties": {"title": {"type": "string"}, "text": {"type": "string"}},
                                              "required": ["title", "text"], "additionalProperties": False}}},
        "required": ["headline", "points"], "additionalProperties": False},
    "analysis": {"type": "object", "properties": {
        "headline": {"type": "string"}, "summary": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}}, "caveat": {"type": "string"}},
        "required": ["headline", "summary", "key_points", "caveat"], "additionalProperties": False},
    "concept": {"type": "object", "properties": {
        "concept": {"type": "string"}, "explanation": {"type": "string"}, "example": {"type": "string"},
        "how_to_spot": {"type": "string"}, "data_support": {"type": "string"}},
        "required": ["concept", "explanation", "example", "how_to_spot", "data_support"], "additionalProperties": False},
}


# ---------- קבצים ----------
def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path, obj, indent=None):
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=None if indent else (",", ":"), indent=indent), encoding="utf-8")


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def ts(iso):
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))


# ---------- בחירת קלט ----------
def team_rank(standings, league, side):
    for table in standings.get(league, []):
        for r in table["rows"]:
            if (side.get("team_id") and r.get("team_id") == side["team_id"]) or r["team"] == side["name"]:
                return r
    return None


def is_big(m, standings, top_rank):
    if m["league"] == "champions_league":
        return True
    a, b = team_rank(standings, m["league"], m["home"]), team_rank(standings, m["league"], m["away"])
    return bool(a and b and a["rank"] <= top_rank and b["rank"] <= top_rank)


def team_snippets(items, team_id, since, limit=6):
    if not team_id:
        return []
    out = []
    for i in items:
        if i["category"] != "video" and not i["dup_of"] and team_id in i["teams"] and ts(i["published"]) >= since:
            out.append(f"- {i['title']} :: {i['summary'][:160]}")
            if len(out) >= limit:
                break
    return out


def preview_prompt(m, standings, items):
    def side(s):
        r = team_rank(standings, m["league"], s)
        row = f"table: #{r['rank']} {r['pts']}pts, {r['gp']} played, GD {r['gd']:+d}, GF {r['gf']} GA {r['ga']}" if r else "table: n/a"
        return f"{s['name']} | {row} | form: {s.get('form') or 'n/a'}"
    since = now_utc() - dt.timedelta(days=3)
    lines = [f"Match: {m['home']['name']} (home) vs {m['away']['name']} (away), {m['league']}, kickoff {m['date']}",
             "HOME " + side(m["home"]), "AWAY " + side(m["away"]), "", "Recent news snippets (home):"]
    lines += team_snippets(items, m["home"].get("team_id"), since) or ["- none"]
    lines += ["Recent news snippets (away):"] + (team_snippets(items, m["away"].get("team_id"), since) or ["- none"])
    return "\n".join(lines)


_STAT_KEYS = ["possessionPct", "totalShots", "shotsOnTarget", "wonCorners", "foulsCommitted", "yellowCards", "redCards",
              "accuratePasses", "totalPasses", "accurateCrosses", "totalCrosses", "totalTackles", "interceptions", "saves", "offsides", "accurateLongBalls", "totalLongBalls"]


def fetch_facts(m):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{ESPN_CODES[m['league']]}/summary?event={m['id']}"
    req = urllib.request.Request(url, headers={"User-Agent": collect.UA})
    r = json.loads(urllib.request.urlopen(req, timeout=25).read())
    lines = [f"Result: {m['home']['name']} {m['home']['score']}-{m['away']['score']} {m['away']['name']} ({m['league']}, {m['date'][:10]})"]
    for t in r.get("boxscore", {}).get("teams", []):
        st = {s["name"]: s["displayValue"] for s in t.get("statistics", [])}
        lines.append(f"{t['team']['displayName']}: " + ", ".join(f"{k}={st[k]}" for k in _STAT_KEYS if k in st))
    for ro in r.get("rosters", []):
        if ro.get("formation"):
            lines.append(f"Formation {ro.get('team', {}).get('displayName', '?')}: {ro['formation']}")
    evs = [k for k in r.get("keyEvents", []) if k.get("type", {}).get("text") in ("Goal", "Yellow Card", "Red Card", "Substitution", "Penalty - Scored", "Own Goal")]
    for k in evs[:25]:
        lines.append(f"{k.get('clock', {}).get('displayValue', '')} {k['type']['text']}: {k.get('text', '')[:140]}")
    return "\n".join(lines)


def analysis_prompt(m, facts, items):
    since = ts(m["date"]) - dt.timedelta(hours=6)
    lines = [facts, "", "Match-report / news snippets:"]
    for side in ("home", "away"):
        lines += team_snippets(items, m[side].get("team_id"), since, 4)
    return "\n".join(lines)


def concept_prompt(items, ai, week):
    since = now_utc() - dt.timedelta(days=7)
    arts = [f"- [{i['source']}] {i['title']} :: {i['summary'][:200]}" for i in items
            if i["category"] == "analysis" and not i["dup_of"] and ts(i["published"]) >= since][:12]
    facts = [a["facts"] for a in ai["analyses"].values() if a.get("week") == week and a.get("facts")][:6]
    if not facts:
        return None
    return "Analysis articles this week:\n" + ("\n".join(arts) or "- none") + "\n\nMatch fact sheets this week:\n\n" + "\n\n".join(facts)


# ---------- עלות ----------
def price(cfg, model, tin, tout):
    p = cfg["ai"]["prices_per_mtok_usd"].get(model)
    return (tin * p["in"] + tout * p["out"]) / 1e6 if p else 0.0


def month_key():
    return now_utc().strftime("%Y-%m")


def record_usage(cfg, usage, job, model, tin, tout):
    u = usage.setdefault("months", {}).setdefault(month_key(), {"cost_usd": 0.0, "calls": 0, "by_job": {}})
    cost = price(cfg, model, tin, tout)
    u["cost_usd"] = round(u["cost_usd"] + cost, 5)
    u["calls"] += 1
    j = u["by_job"].setdefault(job, {"model": model, "calls": 0, "in": 0, "out": 0, "cost_usd": 0.0})
    j["model"] = model
    j["calls"] += 1
    j["in"] += tin
    j["out"] += tout
    j["cost_usd"] = round(j["cost_usd"] + cost, 5)


class Budget(Exception):
    pass


def call_model(client, cfg, usage, job, system, user, max_tokens):
    import anthropic
    if usage.get("months", {}).get(month_key(), {}).get("cost_usd", 0) >= cfg["ai"]["monthly_budget_usd"]:
        raise Budget("הגענו לתקציב החודשי")
    model = cfg["ai"]["models"][job]
    try:
        resp = client.messages.create(
            model=model, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"effort": cfg["ai"]["effort"][job], "format": {"type": "json_schema", "schema": SCHEMAS[job]}},
        )
    except anthropic.AuthenticationError:
        raise
    except anthropic.APIError as e:
        print(f"  שגיאת API ({job}): {type(e).__name__}: {str(e)[:120]}")
        return None
    record_usage(cfg, usage, job, model, resp.usage.input_tokens, resp.usage.output_tokens)
    if resp.stop_reason == "refusal":
        print(f"  המודל סירב ({job}), מדלג")
        return None
    if resp.stop_reason == "max_tokens":
        print(f"  הפלט נחתך ({job}), מדלג")
        return None
    return json.loads(next(b.text for b in resp.content if b.type == "text"))


# ---------- משימות ----------
def pick(cfg, art, mt, ai, only, kind):
    items = art["items"]
    big = cfg["ai"]["big_matches"]
    standings = mt.get("standings", {})
    now = now_utc()
    if kind == "summaries":
        cands = [i for i in items if i["category"] != "video" and not i["dup_of"] and i["id"] not in ai["summaries"] and i["title"]]
        return cands[: cfg["ai"]["summaries"]["max_per_run"]]
    ms = mt.get("matches", [])
    if kind == "preview":
        c = [m for m in ms if m["state"] == "pre" and now <= ts(m["date"]) <= now + dt.timedelta(hours=36)
             and m["id"] not in ai["previews"] and is_big(m, standings, big["top_rank"])]
        return c[: big["max_previews_per_run"]]
    if kind == "analysis":
        c = [m for m in ms if m["state"] == "post" and ts(m["date"]) >= now - dt.timedelta(hours=48)
             and m["id"] not in ai["analyses"] and is_big(m, standings, big["top_rank"])]
        return sorted(c, key=lambda m: m["date"], reverse=True)[: big["max_analyses_per_run"]]
    return []


def run_jobs(cfg, art, mt, ai, usage, args):
    items = art["items"]
    standings = mt.get("standings", {})
    client = None
    if not (args.dry_run or args.mock):
        import anthropic
        client = anthropic.Anthropic()
    week = now_utc().strftime("%G-W%V")
    stats = {}

    def want(job):
        return not args.only or args.only == job

    def fake(job, **kw):
        return {"summaries": {"summaries": [{"id": i, "he": "[דוגמה] תקציר בעברית לבדיקת התצוגה באתר."} for i in kw.get("ids", [])]},
                "preview": {"headline": "[דוגמה] על מה לשים לב", "points": [{"title": "נקודה 1", "text": "טקסט לדוגמה."}, {"title": "נקודה 2", "text": "טקסט לדוגמה."}, {"title": "נקודה 3", "text": "טקסט לדוגמה."}]},
                "analysis": {"headline": "[דוגמה] ניתוח", "summary": "סיכום לדוגמה.", "key_points": ["נקודה א", "נקודה ב"], "caveat": "זהו טקסט לדוגמה."},
                "concept": {"concept": "[דוגמה] לחץ גבוה", "explanation": "הסבר לדוגמה.", "example": "דוגמה לדוגמה.", "how_to_spot": "לחפש...", "data_support": "בדיקה"}}[job]

    def run(job, system, user, max_tokens, **kw):
        if args.dry_run:
            print(f"  [{job}] פרומפט: {len(system) + len(user)} תווים")
            return None
        if args.mock:
            return fake(job, **kw)
        return call_model(client, cfg, usage, job, system, user, max_tokens)

    # 1. תקצירים (באצוות)
    if want("summaries"):
        cands = pick(cfg, art, mt, ai, args.only, "summaries")
        bs = cfg["ai"]["summaries"]["batch_size"]
        done = 0
        for k in range(0, len(cands), bs):
            batch = cands[k:k + bs]
            payload = json.dumps([{"id": i["id"], "lang": i["lang"], "title": i["title"], "snippet": i["summary"][:300]} for i in batch], ensure_ascii=False)
            out = run("summaries", SYS_SUMMARY, payload, 200 * len(batch) + 3000, ids=[i["id"] for i in batch])
            if out:
                valid = {i["id"] for i in batch}
                for s in out["summaries"]:
                    if s["id"] in valid and s["he"].strip():
                        ai["summaries"][s["id"]] = {"he": s["he"].strip()}
                        done += 1
        stats["summaries"] = f"{done}/{len(cands)}"

    # 2. על מה לשים לב
    if want("preview"):
        c = pick(cfg, art, mt, ai, args.only, "preview")
        n = 0
        for m in c:
            out = run("preview", SYS_PREVIEW, preview_prompt(m, standings, items), 4000)
            if out:
                ai["previews"][m["id"]] = {**out, "at": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"), "kickoff": m["date"]}
                n += 1
        stats["preview"] = f"{n}/{len(c)}"

    # 3. ניתוח משחק
    if want("analysis"):
        c = pick(cfg, art, mt, ai, args.only, "analysis")
        n = 0
        for m in c:
            try:
                facts = fetch_facts(m)
            except Exception as e:
                print(f"  לא הצלחתי להביא נתוני משחק {m['id']}: {e}")
                continue
            out = run("analysis", SYS_ANALYSIS, analysis_prompt(m, facts, items), 6000)
            if out:
                ai["analyses"][m["id"]] = {**out, "at": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"), "week": week, "facts": facts, "date": m["date"]}
                n += 1
        stats["analysis"] = f"{n}/{len(c)}"

    # 4. מושג טקטי שבועי (פעם בשבוע, מסוף שבוע)
    if want("concept") and (args.only or now_utc().weekday() >= 5) and week not in ai["concepts"]:
        prompt = concept_prompt(items, ai, week)
        if prompt:
            out = run("concept", SYS_CONCEPT, prompt, 12000)
            if out:
                ai["concepts"][week] = {**out, "at": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")}
                stats["concept"] = "1/1"
    return stats


def prune(ai, art, mt):
    ids = {i["id"] for i in art["items"]}
    ai["summaries"] = {k: v for k, v in ai["summaries"].items() if k in ids}
    keep_from = (now_utc() - dt.timedelta(days=14)).strftime("%Y-%m-%dT00:00:00Z")
    ai["previews"] = {k: v for k, v in ai["previews"].items() if v.get("kickoff", "") >= keep_from}
    ai["analyses"] = {k: v for k, v in ai["analyses"].items() if v.get("date", "") >= keep_from}
    ai["concepts"] = dict(sorted(ai["concepts"].items())[-8:])


# ---------- הערכת עלות ----------
def estimate(cfg, art, mt):
    items = art["items"]
    prim = [i for i in items if i["category"] != "video" and not i["dup_of"]]
    days = {}
    for i in prim:
        days.setdefault(i["published"][:10], 0)
        days[i["published"][:10]] += 1
    today = now_utc().strftime("%Y-%m-%d")
    full = [v for k, v in sorted(days.items()) if k < today][-5:]
    per_day = sum(full) / max(len(full), 1)
    cap_day = cfg["ai"]["summaries"]["max_per_run"] * 4
    tok = lambda s: len(s) / 3.6   # קירוב: ~3.6 תווים לטוקן באנגלית/שפות לטיניות; שגיאה אפשרית של כ-±25%
    sample = prim[:200]
    in_per_art = sum(tok(i["title"] + i["summary"][:300]) + 25 for i in sample) / len(sample)
    sys_per_batch = tok(SYS_SUMMARY) + 150
    bs = cfg["ai"]["summaries"]["batch_size"]

    standings = mt.get("standings", {})
    big = [m for m in mt["matches"] if is_big(m, standings, cfg["ai"]["big_matches"]["top_rank"])]
    span_days = max((ts(max(m["date"] for m in mt["matches"])) - ts(min(m["date"] for m in mt["matches"]))).days, 1)
    big_per_month = len(big) / span_days * 30
    # הנחות פלט (עברית ~2.2 טוקן למילה) + טוקני חשיבה לפי רמת המאמץ
    A = {
        "summaries": dict(n=min(per_day, cap_day) * 30, tin=in_per_art + sys_per_batch / bs, tout=95 + 60),
        "preview": dict(n=big_per_month / 2, tin=tok(SYS_PREVIEW) + 1300, tout=330 + 1200),
        "analysis": dict(n=big_per_month / 2 * 0.8, tin=tok(SYS_ANALYSIS) + 1900, tout=650 + 2500),
        "concept": dict(n=4.3, tin=tok(SYS_CONCEPT) + 3500, tout=1000 + 8000),
    }
    print(f"כתבות ראשיות ביום (ממוצע 5 ימים מלאים): {per_day:.0f} | תקרת תקצירים ביום בהגדרות: {cap_day}")
    print(f"משחקים 'גדולים' בטווח הנתונים: {len(big)} ב-{span_days} ימים -> כ-{big_per_month:.0f} בחודש\n")
    print(f"{'משימה':<10}{'כמות/חודש':>10}{'קלט/קריאה':>11}{'פלט/קריאה':>11}")
    for k, a in A.items():
        print(f"{k:<10}{a['n']:>10.0f}{a['tin']:>11.0f}{a['tout']:>11.0f}")
    tiers = ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"]
    print("\nעלות חודשית משוערת ($), לפי מודל לכל המשימות:")
    for t in tiers:
        parts = {k: price(cfg, t, a["tin"] * a["n"], a["tout"] * a["n"]) for k, a in A.items()}
        print(f"  {t:<18} סה\"כ {sum(parts.values()):6.2f}   " + "  ".join(f"{k}={v:.2f}" for k, v in parts.items()))
    mixes = {"תקצירים Haiku + שאר Sonnet": ("claude-haiku-5-5", "claude-sonnet-5-5", "claude-sonnet-5-5", "claude-sonnet-5-5"),
             "תקצירים Haiku + ניתוחים Opus": ("claude-haiku-5-5", "claude-opus-5-5", "claude-opus-5-5", "claude-opus-5-5")}
    for name, ms in mixes.items():
        tot = sum(price(cfg, m, a["tin"] * a["n"], a["tout"] * a["n"]) for m, a in zip(ms, A.values()))
        print(f"  {name:<34} סה\"כ {tot:6.2f}")
    print("\nטווח בטחון: הכפל ב-2 עד 3 אם הפלט העברי או טוקני החשיבה גדולים מההנחות. המונה האמיתי: data/ai_usage.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--estimate", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--only", choices=JOBS)
    args = ap.parse_args()

    cfg = json.loads(collect.CONFIG_PATH.read_text(encoding="utf-8"))
    art = load_json(DATA / "articles.json", {"items": []})
    mt = load_json(DATA / "matches.json", {"matches": [], "standings": {}})
    if args.estimate:
        estimate(cfg, art, mt)
        return 0
    if not args.dry_run and not args.mock:
        if not cfg["ai"]["enabled"]:
            print("שכבת ה-AI מושבתת (ai.enabled=false). לא עושה כלום.")
            return 0
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("אין ANTHROPIC_API_KEY בסביבה. לא עושה כלום.")
            return 0

    ai = load_json(AI_PATH, {})
    for k in ("summaries", "previews", "analyses", "concepts"):
        ai.setdefault(k, {})
    usage = load_json(USAGE_PATH, {})
    try:
        stats = run_jobs(cfg, art, mt, ai, usage, args)
    except Budget as e:
        print("עצירה:", e)
        stats = {"budget": "stopped"}
    except Exception as e:
        # מפתח שגוי וכו': לא מפילים את שאר ה-Action, אבל כן מדווחים
        print(f"שגיאה: {type(e).__name__}: {e}")
        return 1
    prune(ai, art, mt)
    print("תוצאות:", stats)
    m = usage.get("months", {}).get(month_key())
    if m:
        print(f"עלות החודש עד כה: ${m['cost_usd']:.3f} ({m['calls']} קריאות), תקציב ${cfg['ai']['monthly_budget_usd']}")
    if args.dry_run:
        return 0
    ai["generated_at"] = now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")
    save_json(AI_PATH, ai)
    if not args.mock:
        save_json(USAGE_PATH, usage, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
