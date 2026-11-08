#!/usr/bin/env python3
"""Build flashcards-nia-h01.html from hoofdstuk-01-notes.md (the notes stay the source of truth)."""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE / "hoofdstuk-01-notes.md"
OUT = HERE / "flashcards-nia-h01.html"


def clean(s):
    s = re.sub(r"\*+", "", s)
    return re.sub(r"\s+", " ", s).strip()


def page(s):
    s = clean(s)
    return "" if s in ("", "–", "-") else s


def table_rows(lines):
    """Yield cell lists for data rows of pipe tables (skips header + separator)."""
    rows, seen_header = [], False
    for ln in lines:
        if not ln.startswith("|"):
            seen_header = False
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells):
            seen_header = True
            continue
        if not seen_header:  # header row
            continue
        rows.append(cells)
    return rows


def sections(text):
    """Split into {heading: [lines]} on ## and ### headings."""
    out, cur = {}, None
    for ln in text.splitlines():
        m = re.match(r"#{2,3} (.*)", ln)
        if m:
            cur = m.group(1).strip()
            out[cur] = []
        elif cur is not None:
            out[cur].append(ln)
    return out


def split_word(cell):
    """'vernoemen (naar) → *vernoemd naar*' -> (front, detail)."""
    detail = []
    if "→" in cell:
        cell, seen = cell.split("→", 1)
        detail.append("in de tekst: " + clean(seen))
    m = re.search(r"\(mv\.\s*([^)]*)\)", cell)
    if m:
        detail.append("mv. " + clean(m.group(1)))
        cell = cell.replace(m.group(0), "")
    return clean(cell), detail


# Example sentences in the notes that do not contain their preposition (or contain
# it only inside another word) get a replacement sentence so the blank works.
EXAMPLE_OVERRIDES = {
    "benieuwd": "Ik ben benieuwd naar je nieuwe baan.",
    "merken": "Ik merk niets van het lawaai.",
    "onderzoek doen": "Zij doet onderzoek naar kinderziektes.",
    "zich ergeren": "Ik erger me aan het lawaai.",
    "hangen": "De jas hangt aan de deur.",
    "verwerken": "In zijn schilderijen verwerkt hij zijn herinneringen aan zijn eigen land.",
}


def blank_out(sentence, prep):
    first = clean(prep.split("/")[0])
    new, n = re.subn(r"(?<!\w)" + re.escape(first) + r"(?!\w)", "____", sentence, count=1, flags=re.I)
    return new if n else ""


def conjugation(r):
    """'merk / merkt', 'merkte / merkten', 'heeft gemerkt' -> ['merk/merkt', 'merkte', 'heeft gemerkt']."""
    pres = clean(r[2]).replace(" / ", "/")
    sg, _, pl = clean(r[3]).partition(" / ")
    if "…" in pl and "…" not in sg:  # keep separable part / reflexive pronoun
        sg += " " + pl[pl.index("…"):]
    return [pres, sg, clean(r[4])]


STOP = {"voor", "naar", "aan", "van", "bij", "zich", "hebben", "een", "het"}


def terms(*cells):
    """Words of a lemma (article/brackets removed) that should be highlighted in the example."""
    out = []
    for c in cells:
        c = re.sub(r"\(.*?\)", " ", c)
        for w in re.findall(r"[^\W\d_]+", c.lower()):
            if len(w) >= 4 and w not in STOP and w not in out:
                out.append(w)
    return out


