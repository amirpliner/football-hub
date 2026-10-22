#!/usr/bin/env python3
"""אוסף משחקים (תוצאות ולוח) וטבלאות ושומר ל-data/matches.json.

המקור: ה-API הציבורי של ESPN (בלי מפתח). הוא לא רשמי/מתועד, ולכן כל כשל נתפס
והנתונים הקודמים נשמרים. ה-API לא מקבל טווח תאריכים, אז שולחים בקשה לכל יום בנפרד.

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

ESPN_CODES = {
    "premier_league": "eng.1", "la_liga": "esp.1", "serie_a": "ita.1", "bundesliga": "ger.1",
    "ligue_1": "fra.1", "championship": "eng.2", "liga_portugal": "por.1", "eredivisie": "ned.1",
    "champions_league": "uefa.champions",
}
DAYS_BACK = 3
DAYS_AHEAD = 7
OUT_PATH = collect.DATA_DIR / "matches.json"
SCORE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={date}"
TABLE_URL = "https://site.api.espn.com/apis/v2/sports/soccer/{code}/standings"


def get_json(url):
    last = None
    for _ in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": collect.UA, "Accept-Encoding": "identity"})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read())
        except Exception as e:
            last = e
            time.sleep(1.5)
    raise last


def iso(s):
    """'2026-10-23T19:00Z' -> '2026-10-23T19:00:00Z'"""
    return s if s.count(":") == 2 else s.replace("Z", ":00Z")


def parse_event(e, league, matcher):
    comp = e["competitions"][0]
    st = comp["status"]["type"]
    sides = {}
    for c in comp["competitors"]:
        t = c["team"]
        name = t.get("displayName") or t.get("name") or "?"
        teams, _ = matcher.analyze(name)
        sides[c["homeAway"]] = {
            "name": name,
            "short": t.get("shortDisplayName") or name,
            "logo": t.get("logo"),
            "score": int(c["score"]) if str(c.get("score", "")).isdigit() else None,
            "team_id": next((x for x in teams if matcher.team_league[x] == league), teams[0] if teams else None),
        }
    if "home" not in sides or "away" not in sides:
        return None
    link = next((l["href"] for l in e.get("links", []) if "summary" in l.get("rel", [])), None)
    return {
        "id": e["id"],
        "league": league,
        "date": iso(e["date"]),
        "state": st["state"],                  # pre / in / post
        "detail": st.get("shortDetail", ""),   # FT, 67', Postponed ...
        "home": sides["home"],
        "away": sides["away"],
        "link": link,
    }


def stat(entry, name, default=0):
    for s in entry.get("stats", []):
        if s.get("name") == name:
            v = s.get("value")
            return int(v) if isinstance(v, (int, float)) else default
    return default


def parse_tables(data, league, matcher):
    tables = []
    for child in data.get("children", []):
        rows = []
        for en in child.get("standings", {}).get("entries", []):
            t = en["team"]
            name = t.get("displayName", "?")
            teams, _ = matcher.analyze(name)
            rows.append({
                "rank": stat(en, "rank"),
                "team": name,
                "logo": (t.get("logos") or [{}])[0].get("href"),
                "team_id": next((x for x in teams if matcher.team_league[x] == league), teams[0] if teams else None),
                "gp": stat(en, "gamesPlayed"), "w": stat(en, "wins"), "d": stat(en, "ties"), "l": stat(en, "losses"),
                "gf": stat(en, "pointsFor"), "ga": stat(en, "pointsAgainst"),
                "gd": stat(en, "pointDifferential"), "pts": stat(en, "points"),
            })
        rows.sort(key=lambda r: (r["rank"] or 999, -r["pts"]))
        if rows:
            tables.append({"name": child.get("name", ""), "rows": rows})
    return tables


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = json.loads(collect.CONFIG_PATH.read_text(encoding="utf-8"))
    matcher = collect.Matcher(cfg)
    today = dt.datetime.now(dt.timezone.utc).date()
    dates = [today + dt.timedelta(days=i) for i in range(-DAYS_BACK, DAYS_AHEAD + 1)]
    start_iso = dates[0].strftime("%Y-%m-%dT00:00:00Z")

    old = {}
    if OUT_PATH.exists():
        try:
            old = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        except Exception:
            old = {}
    matches = {m["id"]: m for m in old.get("matches", []) if m["date"] >= start_iso}
    standings = dict(old.get("standings", {}))

    jobs = [(lid, d) for lid in ESPN_CODES for d in dates]

    def fetch_day(job):
        lid, d = job
        try:
            data = get_json(SCORE_URL.format(code=ESPN_CODES[lid], date=d.strftime("%Y%m%d")))
            return job, [m for m in (parse_event(e, lid, matcher) for e in data.get("events", [])) if m], None
        except Exception as e:
            return job, [], f"{type(e).__name__}: {e}"[:100]

    def fetch_table(lid):
        try:
            return lid, parse_tables(get_json(TABLE_URL.format(code=ESPN_CODES[lid])), lid, matcher), None
        except Exception as e:
            return lid, None, f"{type(e).__name__}: {e}"[:100]

    day_errors = []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        day_results = list(ex.map(fetch_day, jobs))
        table_results = list(ex.map(fetch_table, ESPN_CODES))

    fresh = 0
    for (lid, d), found, err in day_results:
        if err:
            day_errors.append(f"{lid} {d}: {err}")
            continue
        day_key = d.strftime("%Y-%m-%d")
        # משחקים של אותו יום שנעלמו מהתשובה (נדחו/בוטלו) לא נשארים בנתונים הישנים
        for mid in [k for k, m in matches.items() if m["league"] == lid and m["date"][:10] == day_key]:
            del matches[mid]
        for m in found:
            matches[m["id"]] = m
            fresh += 1

    table_errors = []
    for lid, tables, err in table_results:
        if err:
            table_errors.append(f"{lid}: {err}")
        elif tables:
            standings[lid] = tables

    ordered = sorted(matches.values(), key=lambda m: (m["date"], m["id"]))
    print(f"משחקים: {len(ordered)} (מהריצה: {fresh}) | טבלאות: {len(standings)}/{len(ESPN_CODES)}")
    for e in day_errors[:10] + table_errors:
        print("  כשל:", e)
    if len(day_errors) == len(jobs) and len(table_errors) == len(ESPN_CODES):
        print("כל הבקשות נכשלו, לא דורס את הקובץ הקיים")
        return 1
    if args.dry_run:
        return 0

    out = {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "ESPN",
        "matches": ordered,
        "standings": standings,
    }
    collect.DATA_DIR.mkdir(exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
