"use strict";

const TZ = "Asia/Jerusalem";
const PAGE = 30;
const AI_NOTE = "נכתב על ידי Claude מתוך נתוני המשחק וסיכומי כתבות, בלי לראות את המשחק. עלול לטעות.";

const $ = (id) => document.getElementById(id);

// ---------- אייקונים (SVG מצויר, משקל קו אחד) ----------
const ICON_PATHS = {
  check: "M5 12.5l4.5 4.5L19 7.5",
  pen: "M4 20l1-4L16.5 4.5a2.1 2.1 0 013 3L8 19z",
  refresh: "M20 12a8 8 0 11-2.6-5.9M20 4v5h-5",
  moon: "M20 14.5A8 8 0 019.5 4a8 8 0 1010.5 10.5z",
  spark: "M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z",
  ext: "M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 01-1 1H5a1 1 0 01-1-1V7a1 1 0 011-1h5",
  copy: "M9 9h10v11H9zM5 15V4h10",
  list: "M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01",
};
const SVG_NS = "http://www.w3.org/2000/svg";
function icon(name) {
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("class", "ico");
  svg.setAttribute("aria-hidden", "true");
  const path = document.createElementNS(SVG_NS, "path");
  path.setAttribute("d", ICON_PATHS[name]);
  svg.append(path);
  return svg;
}
function hydrateIcons() {
  for (const n of document.querySelectorAll("[data-icon]")) n.replaceWith(icon(n.dataset.icon));
}

// צבע לכל ליגה: נקודות ומדבקות
const LEAGUE_COLORS = {
  premier_league: "#a259ff", la_liga: "#ffb01f", serie_a: "#19a35b", bundesliga: "#e63a2e",
  ligue_1: "#25c9e8", championship: "#ff5fa2", liga_portugal: "#0fbf9a", eredivisie: "#ff6f3c", champions_league: "#8fa6ff",
};

// ---------- אחסון מקומי (localStorage) ----------
const store = {
  get(key, fallback) {
    try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; }
    catch (e) { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* פרטי/חסום – ממשיכים בלי שמירה */ }
  },
};

const state = {
  items: [],
  matches: [],
  standings: {},
  ai: { summaries: {}, previews: {}, analyses: {}, concepts: {}, tweets: {} },
  leagues: {},
  league: "",
  view: "analysis",
  shown: PAGE,
};

// ---------- זמן (שעון ישראל) ----------
const fmtTime = new Intl.DateTimeFormat("he-IL", { timeZone: TZ, hour: "2-digit", minute: "2-digit" });
const fmtDay = new Intl.DateTimeFormat("he-IL", { timeZone: TZ, weekday: "long", day: "numeric", month: "long" });
const fmtDayKey = new Intl.DateTimeFormat("en-CA", { timeZone: TZ }); // YYYY-MM-DD

function dayLabel(date) {
  const key = fmtDayKey.format(date);
  const now = new Date();
  if (key === fmtDayKey.format(now)) return "היום";
  if (key === fmtDayKey.format(new Date(now.getTime() - 86400000))) return "אתמול";
  if (key === fmtDayKey.format(new Date(now.getTime() + 86400000))) return "מחר";
  return fmtDay.format(date);
}

// ---------- עזרי ציור ----------
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}
function iconBtn(name, label, cls) {
  const b = el("button", cls || "");
  b.type = "button";
  b.append(icon(name), label);
  return b;
}
function leagueTag(lid) {
  const tag = el("span", "tag");
  const dot = el("i", "dot");
  dot.style.setProperty("--c", LEAGUE_COLORS[lid] || "var(--muted)");
  tag.append(dot, state.leagues[lid] ? state.leagues[lid].name_he : lid);
  return tag;
}
function logoImg(src) {
  const img = el("img");
  img.src = src; img.alt = ""; img.loading = "lazy"; img.referrerPolicy = "no-referrer";
  img.addEventListener("error", () => img.remove());
  return img;
}

