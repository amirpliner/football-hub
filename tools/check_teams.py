#!/usr/bin/env python3
"""משווה את רשימות הקבוצות ב-config/config.json לטבלאות העדכניות של ESPN.

מדפיס (1) קבוצות שיש בטבלה ואין להן הגדרה, ו-(2) קבוצות בהגדרות שכבר לא בליגה.
כדאי להריץ בתחילת כל עונה:   python3 tools/check_teams.py
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import collect  # noqa: E402

ESPN_CODES = {
    "premier_league": "eng.1", "la_liga": "esp.1", "serie_a": "ita.1", "bundesliga": "ger.1",
    "ligue_1": "fra.1", "championship": "eng.2", "liga_portugal": "por.1", "eredivisie": "ned.1",
}


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": collect.UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())


def main():
    cfg = json.loads(collect.CONFIG_PATH.read_text(encoding="utf-8"))
    matcher = collect.Matcher(cfg)
    for lid, code in ESPN_CODES.items():
        d = get_json(f"https://site.api.espn.com/apis/v2/sports/soccer/{code}/standings")
        names = [e["team"]["displayName"] for c in d["children"] for e in c["standings"]["entries"]]
        found = set()
        missing = []
        for n in names:
            teams, _ = matcher.analyze(n)
            teams = [t for t in teams if matcher.team_league[t] == lid]
            if teams:
                found.update(teams)
            else:
                missing.append(n)
        extra = [t for t in cfg["leagues"][lid]["teams"] if t not in found]
        print(f"\n== {lid} ({len(names)} קבוצות בטבלה) ==")
        print("  חסרות בהגדרות:", missing or "—")
        print("  בהגדרות אבל לא בטבלה:", extra or "—")


if __name__ == "__main__":
    main()