def build():
    text = NOTES.read_text(encoding="utf-8")
    sec = sections(text)
    cards = []

    def add(deck, nl, en, detail="", pg="", prep="", blank="", art="", conj=None, items=None, ex="", hl=None, exact=False, phrase=""):
        if nl and en:
            cards.append({"deck": deck, "nl": nl, "en": en, "detail": detail, "page": pg, "prep": prep, "blank": blank, "art": art, "conj": conj or [], "items": items or [], "ex": ex, "hl": hl or [], "exact": exact, "phrase": phrase})
        else:
            print(f"WARN: skipped row in {deck}: {nl!r} / {en!r}", file=sys.stderr)

    woorden = table_rows(sec["1. Nieuwe woorden (Woordenlijst)"])
    for r in woorden:
        nl, det = split_word(r[0])
        lemma = re.sub(r"^(de|het)\s+", "", nl)
        seen = [d.split(":", 1)[1] for d in det if d.startswith("in de tekst")]
        pl = [d[3:].strip() for d in det if d.startswith("mv.")]
        add("Woorden", nl, clean(r[1]), " · ".join(det), page(r[3]),
            ex=clean(r[2]), hl=terms(lemma, *seen, *pl))

    # Words deck: same cards as Woorden, but English on top (handled in the page).
    cards.extend(dict(c, deck="Words") for c in [c for c in cards if c["deck"] == "Woorden"])

    # Artikel deck: every noun that starts with de/het. Front = the noun, back = the article.
    for r in woorden:
        nl, _ = split_word(r[0])
        m = re.match(r"(de|het)\s+(.+)", re.sub(r"\s*\(.*?\)", "", nl))
        if m:
            ex = clean(r[2])
            pl = [d[3:].strip() for d in split_word(r[0])[1] if d.startswith("mv.")]
            add("Artikel", m.group(2).strip(), clean(r[1]), "", page(r[3]), art=m.group(1),
                ex=ex, hl=terms(m.group(2), *pl))

    for name in ("Regelmatige werkwoorden", "Onregelmatige werkwoorden"):
        for r in table_rows(sec[name]):
            add("Werkwoorden", clean(r[0]), clean(r[1]), "", conj=conjugation(r))

    for r in table_rows(sec["4. Prepositie (prepositions)"]):
        word, prep = clean(r[0]), clean(r[1])
        ex = EXAMPLE_OVERRIDES.get(word, clean(r[3]))
        blank = blank_out(ex, prep)
        if not blank:
            print(f"WARN: no blank possible for {word!r}: {ex!r}", file=sys.stderr)
        add("Prepositie", word, clean(r[2]), "", page(r[4]), prep=prep, blank=blank,
            ex=ex, hl=[clean(prep.split("/")[0]).lower()], exact=True)

    for r in table_rows(sec["5. Nuttige uitdrukkingen (useful expressions)"]):
        nl, ex = clean(r[0]), ""
        if " — " in nl:
            nl, ex = nl.split(" — ", 1)
        # Back shows the example sentence (or the expression itself when it is already a
        # sentence) with the expression highlighted, then the meaning.
        add("Uitdrukkingen", nl, clean(r[1]), "", page(r[3]), ex=clean(ex) or nl, phrase=nl)

    # Struikelwoorden: "### word" followed by numbered senses or a single line
    start = list(sec).index("2. Struikelwoorden") + 1
    for head in list(sec)[start:]:
        if head.startswith(("3.", "Regelmatige", "Onregelmatige")):
            break
        senses, exs, items = [], [], []
        for ln in sec[head]:
            ln = re.sub(r"^\d+\.\s*", "", ln.strip())
            if not ln or ln == "---":
                continue
            sense, _, ex = ln.partition(" — ")
            senses.append(clean(sense))
            items.append([clean(sense), clean(ex)])
            if ex:
                exs.append(clean(ex))
        add("Struikelwoorden", clean(head), " / ".join(senses), " · ".join(exs), items=items, hl=terms(head))

    return cards


