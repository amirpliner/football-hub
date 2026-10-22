"use strict";

const TZ = "Asia/Jerusalem";
const PAGE = 60;
const CAT_LABEL = { news: "חדשות", analysis: "ניתוח", fan: "אוהדים" };

const $ = (id) => document.getElementById(id);

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
  leagues: {},     // id -> {name_he, teams}
  teamName: {},    // id -> שם
  teamLeague: {},  // id -> ליגה
  filters: { league: "", team: "", source: "", cat: "", q: "", dups: false, hideRead: false },
  view: "all",
  shown: PAGE,
  read: new Set(store.get("fh_read", [])),
  saved: store.get("fh_saved", {}),     // id -> עותק של הכתבה (שלא תיעלם אחרי 14 יום)
  watch: store.get("fh_watch", []),
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
  return fmtDay.format(date);
}

function ago(date) {
  const mins = Math.round((Date.now() - date.getTime()) / 60000);
  if (mins < 1) return "הרגע";
  if (mins < 60) return `לפני ${mins} דק׳`;
  const h = Math.round(mins / 60);
  if (h < 24) return `לפני ${h} שע׳`;
  return fmtTime.format(date);
}

// ---------- טעינה ----------
async function load() {
  try {
    const [cfgRes, dataRes] = await Promise.all([
      fetch("config/config.json", { cache: "no-cache" }),
      fetch("data/articles.json", { cache: "no-cache" }),
    ]);
    if (!cfgRes.ok || !dataRes.ok) throw new Error(`HTTP ${cfgRes.status}/${dataRes.status}`);
    const cfg = await cfgRes.json();
    const data = await dataRes.json();
    for (const [lid, league] of Object.entries(cfg.leagues)) {
      state.leagues[lid] = league;
      for (const [tid, team] of Object.entries(league.teams || {})) {
        state.teamName[tid] = team.name;
        state.teamLeague[tid] = lid;
      }
    }
    state.items = data.items.map((it) => ({ ...it, date: new Date(it.published) }));
    state.generatedAt = new Date(data.generated_at);
    pruneRead();
    buildControls();
    render();
  } catch (e) {
    $("status").textContent = "לא הצלחתי לטעון את הנתונים (" + e.message + "). אם פתחת את הקובץ ישירות מהמחשב, צריך להריץ שרת מקומי או לפתוח דרך GitHub Pages.";
  }
}

function pruneRead() {
  const ids = new Set(state.items.map((i) => i.id));
  // שומרים סימוני "נקרא" רק לכתבות שעדיין קיימות
  state.read = new Set([...state.read].filter((id) => ids.has(id)));
  store.set("fh_read", [...state.read]);
}

// ---------- בניית פקדים ----------
function buildControls() {
  const chips = $("league-chips");
  chips.textContent = "";
  const counts = {};
  for (const it of state.items) if (!it.dup_of) for (const l of it.leagues) counts[l] = (counts[l] || 0) + 1;
  const add = (id, label) => {
    const b = document.createElement("button");
    b.className = "chip" + (state.filters.league === id ? " on" : "");
    b.textContent = label;
    b.dataset.league = id;
    chips.appendChild(b);
  };
  add("", "כל הליגות");
  for (const [lid, league] of Object.entries(state.leagues)) add(lid, `${league.name_he}${counts[lid] ? " " + counts[lid] : ""}`);

  buildTeamSelect();

  const sources = [...new Set(state.items.map((i) => i.source))].sort((a, b) => a.localeCompare(b));
  const sel = $("f-source");
  sel.textContent = "";
  sel.append(new Option("כל המקורות", ""));
  for (const s of sources) sel.append(new Option(s, s));
}

function buildTeamSelect() {
  const sel = $("f-team");
  const present = new Set();
  for (const it of state.items) for (const t of it.teams) present.add(t);
  sel.textContent = "";
  sel.append(new Option("כל הקבוצות", ""));
  for (const [lid, league] of Object.entries(state.leagues)) {
    if (state.filters.league && state.filters.league !== lid) continue;
    const teams = Object.keys(league.teams || {}).filter((t) => present.has(t));
    if (!teams.length) continue;
    teams.sort((a, b) => state.teamName[a].localeCompare(state.teamName[b]));
    const og = document.createElement("optgroup");
    og.label = league.name_he;
    for (const t of teams) og.append(new Option(state.teamName[t], t));
    sel.append(og);
  }
  sel.value = state.filters.team;
  if (sel.value !== state.filters.team) state.filters.team = "";
}

// ---------- מילות מעקב ----------
function watchRegex() {
  if (!state.watch.length) return null;
  const alt = state.watch.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|");
  return new RegExp(alt, "gi");
}

