---
name: flashcards
description: Build a flashcard web page from a hoofdstuk notes file in this repo (e.g. coutinho/nederlands-in-actie/hoofdstuk-01/hoofdstuk-01-notes.md). Use when the user asks for flashcards, a flashcard deck, or to practise the words of a hoofdstuk or note.
---

# Flashcards from a hoofdstuk note

Turns the vocabulary tables in a `hoofdstuk-NN-notes.md` file into one self-contained,
offline-friendly HTML page. The notes stay the single source of truth: never edit the
generated HTML by hand, change the notes (or the script) and regenerate.

## Run

```bash
python3 .claude/skills/flashcards/build_flashcards.py <path/to/hoofdstuk-NN-notes.md>
```

- Output: `flashcards-nia-hNN.html` next to the notes file (override with `--out <file>`).
- The script prints the card count per deck and `WARN:` lines for anything it skipped.
- Needs only Python 3 (standard library). The page loads Rubik and Shantell Sans from Google Fonts.

## What it reads from the notes

Sections are found by heading keyword (numbering ignored). A missing section is skipped with a warning.

| Heading contains | Table columns expected | Deck(s) |
|---|---|---|
| `Woordenlijst` | Woord, Betekenis, Voorbeeldzin, Pag. | Woorden (Dutch on top), Words (English on top), Artikel (nouns starting with de/het) |
| `Regelmatige werkwoorden` / `Onregelmatige werkwoorden` | Infinitief, Betekenis, Presens, Imperfectum, Perfectum | Werkwoorden |
| `Prepositie` (or `Voorzetsel`) | Woord, Prepositie, Betekenis, Voorbeeldzin, Pag. | Prepositie (example sentence with the preposition blanked) |
| `uitdrukkingen` | Nederlands, Betekenis, Formeel / informeel, Pag. | Uitdrukkingen |
| `Struikelwoorden` | `### word` headings with numbered senses `N. sense = English — *example*` | Struikelwoorden |

Card behaviour (front / back) is fixed in the script's page template; see the code for details.
The Artikel deck is always last. Page numbers are never shown.

## After running

1. Check the `WARN:` output. A Prepositie row whose example sentence does not contain its
   preposition (or only inside another word) cannot be blanked: add a replacement sentence
   to `EXAMPLE_OVERRIDES` in `build_flashcards.py` (keyed by the Woord) and rerun. Tell the
   user which sentences were written by you rather than taken from the notes.
2. Open the page in a browser to spot-check a card from each deck, or tell the user you have
   not looked at it.
3. Commit only if the user asks.

## Notes rule

`.claude/rules/notes-no-exercises.md` applies to the notes: do not add exercises
(Oefenzinnen / Opdracht N) to the notes in order to feed the flashcards.

## Changing the cards

Layout, colours, fonts and key bindings live in the HTML/CSS/JS template inside
`build_flashcards.py`. Edit the template there, rerun on each chapter you want updated, and
verify with headless Chrome (`google-chrome --headless --dump-dom file://…`) if you need to
check card text.