// ---------- טעינה ----------
async function load() {
  try {
    const [cfgRes, dataRes, matchRes, aiRes] = await Promise.all([
      fetch("config/config.json", { cache: "no-cache" }),
      fetch("data/articles.json", { cache: "no-cache" }),
      fetch("data/matches.json", { cache: "no-cache" }).catch(() => null),
      fetch("data/ai.json", { cache: "no-cache" }).catch(() => null),
    ]);
    if (!cfgRes.ok || !dataRes.ok) throw new Error(`HTTP ${cfgRes.status}/${dataRes.status}`);
    const cfg = await cfgRes.json();
    const data = await dataRes.json();
    state.leagues = cfg.leagues;
    state.items = data.items.filter((i) => !i.dup_of).map((it) => ({ ...it, date: new Date(it.published) }));
    state.generatedAt = new Date(data.generated_at);
    if (matchRes && matchRes.ok) {
      const md = await matchRes.json();
      state.matches = md.matches || [];
      state.standings = md.standings || {};
      state.matchesAt = new Date(md.generated_at);
    }
    if (aiRes && aiRes.ok) state.ai = { ...state.ai, ...(await aiRes.json()) };
    restoreView();
    buildChips();
    syncControls();
    render();
  } catch (e) {
    $("status").textContent = "לא הצלחתי לטעון את הנתונים (" + e.message + "). אם פתחת את הקובץ ישירות מהמחשב, צריך להריץ שרת מקומי או לפתוח דרך GitHub Pages.";
  }
}

function restoreView() {
  if (state.restored) return;
  state.restored = true;
  const f = store.get("fh_view", null);
  if (!f) return;
  if (["analysis", "concepts", "reads", "matches", "tables"].includes(f.view)) state.view = f.view;
  if (f.league && state.leagues[f.league]) state.league = f.league;
}
function saveView() { store.set("fh_view", { view: state.view, league: state.league }); }

function buildChips() {
  const chips = $("league-chips");
  chips.textContent = "";
  const add = (id, label) => {
    const b = el("button", "chip" + (state.league === id ? " on" : ""));
    b.dataset.league = id;
    if (id) {
      const dot = el("i", "dot");
      dot.style.setProperty("--c", LEAGUE_COLORS[id] || "var(--muted)");
      b.append(dot);
    }
    b.append(label);
    chips.append(b);
  };
  add("", "כל הליגות");
  for (const [lid, league] of Object.entries(state.leagues)) if (!league.no_match_data) add(lid, league.name_he);
}
function syncControls() {
  for (const c of $("league-chips").children) c.classList.toggle("on", c.dataset.league === state.league);
  for (const b of $("views").children) b.classList.toggle("on", b.dataset.view === state.view);
}

// ---------- זוויות לציוץ ----------
function copyText(text, btn) {
  const done = () => {
    const old = [...btn.childNodes];
    btn.replaceChildren(icon("check"), "הועתק");
    setTimeout(() => btn.replaceChildren(...old), 1500);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, () => {});
}

function tweetPanel(entry) {
  const box = el("div", "tweets");
  for (const a of entry.angles) {
    const d = el("div", "angle");
    const ta = el("textarea", "tw-text");
    ta.value = a.tweet;
    ta.rows = 3;
    ta.dir = "auto";
    ta.setAttribute("aria-label", "טיוטת ציוץ (אפשר לערוך)");
    const count = el("span", "tw-count");
    const upd = () => { const n = ta.value.length; count.textContent = n + "/280"; count.classList.toggle("over", n > 280); };
    ta.addEventListener("input", upd);
    upd();
    d.append(ta);
    const row = el("div", "tw-row");
    const copy = iconBtn("copy", "העתק");
    copy.addEventListener("click", () => copyText(ta.value, copy));
    const open = el("a", "tw-open");
    open.append("פתח ב-X ", icon("ext"));
    open.target = "_blank";
    open.rel = "noopener noreferrer";
    open.href = "#";
    open.addEventListener("click", () => { open.href = "https://x.com/intent/post?text=" + encodeURIComponent(ta.value); });
    row.append(copy, open, count);
    d.append(row, el("p", "tw-why", "למה זו זווית פחות מדוברת: " + a.why), el("p", "tw-verify", "לבדוק לפני פרסום: " + a.verify));
    box.append(d);
  }
  box.append(el("p", "ai-note", "טיוטות של Claude לפי הנתונים שנאספו. אתה אחראי לבדוק עובדות לפני שמפרסמים."));
  return box;
}