TEMPLATE = r"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nederlands in actie – Hoofdstuk 1</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&family=Shantell+Sans:ital,wght@1,500;1,600;1,700&display=swap" rel="stylesheet">
<style>
:root{--bg:#0b0b0d;--fg:#f4f4f5;--card:#17171b;--muted:#9a9aa5;--accent:#ff9f43;--ok:#3ddc84;--line:#2b2b33;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.4 'Rubik',system-ui,sans-serif;padding:16px;display:flex;justify-content:center}
main{width:100%;max-width:640px}
.book{color:var(--accent);font-size:.85rem;font-weight:600;letter-spacing:.04em;text-transform:uppercase;margin-bottom:2px}
h1{font-size:1.2rem;margin:0 0 12px}
.bar{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px;align-items:center}
.chip{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:6px 12px;cursor:pointer;font:inherit;font-size:.85rem}
.chip{border-color:var(--c,var(--line))}
.chip.on{background:var(--c,var(--accent));border-color:var(--c,var(--accent));color:#0b0b0d;font-weight:600}
.stat{color:var(--muted);font-size:.85rem;margin:4px 0 12px}
.card{--c:var(--accent);background:var(--card);border:2px solid var(--c);box-shadow:0 0 24px color-mix(in srgb,var(--c) 28%,transparent);border-radius:16px;min-height:260px;padding:24px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;cursor:pointer;user-select:none}
.main{font-family:'Shantell Sans','Rubik',sans-serif;font-style:italic;font-size:1.7rem;font-weight:600;overflow-wrap:anywhere}
.main.answer{color:#8dffb5}
.card.yel .main.answer{color:#ffd43b}
.card.yel .hit{color:#ffd43b}
.card.big .main{font-size:2.3rem}
.card.small .main{font-size:1.95rem}
.main.sent{font-size:1.55rem;font-weight:700}
.card.bigback .main{font-size:2.1rem}
.yellow{color:#ffd43b;font-size:1.15rem}
.hit{color:#8dffb5;font-weight:700}
.items{text-align:left;width:100%;display:flex;flex-direction:column;gap:12px;font-size:1.05rem;font-weight:600}
.item .ex,.card .detail{font-family:'Shantell Sans','Rubik',sans-serif;font-style:italic}
.item .ex{font-weight:600}
.item .sn{font-weight:400;font-size:.95rem;color:var(--c);margin-top:2px}
.detail{margin-top:14px;color:var(--muted);font-size:.95rem}
.hint{color:var(--muted);font-size:.8rem;margin-top:16px}
.tag{font-size:.8rem;color:var(--c);font-weight:600;margin-bottom:12px}
.card .detail{color:#c9c9d1}
.actions{display:flex;gap:8px;margin-top:12px}
.actions button{flex:1;padding:12px;border-radius:12px;border:1px solid var(--line);background:var(--card);color:var(--fg);font:inherit;cursor:pointer}
.actions .good{background:var(--ok);border-color:var(--ok);color:#0b0b0d;font-weight:600}
.actions .show{border-color:#4dabf7;color:#4dabf7}
.done{font-size:1.3rem}
</style>
</head>
<body>
<main>
<div class="book">Nederlands in actie</div>
<h1>Hoofdstuk 1 — Identiteit</h1>
<div class="bar" id="decks"></div>
<div class="bar">
  <button class="chip" id="shuffle">Shuffle</button>
  <button class="chip" id="reset">Opnieuw beginnen</button>
</div>
<div class="stat" id="stat"></div>
<div class="card" id="card" tabindex="0" role="button" aria-label="Flip card"></div>
<div class="actions">
  <button id="back">Terug (←)</button>
  <button class="show" id="show">Toon (↓)</button>
  <button class="good" id="knew">Wist ik (→)</button>
</div>
</main>
<script>
const CARDS = /*CARDS*/[];
const DECKS = [...new Set(CARDS.map(c => c.deck))];
const COLORS = {Woorden:"#3ddc84",Words:"#22d3ee",Werkwoorden:"#ff9f43",Prepositie:"#4dabf7",Uitdrukkingen:"#f06595",Struikelwoorden:"#ffd43b",Artikel:"#b197fc"};
const col = d => COLORS[d] || "#b197fc";
const KEY = "nt2-h1-flashcards";
let st = {decks: [DECKS[0]], known: {}};
try { Object.assign(st, JSON.parse(localStorage.getItem(KEY)) || {}); } catch (e) {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) {} };
let queue = [], flipped = false, history = [];
const $ = id => document.getElementById(id);

function kk(i) { return String(i); }
function build(shuffle) {
  queue = CARDS.map((c, i) => i).filter(i => st.decks.includes(CARDS[i].deck) && !st.known[kk(i)]);
  if (shuffle) for (let i = queue.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1)); [queue[i], queue[j]] = [queue[j], queue[i]];
  }
  flipped = false; history = []; render();
}
function hlHtml(text, k) {
  if (!k.hl.length) return esc(text);
  let done = false;
  return text.split(/([\p{L}]+)/u).map(part => {
    if (!/^\p{L}+$/u.test(part)) return esc(part);
    const w = part.toLowerCase();
    const hit = k.exact ? (!done && k.hl.includes(w)) : k.hl.some(t => w.includes(t.length > 5 && t.endsWith("en") ? t.slice(0, -2) : t));
    if (hit) done = true;
    return hit ? `<span class="hit">${esc(part)}</span>` : esc(part);
  }).join("");
}
function phraseHtml(k) {
  const i = k.ex.toLowerCase().indexOf(k.phrase.toLowerCase());
  if (i < 0) return esc(k.ex);
  const j = i + k.phrase.length;
  return esc(k.ex.slice(0, i)) + `<span class="hit">${esc(k.ex.slice(i, j))}</span>` + esc(k.ex.slice(j));
}
function esc(s) { return s.replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
function render() {
  $("decks").innerHTML = DECKS.map(d =>
    `<button class="chip ${st.decks.includes(d) ? "on" : ""}" style="--c:${col(d)}" data-d="${esc(d)}">${esc(d)}</button>`).join("");
  $("stat").textContent = `${queue.length} kaarten over`;
  $("show").textContent = flipped ? "Verberg (↑)" : "Toon (↓)";
  const c = $("card");
  if (!queue.length) { c.innerHTML = '<div class="done">Klaar! 🎉</div><div class="hint">Kies "Opnieuw beginnen" om te herhalen.</div>'; return; }
  const k = CARDS[queue[0]], nlFirst = k.deck !== "Words";  // "Words" = English on top
  let front = nlFirst ? k.nl : k.en, back = nlFirst ? k.en : k.nl, detail = k.detail;
  let exHtml = k.ex ? hlHtml(k.ex, k) : "";
  const conjHtml = k.conj.map(esc).join("<br>");
  if (k.conj.length) {
    if (nlFirst) { back = k.conj.join(", "); detail = k.en; }
    else { back = k.nl; detail = k.conj.join(", "); }
  }
  if (k.art) {
    if (nlFirst) { back = k.art; detail = k.en; }
    else { back = k.art + " " + k.nl; detail = ""; }
  }
  if (k.prep) {
    if (nlFirst) { back = k.prep; detail = k.en; }
    else { back = k.nl + " " + k.prep; detail = ""; }
  }
  const detailHtml = k.phrase ? `<span class="yellow">${esc(k.en)}</span>`
    : k.conj.length && nlFirst ? `<span class="yellow">${esc(detail)}</span>`
    : k.conj.length ? conjHtml
    : [detail ? esc(detail) : "", exHtml].filter(Boolean).join(" · ");
  const meta = esc(k.deck);
  const numbered = k.items.length > 1;
  const listHtml = k.items.map(([sn, ex], i) =>
    `<div class="item"><div class="ex">${numbered ? (i + 1) + ". " : ""}${hlHtml(ex || sn, k)}</div>${ex ? `<div class="sn">${esc(sn)}</div>` : ""}</div>`).join("");
  const showList = flipped && nlFirst && k.items.length;
  c.style.setProperty("--c", col(k.deck));
  c.classList.toggle("yel", k.deck === "Woorden" || k.deck === "Words");
  c.classList.toggle("bigback", (k.deck === "Woorden" || k.deck === "Words") && flipped);
  c.classList.toggle("small", k.deck === "Werkwoorden" && flipped);
  c.classList.toggle("big", (k.deck === "Werkwoorden" || k.deck === "Woorden" || k.deck === "Words" || k.deck === "Prepositie") && !flipped);
  c.innerHTML = `${showList ? `<div class="items">${listHtml}</div>` : `<div class="main${flipped && k.phrase ? " sent" : ""}${flipped && !k.conj.length && k.deck !== "Uitdrukkingen" ? " answer" : ""}">${flipped && k.phrase ? phraseHtml(k) : flipped && k.conj.length && nlFirst ? conjHtml : esc(flipped ? back : front)}</div>`}` +
    (!flipped && nlFirst && k.blank ? `<div class="detail">${esc(k.blank)}</div>` : "") +
    (flipped && detailHtml && !showList ? `<div class="detail">${detailHtml}</div>` : "") +
    (flipped ? "" : '<div class="hint">klik of ↓ om te tonen</div>');
}
function setFlip(v) { if (queue.length && flipped !== v) { flipped = v; render(); } }
function flip() { if (queue.length) { flipped = !flipped; render(); } }
function back() {
  const h = history.pop(); if (!h) return;
  if (h.a === "knew") { delete st.known[kk(h.i)]; save(); queue.unshift(h.i); }
  flipped = false; render();
}
function knew() { if (queue.length) { history.push({i: queue[0], a: "knew"}); st.known[kk(queue.shift())] = 1; save(); flipped = false; render(); } }

$("card").onclick = flip;
$("show").onclick = () => setFlip(!flipped);
$("back").onclick = back;
$("knew").onclick = knew;
$("shuffle").onclick = () => build(true);
$("reset").onclick = () => { st.known = {}; save(); build(false); };
$("decks").onclick = e => {
  const d = e.target.dataset.d; if (!d) return;
  st.decks = [d];
  save(); build(false);
};
document.addEventListener("keydown", e => {
  if (e.key === " ") { e.preventDefault(); flip(); }
  else if (e.key === "ArrowRight") knew();
  else if (e.key === "ArrowLeft") back();
  else if (e.key === "ArrowDown") { e.preventDefault(); setFlip(true); }
  else if (e.key === "ArrowUp") { e.preventDefault(); setFlip(false); }
});
if (st.decks.length !== 1 || !DECKS.includes(st.decks[0])) st.decks = [DECKS[0]];
build(false);
</script>
</body>
</html>
"""


def main():
    cards = build()
    cards.sort(key=lambda c: c["deck"] == "Artikel")  # stable: Artikel deck goes last
    counts = {}
    for c in cards:
        counts[c["deck"]] = counts.get(c["deck"], 0) + 1
    html = TEMPLATE.replace("/*CARDS*/[]", json.dumps(cards, ensure_ascii=False).replace("</", "<\\/"))
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT} with {len(cards)} cards: {counts}")


if __name__ == "__main__":
    main()
