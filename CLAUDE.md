# dewmark

An exam file in, an exam page out; submissions in, graded papers and a
marks spreadsheet out. Nothing goes to a server. `README.md` has the full
picture, `planning/PROPOSAL.md` the plan being built, `DECISIONS_LOG.md`
the reasoning. This file is only what you need before touching anything.

## Running things

```bash
pip install -r requirements.txt -r requirements-dev.txt   # first time only
python -m pytest                                           # the builder's tests
python build_exam.py samples/sample-mixed-paper.exam.md --output /tmp/out
python dev/build_site.py                                   # the Pages site, into site/
python -m dewmark check samples/pdp-5n2927/*.exam.md       # the new reader (docs/EXAM_FORMAT.md)
python -m dewmark build FILE -o /tmp/out                    # the new pages: student, practice, answer key, scheme
python -m dewmark lock FILE --sitting "2026-10-20 Group A"  # the names lock, at issue
python -m dewmark scheme FILE -o scheme.json                 # the marker's half as JSON (secret: never in a folder students get)
python -m dewmark package tidy FILE -o package.txt           # the paste route: what to give an assistant
python -m dewmark reply tidy FILE REPLY.txt                # ...and the check of what it returned
python dev/smoke_pages.py                                  # browser rehearsal (Playwright + Chromium)
python -m pytest tests/browser/test_page.py                 # the new page, sat in Chromium
python -m pytest tests/browser/test_checker.py              # the checker page; Python loads from a CDN, so it needs a network
```

`site/` is generated and gitignored. Never edit it.

## Before you write a word a student or teacher will read

Student-facing text lives in `build_exam.py`, `assets/exam-page.js`,
`assets/exam-page.css`, `dewmark/build.py`, `dewmark/render.py`, `assets/page.js`,
`assets/page.css` and the built pages; teacher-facing text in
`workbench/index.html`, `checker/index.html`, `docs/FOR_TEACHERS.md`, the builder's
messages and the paste route's mode names and notices in `dewmark/package.py`.
Follow dewlab's style guide for student text,
<https://github.com/deweydex/dewlab/blob/main/planning/PEDAGOGICAL_STYLE_GUIDE.md#voice>:
plain words, a term defined the first time it is used.

## Where the rest lives

| Doing | Read |
|---|---|
| Anything about the plan, or what to build next | `planning/PROPOSAL.md` §9, then `planning/DECISIONS_2026-09-27.md` |
| The exam file format | `docs/EXAM_FORMAT.md` (adopted; `build_exam.py` still reads the older format in `planning/THE_EXAM_FILE.md` until step 6, and `python -m dewmark build` reads the new one) |
| Changing the builder, the page or the workbench | `docs/DEVELOPMENT.md`, which lists where the drafts fall short |
| Changing the new page or what it saves | `docs/ANSWER_FILE.md`, then `DECISIONS_LOG.md` entry 0.12 |
| Running an exam as a teacher | `docs/FOR_TEACHERS.md` |
| Why something is the way it is | `DECISIONS_LOG.md` |

A change isn't finished until the document describing that behaviour
describes the new one. Where `planning/PROPOSAL.md` and an older
`planning/` document disagree, the proposal wins until the older one is
rewritten.

## Three traps

**Never commit a real exam or a submission.** The repository is public.
Keep real papers under `private/`, which git ignores. Submissions and
marking records are named `dewmark_<exam code>_…`, also ignored. The
four papers in `experiments/pdp-5n2927/` are cleared trial runs, not a
precedent.

**Names are a contract.** An exam's code, its answer names and the
format version are what saved answers and marking records are keyed on.
Once a paper has been sat, renaming any of them strands that work. The
same lesson as dewlab's cell ids. For papers in the new format,
`names.lock.json` beside the file enforces it (`dewmark/lock.py`).

**The start screen must never write.** The page holds a blank state
until the student presses Begin or Continue, and writing it (from a
save, an unload handler, a second window) wipes the saved work the start
screen is offering to restore. `canWrite` in `assets/exam-page.js` and in
`assets/page.js` (the new page) is the one switch every save of the
student's work goes through; the one
deliberate write before Begin is `setAsideStoredWork()`, which copies
earlier work aside when a student starts again. `tests/browser/` fails
if another write gets past, on either page. Each page of an exam keeps its own save slot
(`dewmark:<exam code>:<page>`), and the answer key saves nothing.