// מוסיף כפתור "זווית לציוץ" ל-parent; הפאנל נפתח בתוך container
function addTweetButton(key, parent, container) {
  const entry = state.ai.tweets[key];
  if (!entry || !entry.angles || !entry.angles.length) return;
  const btn = iconBtn("pen", "זווית לציוץ", "tw-btn");
  btn.addEventListener("click", () => {
    const open = container.querySelector(":scope > .tweets");
    if (open) { open.remove(); return; }
    container.append(tweetPanel(entry));
  });
  parent.append(btn);
}

// ---------- ניתוחים ----------
function analysisCard(id, an) {
  const card = el("article", "an");
  const m = an.match || {};
  const top = el("div", "meta");
  if (m.league) top.append(leagueTag(m.league));
  card.append(top);
  if (m.home) {
    const score = el("div", "score");
    const res = el("span", "res num");      // ספרות נפרדות, כדי שכל תוצאה תישאר בצד של הקבוצה שלה ב-RTL
    res.append(el("b", null, m.hs), el("i", null, ":"), el("b", null, m.as));
    score.append(el("span", "side", m.home), res, el("span", "side end", m.away));
    card.append(score);
  }
  card.append(el("h2", null, an.headline), el("p", "an-sum", an.summary));
  const acts = el("div", "acts");
  const more = iconBtn("list", "קרא הכול");
  more.addEventListener("click", () => {
    card.classList.toggle("open");
    const open = card.querySelector(":scope > .an-more");
    if (open) { open.remove(); return; }
    const box = el("div", "an-more");
    const ul = el("ul");
    for (const k of an.key_points) ul.append(el("li", null, k));
    box.append(ul, el("p", "caveat", "מה הנתונים לא מראים: " + an.caveat));
    card.insertBefore(box, acts);
  });
  acts.append(more);
  addTweetButton("m:" + id, acts, card);
  card.append(acts);
  return card;
}

function previewCard(m, pv) {
  const card = el("article", "pv");
  const head = el("button", "pv-head");
  head.type = "button";
  const when = new Date(m.date);
  const title = el("span", "pv-title");
  title.append(el("strong", null, `${m.home.short} – ${m.away.short}`), el("span", "pv-when", `${dayLabel(when)} ${fmtTime.format(when)}`));
  head.append(title, el("span", "pv-line", pv.headline));
  head.addEventListener("click", () => {
    const open = card.querySelector(".pv-body");
    if (open) { open.remove(); return; }
    const body = el("div", "pv-body");
    for (const pt of pv.points) {
      const d = el("div", "pt");
      d.append(el("strong", null, pt.title), el("p", null, pt.text));
      body.append(d);
    }
    card.append(body);
  });
  card.append(head);
  return card;
}

