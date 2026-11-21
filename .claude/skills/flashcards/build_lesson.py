#!/usr/bin/env python3
"""Build a Memrise-style learning lesson from a hoofdstuk notes file.

Usage: build_lesson.py <path/to/notes-nia-hoofdstuk-NN.md> [--out <file.html>]
Default output: lesson-nia-hNN.html next to the notes file.

Reuses the notes parser of build_flashcards.py (Woordenlijst table only).
The notes stay the source of truth: regenerate, never edit the HTML by hand.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_flashcards import build  # noqa: E402


def items_from(text):
    out = []
    for c in build(text):
        if c["deck"] != "Woorden":
            continue
        m = re.match(r"(de|het)\s+(.+)", c["nl"])
        out.append({
            "id": len(out), "nl": c["nl"], "en": c["en"], "detail": c["detail"],
            "ex": "" if c["ex"] in ("–", "-") else c["ex"], "hl": c["hl"], "art": m.group(1) if m else "",
            "noun": m.group(2) if m else "",
        })
    return out


TEMPLATE = r"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>/*BOOK*/ – /*TITLE*/ – les</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&family=Shantell+Sans:ital,wght@1,500;1,600;1,700&display=swap" rel="stylesheet">
<style>
:root{--bg:#0b0b0d;--fg:#f4f4f5;--card:#17171b;--muted:#9a9aa5;--accent:#ff9f43;--ok:#3ddc84;--bad:#ff6b6b;--blue:#4dabf7;--line:#2b2b33;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.4 'Rubik',system-ui,sans-serif;padding:16px;display:flex;justify-content:center}
main{width:100%;max-width:560px;min-height:calc(100vh - 32px);display:flex;flex-direction:column}
.book{color:var(--accent);font-size:.85rem;font-weight:600;letter-spacing:.04em;text-transform:uppercase}
h1{font-size:1.3rem;margin:2px 0 16px}
button{font:inherit;color:inherit;cursor:pointer}
.btn{width:100%;padding:14px;border-radius:14px;border:1px solid var(--line);background:var(--card);font-weight:600}
.btn.go{background:var(--ok);border-color:var(--ok);color:#0b0b0d}
.btn.blue{background:var(--blue);border-color:var(--blue);color:#0b0b0d}
.btn.ghost{color:var(--muted);font-weight:500}
.btn[disabled]{opacity:.4;cursor:default}
.menu{display:flex;flex-direction:column;gap:10px}
.menu .btn{display:flex;justify-content:space-between;align-items:center;text-align:left;padding:16px}
.menu .btn small{display:block;font-weight:400;color:#1d1d22;font-size:.8rem}
.menu .btn.dark small{color:var(--muted)}
.badge{background:#0b0b0d33;border-radius:999px;padding:2px 10px;font-size:.85rem}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:16px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 4px;text-align:center}
.stat b{display:block;font-size:1.25rem}
.stat span{color:var(--muted);font-size:.72rem}
.top{display:flex;align-items:center;gap:12px;margin-bottom:18px}
.x{background:none;border:0;color:var(--muted);font-size:1.4rem;padding:0 4px}
.prog{flex:1;height:10px;background:var(--line);border-radius:99px;overflow:hidden}
.prog i{display:block;height:100%;background:var(--ok);border-radius:99px;transition:width .3s}
.pts{color:var(--accent);font-weight:600;font-size:.9rem;min-width:56px;text-align:right}
.stage{flex:1;display:flex;flex-direction:column;justify-content:center;gap:18px}
.prompt{text-align:center}
.label{color:var(--muted);font-size:.8rem;margin-bottom:8px}
.big{font-family:'Shantell Sans','Rubik',sans-serif;font-style:italic;font-weight:700;font-size:2.1rem;overflow-wrap:anywhere}
.big.en{color:#22d3ee}
.sub{color:var(--muted);margin-top:6px;font-size:.95rem}
.ex{font-family:'Shantell Sans','Rubik',sans-serif;font-style:italic;font-size:1.05rem;margin-top:14px;color:#d8d8df}
.hit{color:#8dffb5;font-weight:700}
.intro{background:var(--card);border:2px solid var(--accent);border-radius:16px;padding:24px;text-align:center;box-shadow:0 0 24px #ff9f4333}
.intro .big{color:#ffd43b}
.intro .mean{font-size:1.25rem;margin-top:10px;color:#8dffb5;font-weight:600}
.opts{display:grid;gap:10px}
.opt{display:flex;gap:12px;align-items:center;text-align:left;padding:14px;border-radius:14px;border:2px solid var(--line);background:var(--card);font-size:1.05rem}
.opt kbd{border:1px solid var(--line);border-radius:6px;padding:0 7px;color:var(--muted);font:.8rem 'Rubik';flex:none}
.opt:hover:not([disabled]){border-color:var(--blue)}
.opt.ok{border-color:var(--ok);background:#3ddc8426}
.opt.no{border-color:var(--bad);background:#ff6b6b26}
.opts.two{grid-template-columns:1fr 1fr}.opts.two .opt{justify-content:center;font-size:1.3rem;font-weight:700}
.opts.two .opt kbd{display:none}
input.ans{width:100%;padding:16px;border-radius:14px;border:2px solid var(--line);background:var(--card);color:var(--fg);font:inherit;font-size:1.3rem;text-align:center}
input.ans:focus{outline:none;border-color:var(--blue)}
input.ans.ok{border-color:var(--ok)}input.ans.no{border-color:var(--bad)}
.spk{background:var(--card);border:2px solid var(--blue);border-radius:50%;width:84px;height:84px;font-size:2rem;margin:0 auto;display:block}
.spk.sm{width:44px;height:44px;font-size:1.1rem;display:inline-block;margin:0 0 0 8px;vertical-align:middle}
.fb{border-radius:14px;padding:14px 16px;margin-top:4px}
.fb.ok{background:#3ddc8426;border:1px solid var(--ok)}
.fb.no{background:#ff6b6b26;border:1px solid var(--bad)}
.fb b{display:block;font-size:1.05rem;margin-bottom:2px}
.fb .ex{margin-top:6px;font-size:.95rem}
.foot{margin-top:16px;display:flex;flex-direction:column;gap:8px}
.timer{font-variant-numeric:tabular-nums;font-weight:700;color:var(--blue);min-width:56px}
.combo{color:var(--accent);font-weight:700;text-align:center;min-height:1.4em}
.done{text-align:center;font-size:1.4rem}
.done .row{display:flex;justify-content:center;gap:24px;margin:18px 0;font-size:1rem;color:var(--muted)}
.done .row b{display:block;color:var(--fg);font-size:1.6rem}
.chips{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:12px}
.chip{border:1px solid var(--line);background:var(--card);border-radius:999px;padding:6px 12px;font-size:.9rem}
.hint{color:var(--muted);font-size:.8rem;text-align:center;margin-top:8px}
</style>
</head>
<body>
<main id="app"></main>
<script>
const ITEMS = /*ITEMS*/[];
const KEY = "nt2-/*ID*/-lesson";
const BATCH = 5, REVIEW_N = 10, SPEED_SECS = 60;
const MIN = [0, 10, 1440, 4320, 10080, 30240]; // minutes until next review per level
const EMOJI = ["", "🌱", "🌿", "🌸", "🌷", "🌳"];
let st = {lv: {}, due: {}, pts: 0, last: "", streak: 0, best: 0};
try { Object.assign(st, JSON.parse(localStorage.getItem(KEY)) || {}); } catch (e) {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) {} };
const $ = s => document.querySelector(s), app = $("#app");
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const pick = a => a[Math.floor(Math.random() * a.length)];
const today = () => new Date().toISOString().slice(0, 10);

// ---------- text helpers
const shortEn = en => en.replace(/^hier:\s*/, "").split(/;\s*ook:/)[0].trim();
const norm = s => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, " ").trim();
const stripArt = s => s.replace(/^(de|het|een) /, "");
const spoken = it => it.nl.replace(/\(.*?\)/g, " ").replace(/…/g, " ").replace(/\s+/g, " ").trim();
function forms(it) {
  const base = it.nl.replace(/^(de|het)\s+/, "");
  return [base.replace(/\(.*?\)/g, " "), base.replace(/[()]/g, " ")].map(f => stripArt(norm(f)));
}
function lev(a, b) {
  const d = Array.from({length: a.length + 1}, (_, i) => [i, ...Array(b.length).fill(0)]);
  for (let j = 1; j <= b.length; j++) d[0][j] = j;
  for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++)
    d[i][j] = Math.min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + (a[i-1] === b[j-1] ? 0 : 1));
  return d[a.length][b.length];
}
function hl(it) {
  return it.ex.split(/([\p{L}]+)/u).map(p => {
    if (!/^\p{L}+$/u.test(p)) return esc(p);
    const w = p.toLowerCase();
    return it.hl.some(t => w.includes(t.length > 5 && t.endsWith("en") ? t.slice(0, -2) : t)) ? `<span class="hit">${esc(p)}</span>` : esc(p);
  }).join("");
}

// ---------- speech
let voices = [];
function loadVoices() { try { voices = speechSynthesis.getVoices(); } catch (e) {} }
try { loadVoices(); speechSynthesis.onvoiceschanged = loadVoices; } catch (e) {}
const canSpeak = () => voices.some(v => v.lang.toLowerCase().startsWith("nl"));
function speak(t) {
  try {
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(t); u.lang = "nl-NL"; u.rate = .9;
    const v = voices.find(v => v.lang.toLowerCase().startsWith("nl")); if (v) u.voice = v;
    speechSynthesis.speak(u);
  } catch (e) {}
}

// ---------- question building
function options(it, field) {
  const key = field === "en" ? (x => shortEn(x.en)) : (x => x.nl);
  const me = key(it);
  const pool = ITEMS.filter(x => x.id !== it.id && key(x) !== me && shortEn(x.en) !== shortEn(it.en));
  const same = pool.filter(x => !!x.art === !!it.art);
  const src = same.length >= 6 ? same : pool;
  const near = src.map(x => [Math.abs(key(x).length - me.length) + Math.random() * 6, x]).sort((a, b) => a[0] - b[0]).slice(0, 12).map(p => p[1]);
  return shuffle([it, ...shuffle(near).slice(0, 3)]);
}
function stepsFor(it) {
  return [...(Math.random() < .5 ? ["mc_ne", "mc_en"] : ["mc_en", "mc_ne"]), ...(it.art ? ["art"] : []), ...(canSpeak() ? ["listen"] : []), "type"];
}
function reviewStep(it) {
  const l = st.lv[it.id] || 1;
  if (l <= 2) return pick(["mc_ne", "mc_en"]);
  if (l === 3) return pick([it.art && "art", canSpeak() && "listen", "mc_en"].filter(Boolean));
  return "type";
}

// ---------- home
function due() { const n = Date.now(); return ITEMS.filter(i => i.id in st.lv && (st.due[i.id] || 0) <= n); }
function home() {
  const learned = ITEMS.filter(i => i.id in st.lv), fresh = ITEMS.length - learned.length, d = due();
  const mastered = learned.filter(i => st.lv[i.id] >= 5).length;
  const counts = [1, 2, 3, 4, 5].map(l => `<span class="chip">${EMOJI[l]} ${learned.filter(i => st.lv[i.id] === l).length}</span>`).join("");
  app.innerHTML = `
    <div class="book">/*BOOK*/</div><h1>/*TITLE*/ · les</h1>
    <div class="stats">
      <div class="stat"><b>${learned.length}/${ITEMS.length}</b><span>geleerd</span></div>
      <div class="stat"><b>${mastered}</b><span>beheerst</span></div>
      <div class="stat"><b>🔥 ${st.streak}</b><span>dagen</span></div>
      <div class="stat"><b>${st.pts}</b><span>punten</span></div>
    </div>
    <div class="menu">
      <button class="btn go" id="learn" ${fresh ? "" : "disabled"}><span>Nieuwe woorden leren<small>${fresh ? `volgende ${Math.min(BATCH, fresh)} van ${fresh}` : "alles geleerd 🎉"}</small></span><span class="badge">${Math.min(BATCH, fresh)}</span></button>
      <button class="btn blue" id="review" ${learned.length ? "" : "disabled"}><span>${d.length ? "Herhalen" : "Extra oefenen"}<small>${d.length ? "woorden die nu aan de beurt zijn" : "niets aan de beurt, oefen toch"}</small></span><span class="badge">${d.length}</span></button>
      <button class="btn dark" id="speed" ${ITEMS.length >= 4 ? "" : "disabled"}><span>Snelle ronde (${SPEED_SECS}s)<small>zoveel mogelijk goed · record: ${st.best}</small></span><span>⚡</span></button>
    </div>
    <div class="chips">${counts}</div>
    <div class="hint">🌱 nieuw → 🌳 beheerst · goed antwoord = hoger niveau, fout = lager</div>
    <div class="foot" style="margin-top:auto"><button class="btn ghost" id="reset">Voortgang wissen</button></div>`;
  $("#learn").onclick = startLearn; $("#review").onclick = startReview; $("#speed").onclick = startSpeed;
  $("#reset").onclick = () => { if (confirm("Alle voortgang wissen?")) { st = {lv: {}, due: {}, pts: 0, last: "", streak: 0, best: 0}; save(); home(); } };
}

// ---------- session core
let S = null, keyHandler = null;
function setKeys(fn) { keyHandler = fn; }
document.addEventListener("keydown", e => { if (keyHandler) keyHandler(e); });
function bump() {
  const t = today();
  if (st.last !== t) { const y = new Date(Date.now() - 864e5).toISOString().slice(0, 10); st.streak = st.last === y ? st.streak + 1 : 1; st.last = t; }
}
function topBar(pct, extra) {
  return `<div class="top"><button class="x" id="quit" aria-label="Stoppen">✕</button><div class="prog"><i style="width:${pct}%"></i></div>${extra || `<div class="pts">${S.pts} pt</div>`}</div>`;
}
function bindQuit() { $("#quit").onclick = () => { if (S.kind === "speed") clearInterval(S.timer); setKeys(null); home(); }; }

function startLearn() {
  const fresh = ITEMS.filter(i => !(i.id in st.lv)).slice(0, BATCH);
  S = {kind: "learn", items: fresh, pts: 0, right: 0, wrong: 0, prog: {}, queue: [], total: 0, doneSteps: 0, intro: 0};
  fresh.forEach(i => { S.prog[i.id] = {steps: stepsFor(i), n: 0, miss: 0}; S.total += S.prog[i.id].steps.length; });
  intro();
}
function intro() {
  const it = S.items[S.intro];
  app.innerHTML = topBar(S.intro / S.items.length * 100, `<div class="pts">${S.intro + 1}/${S.items.length}</div>`) + `
    <div class="stage"><div class="label" style="text-align:center">Nieuw woord</div>
      <div class="intro"><div class="big">${esc(it.nl)}${canSpeak() ? `<button class="spk sm" id="spk">🔊</button>` : ""}</div>
        ${it.detail ? `<div class="sub">${esc(it.detail)}</div>` : ""}
        <div class="mean">${esc(it.en)}</div>
        ${it.ex ? `<div class="ex">${hl(it)}</div>` : ""}</div></div>
    <div class="foot"><button class="btn go" id="next">${S.intro + 1 < S.items.length ? "Volgende" : "Begin met oefenen"} (Enter)</button></div>`;
  bindQuit(); if ($("#spk")) $("#spk").onclick = () => speak(spoken(it));
  speak(spoken(it));
  const next = () => { S.intro++; if (S.intro < S.items.length) intro(); else { S.queue = shuffle(S.items.map(i => i.id)); ask(); } };
  $("#next").onclick = next; setKeys(e => { if (e.key === "Enter") next(); });
}

function startReview() {
  const d = due(), learned = ITEMS.filter(i => i.id in st.lv);
  const set = shuffle(d.length ? d : learned).slice(0, REVIEW_N);
  S = {kind: d.length ? "review" : "practice", items: set, pts: 0, right: 0, wrong: 0, prog: {}, queue: set.map(i => i.id), total: set.length, doneSteps: 0, changes: []};
  set.forEach(i => { S.prog[i.id] = {steps: [reviewStep(i)], n: 0, miss: 0, from: st.lv[i.id]}; });
  ask();
}

function ask() {
  if (!S.queue.length) return finish();
  const it = ITEMS[S.queue[0]], p = S.prog[it.id], type = p.steps[p.n];
  const pct = S.doneSteps / S.total * 100;
  S.cur = {it, type, locked: false};
  let body = "";
  if (type === "mc_ne") {
    S.cur.opts = options(it, "en"); S.cur.correct = it;
    body = `<div class="prompt"><div class="label">Wat betekent dit?</div><div class="big">${esc(it.nl)}</div>${it.detail ? `<div class="sub">${esc(it.detail)}</div>` : ""}</div>` + optsHtml(S.cur.opts, x => shortEn(x.en));
  } else if (type === "mc_en") {
    S.cur.opts = options(it, "nl"); S.cur.correct = it;
    body = `<div class="prompt"><div class="label">Hoe zeg je dit in het Nederlands?</div><div class="big en">${esc(shortEn(it.en))}</div></div>` + optsHtml(S.cur.opts, x => x.nl);
  } else if (type === "listen") {
    S.cur.opts = options(it, "nl"); S.cur.correct = it;
    body = `<div class="prompt"><div class="label">Wat hoor je?</div><button class="spk" id="spk">🔊</button></div>` + optsHtml(S.cur.opts, x => x.nl);
  } else if (type === "art") {
    body = `<div class="prompt"><div class="label">de of het?</div><div class="big">${esc(it.noun)}</div><div class="sub">${esc(shortEn(it.en))}</div></div><div class="opts two"><button class="opt" data-a="de">de</button><button class="opt" data-a="het">het</button></div>`;
  } else {
    body = `<div class="prompt"><div class="label">Typ het Nederlandse woord</div><div class="big en">${esc(shortEn(it.en))}</div></div><input class="ans" id="ans" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="…"><button class="btn blue" id="check">Controleer (Enter)</button><button class="btn ghost" id="dunno">Ik weet het niet</button>`;
  }
  app.innerHTML = topBar(pct) + `<div class="stage">${body}<div id="fb"></div></div><div class="foot" id="foot"></div>`;
  bindQuit();
  if (type === "listen") { $("#spk").onclick = () => speak(spoken(it)); speak(spoken(it)); }
  if (type === "type") {
    const a = $("#ans"); a.focus();
    $("#check").onclick = () => grade(a.value); $("#dunno").onclick = () => grade("");
    setKeys(e => { if (e.key === "Enter" && !S.cur.locked) grade(a.value); else if (e.key === "Enter") advance(); });
  } else {
    document.querySelectorAll(".opt").forEach(b => b.onclick = () => grade(b.dataset.a !== undefined ? b.dataset.a : +b.dataset.i));
    setKeys(e => {
      if (S.cur.locked) { if (e.key === "Enter") advance(); return; }
      const n = +e.key - 1, btns = document.querySelectorAll(".opt");
      if (n >= 0 && n < btns.length) btns[n].click();
      else if (type === "art" && (e.key === "d" || e.key === "h")) [...btns].find(b => b.dataset.a[0] === e.key).click();
    });
  }
}
function optsHtml(opts, label) {
  return `<div class="opts">${opts.map((x, i) => `<button class="opt" data-i="${i}"><kbd>${i + 1}</kbd><span>${esc(label(x))}</span></button>`).join("")}</div>`;
}

function grade(val) {
  const c = S.cur; if (c.locked) return; c.locked = true;
  const it = c.it; let ok = false, note = "";
  if (c.type === "art") ok = val === it.art;
  else if (c.type === "type") {
    const guess = stripArt(norm(val));
    const targets = ITEMS.filter(x => shortEn(x.en) === shortEn(it.en));
    if (guess) for (const t of targets) for (const f of forms(t)) {
      if (f === guess) ok = true;
      else if (!ok && f.length >= 5 && lev(f, guess) <= 1) { ok = true; note = `Let op de spelling: ${t.nl}`; }
    }
  } else ok = c.opts[val].id === it.id;
  // mark UI
  if (c.type === "type") { $("#ans").classList.add(ok ? "ok" : "no"); $("#ans").readOnly = true; $("#check").hidden = $("#dunno").hidden = true; }
  else document.querySelectorAll(".opt").forEach((b, i) => {
    b.disabled = true;
    const right = c.type === "art" ? b.dataset.a === it.art : c.opts[i].id === it.id;
    if (right) b.classList.add("ok"); else if (String(c.type === "art" ? b.dataset.a : i) === String(val)) b.classList.add("no");
  });
  const pr = S.prog[it.id];
  if (ok) { S.right++; S.pts += S.kind === "speed" ? 10 + Math.min(S.combo, 10) * 2 : 10; pr.n++; S.doneSteps++; if (S.kind === "speed") S.combo++; }
  else { S.wrong++; pr.miss++; if (S.kind === "speed") S.combo = 0; }
  if (S.kind === "speed") { setTimeout(() => { if (S.timer !== null) advanceSpeed(ok); }, ok ? 350 : 1100); showSpeedFb(ok, it); return; }
  $("#fb").innerHTML = `<div class="fb ${ok ? "ok" : "no"}"><b>${ok ? ["Goed!", "Precies!", "Juist!", "Top!"][Math.floor(Math.random() * 4)] : "Niet helemaal"} ${ok ? "" : "— " + esc(it.nl) + " = " + esc(it.en)}</b>${note ? esc(note) : ""}${it.ex ? `<div class="ex">${hl(it)}</div>` : ""}</div>`;
  $("#foot").innerHTML = `<button class="btn ${ok ? "go" : "blue"}" id="cont">Verder (Enter)</button>`;
  $("#cont").onclick = advance;
  S.cur.ok = ok;
  if (!ok) speak(spoken(it));
}
function advance() {
  const c = S.cur; if (!c || !c.locked) return;
  const id = S.queue.shift(), pr = S.prog[id];
  if (c.ok) { if (pr.n < pr.steps.length) S.queue.splice(Math.min(S.queue.length, 2 + Math.floor(Math.random() * 2)), 0, id); }
  else if (S.kind === "learn") S.queue.splice(Math.min(S.queue.length, 2), 0, id);  // ask again soon
  else { pr.failed = true; S.doneSteps++; }
  ask();
}

function finish() {
  setKeys(null); bump();
  const now = Date.now(); let changed = [];
  if (S.kind === "learn") S.items.forEach(i => { st.lv[i.id] = 1; st.due[i.id] = now + MIN[1] * 6e4; changed.push(i); });
  else if (S.kind === "review") S.items.forEach(i => {
    const p = S.prog[i.id], from = st.lv[i.id] || 1, to = p.failed ? Math.max(1, from - 1) : Math.min(5, from + 1);
    st.lv[i.id] = to; st.due[i.id] = now + MIN[p.failed ? 1 : to] * 6e4; changed.push(i);
  });
  st.pts += S.pts; save();
  const acc = S.right + S.wrong ? Math.round(S.right / (S.right + S.wrong) * 100) : 0;
  app.innerHTML = `<div class="stage"><div class="done">🎉<br>${S.kind === "learn" ? "Nieuwe woorden geleerd!" : "Ronde klaar!"}
    <div class="row"><div><b>${S.pts}</b>punten</div><div><b>${acc}%</b>goed</div><div><b>${S.items.length}</b>woorden</div></div>
    <div class="chips">${changed.map(i => `<span class="chip">${EMOJI[st.lv[i.id]]} ${esc(i.nl)}</span>`).join("")}</div></div></div>
    <div class="foot"><button class="btn go" id="again">Nog een ronde</button><button class="btn ghost" id="menu">Menu</button></div>`;
  $("#menu").onclick = home;
  $("#again").onclick = () => S.kind === "learn" ? (ITEMS.some(i => !(i.id in st.lv)) ? startLearn() : home()) : startReview();
}

// ---------- speed round
function startSpeed() {
  const learned = ITEMS.filter(i => i.id in st.lv);
  const pool = learned.length >= 8 ? learned : ITEMS;
  S = {kind: "speed", pts: 0, right: 0, wrong: 0, combo: 0, left: SPEED_SECS, pool, prog: {}, queue: [], total: 1, doneSteps: 0};
  ITEMS.forEach(i => S.prog[i.id] = {steps: ["mc_ne"], n: 0, miss: 0});
  S.timer = setInterval(() => { S.left--; const t = $("#timer"); if (t) t.textContent = S.left + "s"; const b = $(".prog i"); if (b) b.style.width = S.left / SPEED_SECS * 100 + "%"; if (S.left <= 0) endSpeed(); }, 1000);
  nextSpeed();
}
function nextSpeed() {
  const it = pick(S.pool); S.queue = [it.id]; S.prog[it.id].n = 0;
  S.cur = {it, type: "mc_ne", locked: false, opts: options(it, "en"), correct: it};
  app.innerHTML = topBar(S.left / SPEED_SECS * 100, `<div class="timer" id="timer">${S.left}s</div>`) + `<div class="stage"><div class="combo">${S.combo > 1 ? "🔥 x" + S.combo : ""} <span style="color:var(--muted)">${S.pts} pt</span></div>
    <div class="prompt"><div class="big">${esc(it.nl)}</div></div>${optsHtml(S.cur.opts, x => shortEn(x.en))}<div id="fb"></div></div>`;
  bindQuit();
  document.querySelectorAll(".opt").forEach(b => b.onclick = () => grade(+b.dataset.i));
  setKeys(e => { const n = +e.key - 1, btns = document.querySelectorAll(".opt"); if (!S.cur.locked && n >= 0 && n < btns.length) btns[n].click(); });
}
function showSpeedFb(ok, it) { if (!ok) $("#fb").innerHTML = `<div class="fb no"><b>${esc(it.nl)} = ${esc(it.en)}</b></div>`; }
function advanceSpeed() { if (S.timer !== null) nextSpeed(); }
function endSpeed() {
  clearInterval(S.timer); S.timer = null; setKeys(null); bump();
  const newBest = S.pts > st.best; if (newBest) st.best = S.pts; st.pts += S.pts; save();
  app.innerHTML = `<div class="stage"><div class="done">⚡<br>Tijd is om!${newBest ? "<br>Nieuw record!" : ""}
    <div class="row"><div><b>${S.pts}</b>punten</div><div><b>${S.right}</b>goed</div><div><b>${S.wrong}</b>fout</div></div></div></div>
    <div class="foot"><button class="btn go" id="again">Nog een keer</button><button class="btn ghost" id="menu">Menu</button></div>`;
  $("#menu").onclick = home; $("#again").onclick = startSpeed;
}

home();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("notes", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    notes = args.notes.resolve()
    text = notes.read_text(encoding="utf-8")
    num = re.search(r"hoofdstuk-(\d+)", notes.name)
    nn = num.group(1) if num else notes.stem
    out = args.out or notes.with_name(f"lesson-nia-h{nn}.html")
    m = re.match(r"#\s+(.+)", text)
    title = m.group(1).strip() if m else f"Hoofdstuk {nn}"
    book = notes.parent.parent.name.replace("-", " ").capitalize()
    items = items_from(text)
    html = TEMPLATE.replace("/*BOOK*/", book).replace("/*TITLE*/", title).replace("/*ID*/", f"h{nn}")
    html = html.replace("/*ITEMS*/[]", json.dumps(items, ensure_ascii=False).replace("</", "<\\/"))
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out} with {len(items)} words")


if __name__ == "__main__":
    main()