function matchesWatch(it, rx) {
  if (!rx) return false;
  rx.lastIndex = 0;
  return rx.test(it.title + " " + it.summary);
}

function highlight(text, rx) {
  const frag = document.createDocumentFragment();
  if (!rx) { frag.append(text); return frag; }
  rx.lastIndex = 0;
  let last = 0, m;
  while ((m = rx.exec(text)) !== null) {
    if (m[0] === "") { rx.lastIndex++; continue; }
    if (m.index > last) frag.append(text.slice(last, m.index));
    const mk = document.createElement("mark");
    mk.textContent = m[0];
    frag.append(mk);
    last = m.index + m[0].length;
  }
  if (last < text.length) frag.append(text.slice(last));
  return frag;
}

// ---------- סינון ----------
function visibleItems() {
  const f = state.filters;
  const rx = watchRegex();
  const q = f.q.trim().toLowerCase();
  let pool = state.items;
  if (state.view === "saved") {
    // שמורים: כולל כתבות שכבר יצאו מהפיד
    const live = new Map(state.items.map((i) => [i.id, i]));
    pool = Object.values(state.saved).map((s) => live.get(s.id) || { ...s, date: new Date(s.published) });
    pool.sort((a, b) => b.date - a.date);
  }
  return pool.filter((it) => {
    if (state.view !== "saved" && !f.dups && it.dup_of) return false;
    if (state.view === "watch" && !matchesWatch(it, rx)) return false;
    if (f.league && !it.leagues.includes(f.league)) return false;
    if (f.team && !it.teams.includes(f.team)) return false;
    if (f.source && it.source !== f.source) return false;
    if (f.cat && it.category !== f.cat) return false;
    if (f.hideRead && state.read.has(it.id)) return false;
    if (q && !(it.title + " " + it.summary).toLowerCase().includes(q)) return false;
    return true;
  });
}

// ---------- ציור ----------
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

function renderCard(it, rx) {
  const card = el("article", "card" + (state.read.has(it.id) ? " read" : "") + (it.dup_of ? " dup" : ""));
  card.dataset.id = it.id;

  if (it.image) {
    const img = el("img", "thumb");
    img.src = it.image;
    img.alt = "";
    img.loading = "lazy";
    img.referrerPolicy = "no-referrer";
    img.addEventListener("error", () => img.remove());
    card.append(img);
  }

  const meta = el("div", "meta");
  meta.append(el("span", "src", it.source));
  const t = el("time", null, ago(it.date));
  t.dateTime = it.published;
  t.title = fmtTime.format(it.date);
  meta.append(t);
  if (it.category !== "news") meta.append(el("span", "tag cat", CAT_LABEL[it.category] || it.category));
  for (const l of it.leagues.slice(0, 2)) if (state.leagues[l]) meta.append(el("span", "tag", state.leagues[l].name_he));
  for (const tm of it.teams.slice(0, 2)) meta.append(el("span", "tag", state.teamName[tm] || tm));
  card.append(meta);

  const h = el("h2");
  const a = document.createElement("a");
  a.href = it.link;
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  a.lang = it.lang;
  a.dir = "auto";
  a.append(highlight(it.title, rx));
  const markRead = () => setRead(it.id, true);
  a.addEventListener("click", markRead);
  a.addEventListener("auxclick", markRead);
  h.append(a);
  card.append(h);

  if (it.summary) {
    const p = el("p", "sum");
    p.lang = it.lang;
    p.dir = "auto";
    p.append(highlight(it.summary, rx));
    card.append(p);
  }

  const acts = el("div", "acts");
  const save = el("button", state.saved[it.id] ? "on" : "", state.saved[it.id] ? "★ שמור" : "☆ לקרוא אחר כך");
  save.addEventListener("click", () => toggleSaved(it));
  const read = el("button", state.read.has(it.id) ? "on" : "", state.read.has(it.id) ? "✓ נקרא" : "סמן כנקרא");
  read.addEventListener("click", () => setRead(it.id, !state.read.has(it.id)));
  acts.append(save, read);
  if (it.also && it.also.length) {
    const more = el("button", "", `עוד ${it.also.length} מקורות`);
    more.addEventListener("click", () => {
      const open = card.querySelector(".also");
      if (open) { open.remove(); return; }
      const ul = el("ul", "also");
      for (const o of it.also) {
        const li = el("li");
        li.append(o.source + ": ");
        const link = document.createElement("a");
        link.href = o.link; link.target = "_blank"; link.rel = "noopener noreferrer";
        link.textContent = o.title; link.dir = "auto";
        li.append(link);
        ul.append(li);
      }
      card.append(ul);
    });
    acts.append(more);
  }
  card.append(acts);
  return card;
}