function renderAnalysis() {
  const list = $("list");
  const lg = state.league;
  // לפני המשחק: רק משחקים שעוד לא שוחקו
  const now = Date.now();
  const upcoming = state.matches
    .filter((m) => state.ai.previews[m.id] && m.state === "pre" && new Date(m.date).getTime() > now && (!lg || m.league === lg))
    .sort((a, b) => a.date.localeCompare(b.date));
  if (upcoming.length) {
    list.append(el("h3", "sec", "על מה לשים לב"));
    for (const m of upcoming.slice(0, 4)) list.append(previewCard(m, state.ai.previews[m.id]));
  }
  const rows = Object.entries(state.ai.analyses)
    .filter(([, a]) => !lg || (a.match && a.match.league === lg))
    .sort(([, a], [, b]) => (b.date || "").localeCompare(a.date || ""));
  if (rows.length) list.append(el("h3", "sec", "ניתוחי משחקים"));
  let lastDay = "";
  for (const [id, an] of rows.slice(0, state.shown)) {
    const d = new Date(an.date);
    const label = dayLabel(d);
    if (label !== lastDay) { list.append(el("div", "day", label)); lastDay = label; }
    list.append(analysisCard(id, an));
  }
  $("more").hidden = rows.length <= state.shown;
  $("status").textContent = rows.length || upcoming.length ? AI_NOTE : "אין עדיין ניתוחים לליגה הזו. הם נכתבים אחרי כל משחק, ומתעדכנים 4 פעמים ביום.";
}

// ---------- מושגים ----------
function renderConcepts() {
  const list = $("list");
  const weeks = Object.keys(state.ai.concepts).sort().reverse();
  $("status").textContent = weeks.length ? "מושג טקטי חדש כל שבוע, עם דוגמה ממשחק אמיתי מאותו שבוע." : "המושג הראשון ייכתב בסוף השבוע.";
  for (const w of weeks) {
    const c = state.ai.concepts[w];
    const box = el("article", "concept");
    box.append(el("h2", null, c.concept), el("p", null, c.explanation));
    box.append(el("h4", null, "דוגמה מהשבוע"), el("p", null, c.example));
    box.append(el("h4", null, "במה לשים לב"), el("p", null, c.how_to_spot));
    box.append(el("p", "caveat", "עד כמה הנתונים תומכים: " + c.data_support));
    box.append(el("p", "ai-note", AI_NOTE));
    const acts = el("div", "acts");
    addTweetButton("c:" + w, acts, box);
    box.append(acts);
    list.append(box);
  }
}

// ---------- מאמרים טקטיים חיצוניים ----------
function readCard(it) {
  const card = el("article", "card");
  const color = LEAGUE_COLORS[(it.leagues || []).find((l) => l !== "champions_league")] || "var(--panel-2)";
  if (it.image) {
    const a = el("a", "stk");
    a.href = it.link; a.target = "_blank"; a.rel = "noopener noreferrer"; a.tabIndex = -1;
    a.setAttribute("aria-hidden", "true");
    a.style.setProperty("--c", color);
    const img = logoImg(it.image);
    img.addEventListener("error", () => { a.classList.add("tile"); a.append(el("span", "plate", it.source)); });
    a.append(img);
    card.append(a);
  } else {
    const t = el("span", "stk tile");
    t.style.setProperty("--c", color);
    t.append(el("span", "plate", it.source));
    card.append(t);
  }
  const h = el("h2");
  const a = el("a", null, it.title);
  a.href = it.link; a.target = "_blank"; a.rel = "noopener noreferrer"; a.lang = it.lang; a.dir = "auto";
  h.append(a);
  card.append(h);
  const meta = el("div", "meta");
  meta.append(el("span", "src", it.source));
  const t = el("time", null, dayLabel(it.date));
  t.dateTime = it.published;
  meta.append(t);
  for (const l of it.leagues.slice(0, 2)) if (state.leagues[l]) meta.append(leagueTag(l));
  card.append(meta);
  const he = state.ai.summaries[it.id];
  if (he && it.lang !== "he") {
    const hp = el("p", "sum-he");
    const tag = el("span", "ai-tag");
    tag.append(icon("spark"), "תקציר Claude");
    hp.append(tag, he.he);
    card.append(hp);
  } else if (it.summary) {
    const p = el("p", "sum", it.summary);
    p.lang = it.lang; p.dir = "auto";
    card.append(p);
  }
  const acts = el("div", "acts");
  addTweetButton("a:" + it.id, acts, card);
  if (acts.children.length) card.append(acts);
  return card;
}

