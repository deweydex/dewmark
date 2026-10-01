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

## The new reader

`dewmark/` is the new builder, growing beside `build_exam.py` one step of
the plan at a time. Today it holds the reader for the exam format in
`docs/EXAM_FORMAT.md` (`dewmark/reader.py`, with `settings.py`,
`numbers.py`, `kinds.py` and `scheme.py`), the names lock that holds an
issued paper's names still (`dewmark/lock.py`), the marker's half as JSON (`dewmark/scheme_json.py`) and the two layers
that keep it off a student page (`dewmark/secrecy.py`), the paste route
(`dewmark/package.py` builds what a teacher gives an assistant,
`dewmark/reply.py` checks what comes back, and `dewmark/data/` holds the
cheat sheet and the specimen paper it sends), and the converter for the
hand-built PDP pages (`dewmark/convert_pdp.py`). It uses only Python's
standard library, so the studio can run it unchanged in the browser.

```sh
python -m dewmark check samples/pdp-5n2927/*.exam.md
python -m dewmark lock FILE --sitting "2026-10-20 Group A"
python -m dewmark scheme FILE -o scheme.json
python -m dewmark package tidy FILE -o package.txt
python -m dewmark reply tidy FILE REPLY.txt -o reworded.exam.md
python -m dewmark.convert_pdp samples/pdp-5n2927 experiments/pdp-5n2927/*.html
```

`tests/test_reader.py` holds the format's hostile cases as tests, reads
the specimen paper in `tests/fixtures/`, and fails if the converted PDP
papers in `samples/pdp-5n2927/` drift from what the converter writes.
The checker page, `checker/index.html`, is a template. `python
dev/build_site.py` writes the real page to `site/checker/`, with every file
of the `dewmark` package the page calls (not `__main__.py` or the PDP
converter) in a data block, so the page checks with the code the command
line runs. The page loads Pyodide from jsDelivr, at the version the exam page
pins, and calls `dewmark/web.py`, which takes text and returns JSON. Opened
without being built, it says so. `tests/browser/test_checker.py` runs the
page in Chromium and compares what the browser and the command line say over
the specimen and the four PDP papers, string for string; it needs a network
for Python, and skips without one unless `DEWMARK_REQUIRE_BROWSER` is set, as
it is in CI. `tests/test_web.py` runs the embedded sources in a bare
interpreter (`python -S -I`, an empty folder) to prove they need nothing else.

`tests/test_secrecy.py` tries the search and the mutation test on small
renderers written there: one that builds a page as it should be built and
nine that each let the scheme through a different way (a comment, a data
block, escaped, in capitals, by its start, a class on the right option, a
short key, base64). It shows which layer catches which: the search cannot see
a key too short to look for, one implied by a class, or one encoded, and the
mutation test finds them. When step 4's renderer exists, add
`mutation_test(sample, build_student_page)` and `find_leaks` over every sample
to the tests, and stop the build on a leak.

`tests/test_lock.py` issues a small paper, changes it the ways a teacher
might after a sitting, and checks what the lock refuses and allows.

`tests/test_paste.py` makes replies that go wrong one way at a time (a
setting, a number, a line of code, a scheme slipped in) and checks each
is refused; it also has a fake assistant reword the four real PDP papers
and checks the rewording is accepted, all rejected gives the papers back
byte for byte, and one changed digit is refused. It also fails if the
cheat sheet in `dewmark/data/` drifts from §8 of `docs/EXAM_FORMAT.md`.

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
