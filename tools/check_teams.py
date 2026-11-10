#!/usr/bin/env python3
"""משווה את רשימות הקבוצות ב-config/config.json לטבלאות העדכניות (FotMob, מתוך data/matches.json).

מדפיס (1) קבוצות שיש בטבלה ואין להן הגדרה, ו-(2) קבוצות בהגדרות שכבר לא בליגה.
כדאי להריץ בתחילת כל עונה:   python3 tools/check_teams.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import collect  # noqa: E402

def main():
    # הטבלאות העדכניות מגיעות מ-data/matches.json (FotMob); מריצים קודם scripts/collect_matches.py
    cfg = json.loads(collect.CONFIG_PATH.read_text(encoding="utf-8"))
    matcher = collect.Matcher(cfg)
    standings = json.loads((collect.DATA_DIR / "matches.json").read_text(encoding="utf-8")).get("standings", {})
    for lid, tables in standings.items():
        if not cfg["leagues"].get(lid, {}).get("teams"):
            continue
        names = [r["team"] for t in tables for r in t["rows"]]
        found, missing = set(), []
        for n in names:
            teams = [t for t in matcher.analyze(n)[0] if matcher.team_league[t] == lid]
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