function renderReads() {
  const list = $("list");
  const lg = state.league;
  const items = state.items.filter((i) => !lg || i.leagues.includes(lg));
  $("status").textContent = items.length ? `${items.length} מאמרי ניתוח וטקטיקה מהשבועות האחרונים` : "אין מאמרים לליגה הזו כרגע.";
  let lastDay = "";
  for (const it of items.slice(0, state.shown)) {
    const label = dayLabel(it.date);
    if (label !== lastDay) { list.append(el("div", "day", label)); lastDay = label; }
    list.append(readCard(it));
  }
  $("more").hidden = items.length <= state.shown;
}

// ---------- משחקים וטבלאות ----------
function updatedLabel() {
  return state.matchesAt ? `עודכן ${fmtDay.format(state.matchesAt)} ${fmtTime.format(state.matchesAt)} · נתוני ESPN, לא בזמן אמת` : "";
}

function matchRow(m) {
  const row = document.createElement(m.link ? "a" : "div");
  row.className = "match " + m.state;
  if (m.link) { row.href = m.link; row.target = "_blank"; row.rel = "noopener noreferrer"; }
  const date = new Date(m.date);
  const when = el("span", "when");
  if (m.state === "pre") when.textContent = fmtTime.format(date);
  else if (m.state === "in") { when.textContent = m.detail; when.classList.add("live"); }
  else when.textContent = m.detail === "FT" ? "סיום" : m.detail;
  const side = (t, cls) => {
    const s = el("span", "team " + cls);
    if (t.logo) s.append(logoImg(t.logo));
    s.append(el("span", "nm", t.short));
    return s;
  };
  const sc = (v) => el("span", "sc", v == null ? "" : String(v));
  const hasScore = m.state !== "pre";
  const mid = el("span", "mid");
  mid.append(hasScore ? sc(m.home.score) : el("span", "sc", ""), el("span", "dash", hasScore ? "–" : "נגד"), hasScore ? sc(m.away.score) : el("span", "sc", ""));
  row.append(when, side(m.home, "home"), mid, side(m.away, "away"));
  return row;
}

function aiPanel(m) {
  const pv = state.ai.previews[m.id], an = state.ai.analyses[m.id];
  if (!pv && !an) return null;
  const wrap = el("div", "ai-wrap");
  const btn = iconBtn("spark", an ? "ניתוח המשחק" : "על מה לשים לב", "ai-btn");
  btn.addEventListener("click", () => {
    const open = wrap.querySelector(".ai-panel");
    if (open) { open.remove(); return; }
    const p = el("div", "ai-panel");
    const src = an || pv;
    p.append(el("h4", null, src.headline));
    if (an) {
      p.append(el("p", null, an.summary));
      const ul = el("ul");
      for (const k of an.key_points) ul.append(el("li", null, k));
      p.append(ul, el("p", "caveat", "מה הנתונים לא מראים: " + an.caveat));
    } else {
      for (const pt of pv.points) {
        const d = el("div", "pt");
        d.append(el("strong", null, pt.title), el("p", null, pt.text));
        p.append(d);
      }
    }
    p.append(el("p", "ai-note", AI_NOTE));
    if (an) addTweetButton("m:" + m.id, p, p);
    wrap.append(p);
  });
  wrap.append(btn);
  return wrap;
}

