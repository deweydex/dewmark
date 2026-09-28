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
python dev/smoke_pages.py                                  # browser rehearsal (Playwright + Chromium)
```

`site/` is generated and gitignored. Never edit it.

## Before you write a word a student or teacher will read

Student-facing text lives in `build_exam.py`, `assets/exam-page.js`,
`assets/exam-page.css` and the built pages; teacher-facing text in
`workbench/index.html`, `docs/FOR_TEACHERS.md` and the builder's messages.
Follow dewlab's style guide for student text,
<https://github.com/deweydex/dewlab/blob/main/planning/PEDAGOGICAL_STYLE_GUIDE.md#voice>:
plain words, a term defined the first time it is used.

## Where the rest lives

| Doing | Read |
|---|---|
| Anything about the plan, or what to build next | `planning/PROPOSAL.md` §9, then `planning/DECISIONS_2026-09-27.md` |
| The exam file format | `docs/EXAM_FORMAT.md` (adopted; the builder still reads the older format in `planning/THE_EXAM_FILE.md` until step 3) |
| Changing the builder, the page or the workbench | `docs/DEVELOPMENT.md`, which lists where the drafts fall short |
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
same lesson as dewlab's cell ids.

**Practice and exam builds share one save slot today.** Until step 2 of
the plan fixes it, a practice attempt can be offered as a restore in the
real paper when both open in the same browser, and reloading the start
screen wipes saved answers. Do not host practice and exam builds of one
paper side by side, and do not put a class in front of a dewmark paper,
before step 2 lands.
