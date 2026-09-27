# Parked: 2026-09-27, mid-research

This branch holds work in progress, parked so a fresh session can pick it
up. Delete this file, `planning/research-2026-09-27/shots/` and
`planning/research-2026-09-27/probes/` before the branch merges; they are
working material, not part of the project.

## What Josh asked for

Bring dewmark out of `deweydex/dewlab` (where it lives as the folder
`dewmark/`) into this repository, and plan its next shape step by step:

- which kinds of exam dewmark should support: programming now, and also
  maths and biology, and what each needs from the page;
- the flow a student goes through, including a first screen with the
  student's name, a settings screen, and a loading screen while assets
  such as Pyodide arrive;
- better exam branding: institution, college, module, paper;
- what to do if an offline LLM becomes available on a local box, and
  which API dewmark should call so that teachers have an easier time;
- all of it beautiful, clear and easy for teachers to use.

## Decisions Josh has made

- **The four PDP 5N2927 papers may be committed and used on the site.**
  They are trial runs and will not be sat as exams, the 2027 paper
  included. They are in `experiments/pdp-5n2927/`. Some of the research
  reports warn that the 2027 paper must stay private; those warnings are
  out of date.

## Where the work stands

1. **Understand (in progress).** Seven readers ran as one workflow. Four
   finished, and their reports are in `planning/research-2026-09-27/`:
   - `design-docs.md`: dewmark's written design, with a critique
   - `code.md`: the builder, exam page and workbench, audited and run
     (18/18 tests pass, all five samples build, seven runtime bugs found)
   - `pdp-pages.md`: a teardown of the four PDP pages and a comparison
     with dewmark's format
   - `dewlab-runtime.md`: what dewlab built after PR #181 that dewmark
     should reuse, including an offline Python engine verified in
     Chromium (`probes/engine/`)

   Three did not finish: **extraction** (the mechanics of the move),
   **local-llm** (serving options, the API contract, EU AI Act) and
   **exam-types** (maths, biology and programming question types, QTI,
   QQI). Their prompts are in `planning/research-2026-09-27/understand-workflow.js`.
   Re-run only those three.
2. **Design (not started).** Once all seven reports are in, run a design
   round covering: the repository move; one exam format reconciling
   dewmark's grammar with the PDP format and dewlab's `question` fence;
   the start flow (identity, settings, loading, Begin); branding keys; a
   type registry for maths and biology; the local-LLM contract. Then take
   the open decisions to Josh.
3. **Move (not started).** Extract `dewmark/` from dewlab with its history
   (`git filter-repo --subdirectory-filter dewmark`, then merge here with
   `--allow-unrelated-histories`). Add CI and Pages here. Then open a
   separate dewlab PR that removes the folder, the `dewmark` CI job, the
   `build.py` step that copies the workbench to `site/dewmark/` and its
   test, and the `dev/normalise_svg.py` exclusion, and that updates
   dewlab's README.

## Findings so far

- dewmark's code is self-contained: nothing in it imports from dewlab.
  The move is clean. The coupling runs the other way, through dewlab's
  CI job, `build.py` and one test.
- The PDP pages give a student a better experience than dewmark's drafts:
  CodeMirror, a settings drawer, `input()`, a per-run time limit, a
  reference sheet, a timer, and a name screen while Python loads. But
  they have no teacher side: no marking scheme, no model answers, no
  workbench. They also fail completely with no network, and have
  verified bugs in autosave and the time limit.
- dewmark's drafts have data-loss bugs that must be fixed before any
  sitting: reloading the start screen wipes saved answers, and the
  practice paper and the exam paper share one save slot.
- An offline Python engine with `input()` and a Stop button works from
  `file://` (verified in Chromium 141 on Pyodide 0.28.3): a blob-URL
  classic Worker, `run_sync` for `input()`, and `terminate()` to stop.
  Firefox and Safari are still untested.
- Both reports recommend designing the start as a flow (identity,
  settings, asset loading, Begin) and adding a presentation block to
  the exam file for branding.

Nothing was changed in dewlab. The local dewlab clone was unshallowed,
which is needed for the history-preserving move.
