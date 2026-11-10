#!/usr/bin/env python3
"""אוסף משחקים (תוצאות ולוח) וטבלאות ושומר ל-data/matches.json.

המקור: ה-API הציבורי של FotMob (בלי מפתח), שמכסה גם את ליגת העל והליגה הלאומית.
הוא לא רשמי/מתועד, ולכן כל כשל נתפס והנתונים הקודמים נשמרים.
מזהה הליגה ב-FotMob מוגדר בקובץ ההגדרות (leagues.<id>.fotmob_id).

שימוש:
    python3 scripts/collect_matches.py
    python3 scripts/collect_matches.py --dry-run
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import collect  # noqa: E402  (משתמשים באותו Matcher ו-UA)

DAYS_BACK = 4
DAYS_AHEAD = 10
OUT_PATH = collect.DATA_DIR / "matches.json"
LEAGUE_URL = "https://www.fotmob.com/api/data/leagues?id={id}"
LOGO_URL = "https://images.fotmob.com/image_resources/logo/teamlogo/{id}_small.png"
MATCH_URL = "https://www.fotmob.com/api/data/matchDetails?matchId={id}"
LINEUPS_PATH = collect.DATA_DIR / "lineups.json"


def get_json(url):
    last = None
    for _ in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": collect.UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            last = e
            time.sleep(2)
    raise last


def _lines(players):
    """הרכב כשורות מאחור לקדימה; בכל שורה משמאל לימין (לפי מיקום FotMob)."""
    rows = {}
    for p in players:
        lay = p.get("horizontalLayout") or {}
        rows.setdefault(round(lay.get("x", 0), 1), []).append((lay.get("y", 0), p))
    out = []
    for x in sorted(rows):
        names = [f"{p['name']} ({p.get('shirtNumber', '')})" for _, p in sorted(rows[x], key=lambda t: t[0])]
        out.append(", ".join(names))
    return out


def fetch_match(m):
    """מחזיר (גיליון עובדות טקסטואלי, הרכבים לציור, אירועים) למשחק, מתוך FotMob."""
    md = get_json(MATCH_URL.format(id=m["id"]))
    c = md.get("content", {})
    lines = [f"Result: {m['home']['name']} {m['home']['score']}-{m['away']['score']} {m['away']['name']} ({m['league']}, {m['date'][:10]})"]
    lineups = {}
    lu = c.get("lineup") or {}
    for side, key in (("home", "homeTeam"), ("away", "awayTeam")):
        t = lu.get(key) or {}
        starters = t.get("starters") or []
        coach = (t.get("coach") or {}).get("name") if isinstance(t.get("coach"), dict) else None
        if not starters:
            continue
        lines.append(f"{t.get('name', m[side]['name'])} ({side}) formation {t.get('formation', '?')}, coach {coach or '?'}:")
        lines += [f"  line {i + 1}: {row}" for i, row in enumerate(_lines(starters))]
        lineups[side] = {
            "formation": t.get("formation"), "coach": coach,
            "players": [{"n": p.get("shirtNumber"), "name": p.get("lastName") or p["name"],
                         "x": round((p.get("horizontalLayout") or {}).get("x", 0), 3), "y": round((p.get("horizontalLayout") or {}).get("y", 0), 3)}
                        for p in starters],
        }
    events = []
    ev = ((c.get("matchFacts") or {}).get("events") or {}).get("events") or []
    for e in ev:
        who = "home" if e.get("isHome") else "away"
        if e.get("type") == "Substitution" and e.get("swap"):
            names = [x.get("name") for x in e["swap"]]
            inn, out = names[0], names[1] if len(names) > 1 else "?"
            lines.append(f"{e.get('time')}' sub ({who}): {inn} on for {out}")
            events.append({"t": e.get("time"), "type": "sub", "side": who, "in": inn, "out": out})
        elif e.get("type") == "Goal":
            lines.append(f"{e.get('time')}' goal ({who}): {e.get('nameStr')}{' (pen)' if e.get('isPenalty') else ''}{' (own goal)' if e.get('ownGoal') else ''}")
            events.append({"t": e.get("time"), "type": "goal", "side": who, "name": e.get("nameStr"), "pen": bool(e.get("isPenalty")), "og": bool(e.get("ownGoal"))})
        elif e.get("type") == "Card" and e.get("card") in ("Red", "YellowRed"):
            lines.append(f"{e.get('time')}' red card ({who}): {e.get('nameStr')}")
            events.append({"t": e.get("time"), "type": "red", "side": who, "name": e.get("nameStr")})
    mo = c.get("momentum")
    if isinstance(mo, dict):
        data = (mo.get("main") or {}).get("data") or []
        blocks = []
        for start in range(0, 90, 15):
            vals = [d["value"] for d in data if start <= d.get("minute", 0) < start + 15]
            if vals:
                avg = sum(vals) / len(vals)
                blocks.append(f"{start}-{start + 15}': " + ("home on top" if avg > 12 else "away on top" if avg < -12 else "balanced"))
        if blocks:
            lines.append("Momentum by period: " + "; ".join(blocks))
    return "\n".join(lines), lineups, events


def team_id(matcher, league, name):
    teams, _ = matcher.analyze(name)
    return next((t for t in teams if matcher.team_league[t] == league), teams[0] if teams else None)


def parse_fixture(f, league, matcher):
    st = f.get("status", {})
    if st.get("cancelled"):
        return None
    state = "post" if st.get("finished") else "in" if st.get("started") else "pre"
    score = (st.get("scoreStr") or "").replace(" ", "").split("-")
    sides = {}
    for i, key in enumerate(("home", "away")):
        t = f[key]
        sides[key] = {
            "name": t["name"],
            "short": t.get("shortName") or t["name"],
            "logo": LOGO_URL.format(id=t["id"]),
            "fotmob_id": str(t["id"]),
            "score": int(score[i]) if len(score) == 2 and score[i].isdigit() else None,
            "team_id": team_id(matcher, league, t["name"]),
        }
    reason = (st.get("reason") or {}).get("short", "")
    return {
        "id": str(f["id"]),
        "league": league,
        "date": st.get("utcTime", "").replace(".000Z", "Z"),
        "state": state,
        "detail": "FT" if state == "post" else (st.get("liveTime") or {}).get("short", reason) if state == "in" else "",
        "home": sides["home"],
        "away": sides["away"],
        "link": "https://www.fotmob.com" + f["pageUrl"] if f.get("pageUrl") else None,
    }


def parse_table(data, league, matcher):
    tables = []
    for block in data.get("table", []):
        d = block.get("data", {})
        groups = d.get("tables") or [d]
        for g in groups:
            rows = []
            for r in g.get("table", {}).get("all", []):
                gf, _, ga = (r.get("scoresStr") or "0-0").partition("-")
                rows.append({
                    "rank": r.get("idx"),
                    "team": r["name"],
                    "logo": LOGO_URL.format(id=r["id"]),
                    "team_id": team_id(matcher, league, r["name"]),
                    "gp": r.get("played", 0), "w": r.get("wins", 0), "d": r.get("draws", 0), "l": r.get("losses", 0),
                    "gf": int(gf or 0), "ga": int(ga or 0), "gd": r.get("goalConDiff", 0), "pts": r.get("pts", 0),
                })
            if rows:
                tables.append({"name": g.get("leagueName", ""), "rows": rows})
    return tables


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = json.loads(collect.CONFIG_PATH.read_text(encoding="utf-8"))
    matcher = collect.Matcher(cfg)
    leagues = {lid: l["fotmob_id"] for lid, l in cfg["leagues"].items() if l.get("fotmob_id")}
    now = dt.datetime.now(dt.timezone.utc)
    start = (now - dt.timedelta(days=DAYS_BACK)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = (now + dt.timedelta(days=DAYS_AHEAD)).strftime("%Y-%m-%dT%H:%M:%SZ")

    old = {}
    if OUT_PATH.exists():
        try:
            old = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        except Exception:
            old = {}
    # נתונים ישנים נשמרים רק לליגות שעדיין מוגדרות, וכגיבוי לליגה שהבקשה שלה נכשלה
    matches = {m["id"]: m for m in old.get("matches", []) if m["league"] in leagues and m["date"] >= start}
    standings = {k: v for k, v in old.get("standings", {}).items() if k in leagues}

    def fetch(lid):
        try:
            return lid, get_json(LEAGUE_URL.format(id=leagues[lid])), None
        except Exception as e:
            return lid, None, f"{type(e).__name__}: {e}"[:100]

    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(fetch, leagues))

    errors = []
    for lid, data, err in results:
        if err:
            errors.append(f"{lid}: {err}")
            continue
        fixtures = (data.get("fixtures") or {}).get("allMatches", [])
        for mid in [k for k, m in matches.items() if m["league"] == lid]:
            del matches[mid]
        for f in fixtures:
            t = (f.get("status") or {}).get("utcTime", "")
            if start <= t <= end:
                m = parse_fixture(f, lid, matcher)
                if m:
                    matches[m["id"]] = m
        tables = parse_table(data, lid, matcher)
        if tables:
            standings[lid] = tables

    ordered = sorted(matches.values(), key=lambda m: (m["date"], m["id"]))

    # הרכבים, מערכים ואירועים למשחקים שהסתיימו: רק כאלה שעוד לא נשמרו
    lineups = {}
    if LINEUPS_PATH.exists():
        try:
            lineups = json.loads(LINEUPS_PATH.read_text(encoding="utf-8"))
        except Exception:
            lineups = {}
    lineups = {k: v for k, v in lineups.items() if k in matches}
    todo = [m for m in ordered if m["state"] == "post" and m["id"] not in lineups]

    def details(m):
        try:
            _, lu, ev = fetch_match(m)
            return m["id"], {"lineups": lu, "events": ev} if lu else None
        except Exception:
            return m["id"], None

    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        for mid, entry in ex.map(details, todo):
            if entry:
                lineups[mid] = entry
    print(f"הרכבים: {len(lineups)} משחקים ({len([1 for m in todo if m['id'] in lineups])} חדשים)")
    print(f"משחקים: {len(ordered)} | טבלאות: {len(standings)}/{len(leagues)}")
    for e in errors:
        print("  כשל:", e)
    if len(errors) == len(leagues):
        print("כל הבקשות נכשלו, לא דורס את הקובץ הקיים")
        return 1
    if args.dry_run:
        return 0
    out = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "FotMob",
        "matches": ordered,
        "standings": standings,
    }
    collect.DATA_DIR.mkdir(exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    LINEUPS_PATH.write_text(json.dumps(lineups, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
