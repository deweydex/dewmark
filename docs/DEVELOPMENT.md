# dewmark development notes

This document is for people working on dewmark's own code. It explains
how the folder is organised, how to run everything, and — most
importantly — where the current draft falls short of the design
documents, so nobody mistakes a draft behaviour for a decision.

## dewmark stands alone

dewmark began inside the [dewlab](https://github.com/deweydex/dewlab)
repository and moved to its own in September 2026, with its history
(see `DECISIONS_LOG.md`, entry 0.1). It shares no code, styles, or
build machinery with dewlab: its pages repeat the colour palette rather
than importing it, and its tests run on their own. Anything it takes
from dewlab in future is copied, with a record of where it came from
(entry 0.3), never linked. The one thing shared with dewlab is its
working habits:
plain-spoken documents, why-comments in code, and tests beside every
program.

## Layout

```text
  build_exam.py        the exam builder: exam file in, finished pages out
  assets/
    exam-page.css      styles inlined into every built exam page
    exam-page.js       behaviour inlined into every built exam page
  workbench/
    index.html         the marking workbench, one self-contained page
  samples/             openly shareable exam files and their pictures
  tests/               the builder's automated tests
  dev/                 hand-run scripts, including the browser smoke test
  docs/                this file, and the guide for teachers
  planning/            the design documents (start with the README above)
```

## Running things

```sh
pip install -r requirements.txt -r requirements-dev.txt

# build the sample exam
python build_exam.py samples/sample-mixed-paper.exam.md \
    --output /tmp/dewmark-sample

# the builder's tests
python -m pytest

# the browser smoke tests (need Playwright and a Chromium; see each file)
python -m pytest tests/browser   # the saving rehearsals (Playwright + Chromium)
python dev/smoke_pages.py
python dev/smoke_python_page.py
```

The first smoke test builds the mixed sample exam, sits part of it in
a headless browser (answers several question types, finishes,
downloads the submission, reloads and restores), then loads the
marking workbench, marks with all three marking methods, and checks
the exports. The second does the same round trip for Python code
questions using the database practical sample: it waits for the
Python system, runs cells that query the embedded database, draw a
chart, and read a spreadsheet, checks the recorded outputs inside the
submission, and confirms the workbench displays a code answer.
Together they are the closest thing to a rehearsal that runs without a
person. `tests/browser/` holds the rehearsals for how the page saves:
each reproduces a way today's page once lost or mixed up answers
(a reload on the start screen, pages of one exam sharing a save slot,
a second window, the workbench counting its own files as students) and
fails if it returns. The repository's continuous checks run the
builder's tests, build every sample and the site, and run
`tests/browser/` and the first smoke test in Chromium; the Python smoke
test stays hand-run, since it downloads Pyodide.

## Where the draft falls short of the design

Each of these is a deliberate simplification in the current code, not a
decision against the design documents. The documents remain the target.

- **Mathematics typesets to MathML.** Text between dollar signs is
  converted at build time and rendered by the browser itself, with no
  typesetting program in the page. Browsers released before 2023 show
  it poorly; the older italic form remains only as the fallback for an
  expression the converter refuses, and the checks report every such
  expression so a built page never falls back unnoticed.
- **Python code questions run, but young.** The in-page runner (the
  Pyodide system, loaded from a network address or a locally served
  copy), the shared session, set-up and provided code, embedded data
  files, the form helpers, and the recording of printed text, tables,
  and pictures into the submission are all built and exercised by a
  browser test. Not yet built: stopping a runaway cell without
  reloading the page, a per-question time or output limit, and the
  exam-room checklist document for serving Pyodide locally.
- **The essay writing view is simplified.** The word count and the
  planning box work; the full-width distraction-free layout the design
  describes is not built.
- **Marking is mouse-and-keyboard, not keyboard-first.** The
  digits-then-Enter flow, and the reusable feedback phrases, are not
  wired yet.
- **"Answer any N" counting cannot yet be overridden.** The workbench
  counts the best N automatically; the marking record already has a
  field for a marker's override, but there is no control for it.
- **The readable copy is produced from the live page.** The design
  prefers a copy generated independently of the page's state; the
  current approach is tested to contain no scripts, but it is the
  weaker construction.
- **Submission zips are read back only in dewmark's own form** (entries
  stored without compression). A zip re-packed by other software is
  reported, not read.
- **Question prose cannot contain lines of three backticks**, because
  the parser treats every such line as a settings block. Code shown in
  prose must use indented blocks instead, as the reference blocks in
  the two sample papers with code do.
- **Saved work from before September 2026 is not offered.** The page
  used to keep one browser slot per exam, shared by its pages
  (`dewmark:<exam code>`); each page now has its own
  (`dewmark:<exam code>:<page>`). Work left in the old slot stays in
  the browser but is no longer offered for restore. No class had sat a
  dewmark paper, so nothing real was stranded.
- **Starting again keeps earlier work aside, but nothing yet shows it.**
  It is stored under `dewmark:<exam code>:<page>:set-aside:<time>`;
  the invigilator's view that lists and recovers it comes with the new
  start screens (step 4 of the plan).
- **Two markers, one folder, is unhandled.** The marking record is a
  single file with no merging; the last save wins.
- **The accessibility baseline is only partly met.** Answer spaces have
  labels and the pages work by keyboard, but no full audit against
  planning/APPEARANCE_AND_READABILITY.md has been run.

## Conventions

Python and JavaScript code carries comments that explain why, not what.
Every check the builder performs has a test in `tests/` that proves it
fires, and a change that adds a check adds its test in the same commit.
The saved-data formats — the exam file, the answers file, the marking
scheme, the marking record — all carry `format_version: 1`; any change
to what they contain must raise the version and keep the old one
readable, because real submissions must stay readable for years. None
of the formats is frozen yet; the roadmap freezes them before any real
sitting.