function render() {
  const rx = watchRegex();
  const items = visibleItems();
  const list = $("list");
  list.textContent = "";
  let lastDay = "";
  for (const it of items.slice(0, state.shown)) {
    const label = dayLabel(it.date);
    if (label !== lastDay) { list.append(el("div", "day", label)); lastDay = label; }
    list.append(renderCard(it, rx));
  }
  $("more").hidden = items.length <= state.shown;
  $("status").textContent = items.length
    ? `${items.length} כתבות · עודכן ${fmtDay.format(state.generatedAt)} ${fmtTime.format(state.generatedAt)}`
    : state.view === "saved" ? "אין עדיין כתבות שמורות."
    : state.view === "watch" ? (state.watch.length ? "אין כרגע כתבות שמתאימות למילות המעקב." : "עוד לא הוספת מילות מעקב. לחץ על \"מילות מעקב\".")
    : "אין כתבות שמתאימות לסינון.";
  $("n-saved").textContent = Object.keys(state.saved).length || "";
  $("n-watch").textContent = state.watch.length
    ? state.items.filter((i) => !i.dup_of && matchesWatch(i, rx)).length || "" : "";
}

// ---------- פעולות ----------
function setRead(id, value) {
  if (value) state.read.add(id); else state.read.delete(id);
  store.set("fh_read", [...state.read]);
  render();
}

function toggleSaved(it) {
  if (state.saved[it.id]) delete state.saved[it.id];
  else {
    const { date, ...plain } = it;
    state.saved[it.id] = plain;
  }
  store.set("fh_saved", state.saved);
  render();
}

function refilter() { state.shown = PAGE; render(); }

function wireEvents() {
  $("league-chips").addEventListener("click", (e) => {
    const b = e.target.closest(".chip");
    if (!b) return;
    state.filters.league = b.dataset.league;
    for (const c of $("league-chips").children) c.classList.toggle("on", c === b);
    buildTeamSelect();
    refilter();
  });
  $("views").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-view]");
    if (!b) return;
    state.view = b.dataset.view;
    for (const x of $("views").children) x.classList.toggle("on", x === b);
    refilter();
  });
  let timer;
  $("q").addEventListener("input", (e) => {
    clearTimeout(timer);
    timer = setTimeout(() => { state.filters.q = e.target.value; refilter(); }, 150);
  });
  $("f-team").addEventListener("change", (e) => { state.filters.team = e.target.value; refilter(); });
  $("f-source").addEventListener("change", (e) => { state.filters.source = e.target.value; refilter(); });
  $("f-cat").addEventListener("change", (e) => { state.filters.cat = e.target.value; refilter(); });
  $("f-dups").addEventListener("change", (e) => { state.filters.dups = e.target.checked; refilter(); });
  $("f-hide-read").addEventListener("change", (e) => { state.filters.hideRead = e.target.checked; refilter(); });
  $("more").addEventListener("click", () => { state.shown += PAGE; render(); });

  // מילות מעקב
  const dlg = $("dlg-keywords");
  const drawKw = () => {
    const ul = $("kw-list");
    ul.textContent = "";
    for (const w of state.watch) {
      const li = el("li", null, w);
      const x = el("button", null, "×");
      x.type = "button";
      x.setAttribute("aria-label", "הסר " + w);
      x.addEventListener("click", () => {
        state.watch = state.watch.filter((k) => k !== w);
        store.set("fh_watch", state.watch);
        drawKw(); render();
      });
      li.append(x);
      ul.append(li);
    }
  };
  const addKw = () => {
    const v = $("kw-input").value.trim();
    if (v && !state.watch.some((k) => k.toLowerCase() === v.toLowerCase())) {
      state.watch.push(v);
      store.set("fh_watch", state.watch);
      drawKw(); render();
    }
    $("kw-input").value = "";
    $("kw-input").focus();
  };
  $("btn-keywords").addEventListener("click", () => { drawKw(); dlg.showModal(); });
  $("kw-add").addEventListener("click", addKw);
  $("kw-input").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); addKw(); } });

  // פתיחת/סגירת הסינון במסך קטן
  $("btn-filters").addEventListener("click", () => {
    const open = $("filters").classList.toggle("open");
    $("btn-filters").setAttribute("aria-expanded", open);
  });

  // מצב כהה/בהיר
  $("btn-theme").addEventListener("click", () => {
    const cur = document.documentElement.dataset.theme === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = cur;
    store.set("fh_theme", cur);
  });
}

document.documentElement.dataset.theme = store.get("fh_theme", "dark");
wireEvents();
load();
