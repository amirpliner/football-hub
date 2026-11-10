# מגרש: טקטיקה וניתוח

אפליקציה אישית ללימוד טקטיקה, נקייה מחדשות: ליגת העל, הליגה הלאומית ו-5 הליגות הבכירות. לכל משחק ניתוח טקטי (מערכים על מגרש, תפקידים, חילופים, "מה לומדים"), מושג טקטי שבועי, מאמרי טקטיקה, ומשחקים וטבלאות. מקורות החדשות, הבלוגים והווידאו כבויים ב-`config/config.json` (`"enabled": false`), ואפשר להחזיר אותם משם.

## מבנה
- `config/config.json` – **קובץ ההגדרות היחיד**: ליגות, קבוצות (לזיהוי אוטומטי), מקורות RSS, כמה ימים לשמור.
- `scripts/collect.py` – אוסף את הכתבות ושומר ל-`data/articles.json` (ו-`data/status.json` עם מצב כל מקור).
- `.github/workflows/collect.yml` – מריץ את הסקריפט 4 פעמים ביום, וגם ידנית.
- `scripts/collect_matches.py` – משחקים וטבלאות מ-FotMob (API לא רשמי) ל-`data/matches.json`, והרכבים, מערכים וחילופים של משחקים שהסתיימו ל-`data/lineups.json` (בחינם, בלי Claude). מזהה כל ליגה ב-FotMob: `leagues.<id>.fotmob_id`.
- `scripts/ai_layer.py` – שכבת Claude (**כבויה כרגע, כדי שלא תהיה עלות**) (ניתוח משחק, על מה לשים לב, מושג שבועי, תקצירי מאמרים, זוויות לציוץ). `--estimate` מחשב עלות חודשית מהנתונים האמיתיים.
- `tools/check_teams.py` – בדיקת רשימות הקבוצות מול הטבלאות.
- `tools/check_feeds.py` – בודק אם כתובת RSS חדשה באמת עובדת, לפני שמוסיפים אותה.

## הרצה מקומית
```
python3 scripts/collect.py            # הרצה רגילה
python3 scripts/collect.py --dry-run  # בלי לשמור
python3 scripts/collect.py --only bbc-pl
```

## להוסיף / להסיר מקור
ב-`config/config.json` תחת `sources`: מוסיפים שורה (מעתיקים אחת קיימת ומשנים), או מוסיפים `"enabled": false` כדי לכבות.
- `leagues` – כל הכתבות בפיד שייכות לליגה הזו.
- `match_leagues` – פיד רחב: נשמרות רק כתבות שמזכירות קבוצה מהליגות האלה.
- `keep_unmatched` – שומרים הכול (כללי / ניתוח).

## להוסיף / להסיר ליגה או קבוצה
ב-`leagues` ב-`config/config.json`. בתחילת כל עונה (עליות וירידות) מריצים `python3 scripts/collect_matches.py` ואז `python3 tools/check_teams.py`: הוא משווה את הרשימות לטבלאות העדכניות ומראה מה חסר או מיותר.

## זוויות לציוץ (כבויות)
כפתור "זווית לציוץ" מופיע ליד ניתוחי משחק, מושגים ומאמרים. הטיוטות נוצרות מראש ב-Action (בגלל שמפתח ה-API לא יכול לשבת בדפדפן), ולכן אין יצירה "לפי דרישה". `ai.tweets.max_per_run` שולט בכמה כתבות בכל הרצה (0 = כבוי), ו-`ai.tweets.language` בשפת הציוץ (`he` / `en`).

## התקנה על הטלפון
פותחים את האתר ב-Safari או Chrome ← שיתוף ← "הוסף למסך הבית".

## הפעלת שכבת Claude (רק אחרי שאישרת עלות)
1. ב-GitHub: Settings ← Secrets and variables ← Actions ← New repository secret, שם `ANTHROPIC_API_KEY`.
2. ב-`config/config.json` תחת `ai`: בוחרים מודלים ב-`models`, מגדירים `monthly_budget_usd`, ומשנים `enabled` ל-`true`.
3. העלות האמיתית נרשמת ב-`data/ai_usage.json`. כשמגיעים לתקציב החודשי הסקריפט עוצר לבד.
