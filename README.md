# אתר כדורגל אישי

## מבנה
- `config/config.json` – **קובץ ההגדרות היחיד**: ליגות, קבוצות (לזיהוי אוטומטי), מקורות RSS, כמה ימים לשמור.
- `scripts/collect.py` – אוסף את הכתבות ושומר ל-`data/articles.json` (ו-`data/status.json` עם מצב כל מקור).
- `.github/workflows/collect.yml` – מריץ את הסקריפט 4 פעמים ביום, וגם ידנית.
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
ב-`leagues` ב-`config/config.json`. רשימות הקבוצות מבוססות על עונת 2025-26 – **צריך לעדכן עלייה/ירידה** בתחילת כל עונה.