function renderMatches() {
  const list = $("list");
  const lg = state.league;
  const ms = state.matches.filter((m) => !lg || m.league === lg);
  if (!ms.length) { $("status").textContent = state.matches.length ? "אין משחקים בליגה הזו בטווח התאריכים." : "אין נתוני משחקים."; return; }
  $("status").textContent = updatedLabel();
  const live = ms.filter((m) => m.state === "in");
  const upcoming = ms.filter((m) => m.state === "pre").sort((a, b) => a.date.localeCompare(b.date));
  const done = ms.filter((m) => m.state === "post").sort((a, b) => b.date.localeCompare(a.date));
  const section = (title, arr) => {
    if (!arr.length) return;
    list.append(el("h3", "sec", title));
    let lastDay = "", lastLeague = "";
    for (const m of arr) {
      const label = dayLabel(new Date(m.date));
      if (label !== lastDay) { list.append(el("div", "day", label)); lastDay = label; lastLeague = ""; }
      if (!lg && m.league !== lastLeague) { const l = el("div", "lg"); l.append(leagueTag(m.league)); list.append(l); lastLeague = m.league; }
      list.append(matchRow(m));
      const panel = aiPanel(m);
      if (panel) list.append(panel);
    }
  };
  section("משחקים חיים", live);
  section("תוצאות אחרונות", done);
  section("משחקים קרובים", upcoming);
}

function renderTables() {
  const list = $("list");
  const ids = Object.keys(state.leagues).filter((l) => state.standings[l] && (!state.league || l === state.league));
  if (!ids.length) { $("status").textContent = "אין נתוני טבלה."; return; }
  $("status").textContent = updatedLabel();
  for (const lid of ids) {
    for (const t of state.standings[lid]) {
      const wrap = el("section", "tbl-wrap");
      const title = state.leagues[lid].name_he + (state.standings[lid].length > 1 && t.name ? " · " + t.name : "");
      wrap.append(el("h3", "sec", title));
      const table = el("table", "tbl");
      const head = el("tr");
      for (const [h, cls] of [["#", "r"], ["קבוצה", "t"], ["מש׳", ""], ["נצ׳", "x"], ["תק׳", "x"], ["הפ׳", "x"], ["שערים", "x"], ["הפרש", ""], ["נק׳", "p"]]) head.append(el("th", cls, h));
      table.append(head);
      for (const r of t.rows) {
        const tr = el("tr");
        tr.append(el("td", "r", r.rank));
        const td = el("td", "t");
        if (r.logo) td.append(logoImg(r.logo));
        td.append(el("span", null, r.team));
        tr.append(td);
        const ltr = (cls, text) => { const c = el("td", cls, text); c.dir = "ltr"; return c; };  // כדי ש-"+12" לא יתהפך ל-"12+"
        tr.append(el("td", "", r.gp), el("td", "x", r.w), el("td", "x", r.d), el("td", "x", r.l),
          ltr("x", `${r.gf}:${r.ga}`), ltr("", r.gd > 0 ? "+" + r.gd : String(r.gd)), el("td", "p", r.pts));
        table.append(tr);
      }
      wrap.append(table);
      list.append(wrap);
    }
  }
}

// ---------- ניתוב ----------
function render() {
  document.body.dataset.view = state.view;
  $("list").textContent = "";
  $("more").hidden = true;
  ({ analysis: renderAnalysis, concepts: renderConcepts, reads: renderReads, matches: renderMatches, tables: renderTables })[state.view]();
}

function wireEvents() {
  $("league-chips").addEventListener("click", (e) => {
    const b = e.target.closest(".chip");
    if (!b) return;
    state.league = b.dataset.league;
    state.shown = PAGE;
    syncControls(); saveView(); render();
  });
  $("views").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-view]");
    if (!b) return;
    state.view = b.dataset.view;
    state.shown = PAGE;
    syncControls(); saveView(); render();
    window.scrollTo(0, 0);
  });
  $("more").addEventListener("click", () => { state.shown += PAGE; render(); });
  $("btn-refresh").addEventListener("click", async () => {
    const b = $("btn-refresh");
    b.disabled = true;
    await load();
    b.disabled = false;
  });
  $("btn-theme").addEventListener("click", () => {
    const cur = document.documentElement.dataset.theme === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = cur;
    store.set("fh_theme", cur);
  });
}

document.documentElement.dataset.theme = store.get("fh_theme", "dark");
hydrateIcons();
wireEvents();
load();
