# dewmark working code: audit for the repo split

Subject: `/home/user/dewlab/dewmark` (builder, exam page runtime, workbench, tests, dev rehearsals, samples). All runs happened in a private copy at `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/code/`. Neither repo was modified.

## Headline findings

- **The code is small and self-contained.** It is about 4,300 lines in total. Nothing in dewmark imports from dewlab; the coupling runs the other way (see §7). The unit tests pass (18/18), all 5 samples build, and both browser rehearsals pass once the network is supplied.
- **Several serious runtime bugs are not caught by the rehearsals.** Each was confirmed with a probe:
  1. Reloading or closing the start screen wipes the browser copy of a student's answers (3 answers became 0).
  2. The practice paper and the exam paper share one save slot.
  3. `input()` raises `OSError`.
  4. Output from the sample's own `@button` form is silently dropped. That form is worth 2 marks in the hvit marking scheme.
  5. A runaway loop freezes the whole page.
  6. Every question's heading is attributed to the *previous* question.
  7. The workbench treats the marking-scheme JSON as a student.
- **Python exams cannot yet run offline for teachers.** The Pyodide location can only be changed by injecting `window.DEWMARK_PYTHON_BASE` from a test harness. `openpyxl` always comes from PyPI.
- **The runtime is now behind Josh's newest hand-built PDP pages.** Those pages have CodeMirror, a settings pane, an `input()` shim, a `settrace` deadline for runaway loops, and a timer. dewmark has a bare `<textarea>` where Tab moves focus away instead of indenting.

---

## 1. The builder (`build_exam.py`, 1,344 lines, 60 KB)

### Pipeline

It runs as `build()` at L1285, in six stages:

1. **Parse** (`parse_exam_file`, L111–251). A line-by-line state machine:
   - An opener matches `^```([A-Za-z][\w-]*)\s*$` (L145). Everything up to the next bare fence is YAML parsed by `yaml.safe_load` (L175).
   - Prose lines collect into chunks. `flush_prose()` (L127) attaches each chunk to whichever question, section or preamble is currently open.
   - The state is `current_section`, `current_question`, `last_answer` and `prose_since_answer`. The last two enforce that a marking block sits directly after its answer.
   - L248–249 is a dangling, unfinished comment: "…The flush above".
2. **Check** (`check_exam` L254, `check_answer` L433, `check_marking` L560). This stage:
   - checks required exam keys, the `exam_code`/`version` formats and name rules (`NAME_RE` / `SECTION_NAME_RE`, L55–56);
   - checks that marks add up, per answer, per question and per total after `choose` rules (L301–354, L427–430);
   - checks that each `choose` rule is mentioned in the instructions, by digit or number-word (L343–350);
   - requires `python:` when there are code questions (L358–367), and checks the `calculator` value, that data files exist, reference blocks, and picture alt text and existence (L396–405);
   - checks that `$…$` typesets (L409–425);
   - does per-type shape checks;
   - parses marking into one of three methods: `points-with-a-limit` (with `POINT_RE`, L61), `a-criteria-grid` (with `BAND_RE`, L63), or `marks-out-of-a-total`.
   - In all, 66 `problems.append` sites. Errors are collected and reported together (`BuildError`, L100).
3. **Render.** `render_paper` (L955) calls `render_markdown` (L689) and `render_answer_space` (L734, one branch per type). `render_model_block` (L882) is used by the answer key only.
   - Mathematics is stashed before Markdown and converted to MathML with `latex2mathml` (`math_html`, L647).
   - Images become base64 data URIs (`embed_image`, L678).
4. **Assemble** (`build_page`, L1048).
   - It inlines the **entire** `exam-page.css` and `exam-page.js` into every variant.
   - The calculator panel HTML is generated here in Python (L1070–1103).
   - `page_model()` (L999) is embedded as `<script type="application/json" id="dewmark-exam-model">`. Data files go into it as base64 (L1059–1065).
5. **Leak check** (`leak_fragments` L1187, `check_for_leaks` L1225). It runs over the student and practice pages.
   - It strips `<style>` and **all `<script>` content** before searching (L1228). The `page_model` docstring (L1000–1003) claims the JSON block is covered; it is not.
6. **Write** (L1303–1318).
   - `<code>.student.html`, `<code>.practice.html`, `<code>.answer-key.html`
   - `dewmark_<code>_marking_scheme.json`, produced by `marking_scheme()` (L1252), which carries the full answer settings plus the parsed marking.

The output is deterministic, and a test checks this. There is no `--preview` flag, and no way to choose which variant to build.

### Grammar actually parsed vs `planning/THE_EXAM_FILE.md`

| Spec says | Code does |
|---|---|
| Six block kinds | Same six (`BLOCK_KINDS`, L38) |
| "ordinary text belongs to whatever section or question is open where it appears" | Implemented literally. But the spec's own example puts `### Question A1` *before* its `question` block, so every heading lands in the previous question's `<div class="dm-question">`. Verified on the mixed sample: `scheme["sections"][0]["questions"][0]["prose"]` ends with "### Question A2 — The parts of an argument". The workbench displays that text as a1's wording, and the "wording" column of `_what_the_columns_mean.csv` is wrong for every question. |
| Builder "told which build to produce" | It always builds all three variants |
| `hint` survives into the practice build | Only `short-/long-written-answer` render `hint`, as a placeholder (L785). Both sample hints are on `numeric-answer` and are dropped. **Student and practice pages differ only in the banner for all five samples** (6-line diff each). |
| Refuse "an answer space that needs a marking scheme has none" | Not checked. A missing marking block silently defaults to `marks-out-of-a-total` (L564). |
| "includes only what the exam's question types need" | The full 37 KB of JS and 13 KB of CSS are always inlined |
| Mathematics anywhere | Typeset only in prose, instructions, reference text, `prompt`, and `shape.prompt` (`every_math_text` L69, `esc_with_math` L665). MC options, table cells, box labels, feature labels and `model_answer` go through plain `esc()`. `$x^2$` in an MC option renders with raw dollars **and passes the checks** (probe). |
| — | Unknown keys are silently accepted (a `modle_answer` typo built fine). |
| — | YAML 1.1 coercion (probe): `options: [Yes, No]` renders **"True"/"False"**, and `expected: 12:30` becomes **750**. |
| — | A fenced code block in prose is a build error, not a code block (known gap). |
| — | `BAND_RE` accepts integers only; `POINT_RE` accepts `.5`. |

---

## 2. The exam page runtime (`assets/exam-page.js`, 1,058 lines; `exam-page.css`, 290 lines)

**Start.** There *is* a start screen (`#dm-start`, `build_exam.py` L1144–1153), shown in `shots/01`.
- It shows the band (kind, title, time allowed, total), the instructions, one text input per `student_details` label, a fixed save note, Begin, and "Load a saved answer file…".
- There is no institution, module or logo field. Branding is hard-coded navy/orange CSS.
- There is no loading or preflight step. Python starts only *after* Begin (`enterExam` → `startPython`, L297).
- `begin()` (L259) uses `alert()` for missing details.
- The answer key also demands student details and saves under the same key (`shots/14`).

**Python** (L544–837).
- Pyodide **v0.27.4** from `https://cdn.jsdelivr.net/pyodide/v0.27.4/full/`, unless `window.DEWMARK_PYTHON_BASE` is set (L714). Nothing in the exam file or build can set it.
- It runs **on the main thread**: there is no Worker and no interrupt buffer.
- Loading goes `loadPackage(["micropip", "sqlite3"?])`, then `micropip.install(rest)` (L750–758).
- Data files are written to `/exam`, and the process changes into that directory. A `dewmark_tools` module is written to `/` (L599–702). It provides `show`, `show_table`, `text_input`, `number_input`, `dropdown` and a `button` decorator. `matplotlib` uses the Agg backend.
- There is one shared session, with a global `pythonBusy` lock.
- Behaviours confirmed by probe:
  - `input()` fails with `OSError: [Errno 29] I/O error`, because `setStdin` is never called.
  - `while True: pass` left the page unable to run any JavaScript for 8 s or more. The code *had* been saved to localStorage, which a second tab confirmed. There is no timeout, output cap or stop button.
  - After clicking the `@button` "Register" widget, the output area was empty and `outputs: []`. The cause is that `__dewmarkEmit` only records or renders while `currentRecords` is set (L728–743), and widget handlers run outside `runPython`. The widgets themselves are inserted as raw HTML, not records, so they are never in the submission. The hvit marking scheme awards 2 marks for "a confirmation message appears after registering". Label and option strings are not HTML-escaped (L657–679).
  - `setup_code` output and errors go to `"dm-nowhere"` (L803). A failing setup is invisible while the pill says "Python ready". Provided-code output is not recorded.
  - stderr, including warnings, becomes red "error" records (L747).
  - Offline, the pill reads "Python failed — click to retry" within about 1 s. All 14 Run buttons stay disabled, and there is no explanation for the student (`shots/16`).

**Editor.** A plain `<textarea class="dm-code">` (build L753). No highlighting, no line numbers, no bracket help, and no Tab handling: the only `keydown` handler is the calculator's (L1033), so Tab leaves the box.

**Maths.** Converted to MathML at build time (0 fallbacks across the samples). No typesetting at runtime.

**Calculator.** A hand-written tokenizer and recursive-descent parser (L914–1036) with no `eval`. The smoke test covers it.

**Saving.**
- `saveEverywhere()` (L192) runs on every `input`/`change`:
  - `localStorage["dewmark:"+exam_code]` immediately;
  - a File System Access handle from `showSaveFilePicker` at Begin, debounced 800 ms (L204). Chromium only.
- "Save a copy" downloads JSON. There is no IndexedDB.
- **Bug A (verified).** `beforeunload` (L892–896) writes `gatherState()` even when the exam was never entered. On the start screen, `state` is blank, so a reload or close from the "Saved work was found" screen replaces the saved answers with an empty set. Pressing Begin instead of "Continue" has the same effect (L259–298, then `saveEverywhere`).
- **Bug B (verified).** The storage key and the `BroadcastChannel` are keyed by `exam_code` only (L6, L1040), so the practice page offered the student page's saved work. The "second window will not save" guard (L1040–1058) only disables buttons; that window's `beforeunload` still writes.
- If file saving fails, it just says "File saving is off" (L211–212). There is no re-pick, and browsers without File System Access get no reminder.

**Finish and submission.**
- `finishReport()` (L390) lists empty spaces by *internal name*. It counts both unchosen alternatives in a `choose` section, so the mixed paper said "8 answer spaces are empty, worth **64** marks" on a **50**-mark paper (`shots/05`).
- The finish report has no stale-code item, no links, and no exam-specific hand-in text (hard-coded L421–424).
- `downloadSubmission` (L519) zips `answers.json` and `your-exam.html` with a hand-rolled STORED zip writer (`makeZip`, L467–517). DOS date and time are 0, so `unzip -l` shows "1980-00-00".
- The name is `dewmark_<code>_<number>_<full-name-slug>.zip`. The spec asks for surname first.
- It looks up the literal keys `"student number"` and `"full name"` (L227–228). Different `student_details` labels degrade to `student`.
- `your-exam.html` is a DOM clone with scripts removed (L427–465). The comment that "cloned controls lose checked state" is wrong per the HTML spec, but harmless.
- `answers.json` holds `format_version`, code, version, student, `started_at`, `saved_at`, `finished_at` and `answers{name: typed value}`. Python answers add `{code, outputs[], last_run, run_matches_code}`. There is no per-section attempt list and no save/run timeline, both of which `THE_SUBMISSION.md` promises.

**Layout.**
- There is one `@media print` block only: no dark mode and no responsive rules. At 420 px, `scrollWidth` is 871 (`shots/09`).
- There is no collapsible panel, no timer, no font or spacing settings, and no essay writing view.

---

## 3. The workbench (`workbench/index.html`, 901 lines: about 97 CSS, about 775 JS)

**Import.**
- The teacher loads the scheme JSON first (L155–173); the check is only `format_version === 1 && sections`.
- "Open submissions…" uses `showDirectoryPicker({mode:"readwrite"})` and iterates **every file** (L247–258). Otherwise it falls back to multi-select of `.zip,.json`.
- `readZipStoredEntries` (L175–197) reads STORED entries only. A deflated zip is reported and skipped (verified).
- Students are keyed by `student["student number"]`, falling back to the file name (L219).
- Duplicates keep the newer `saved_at` and report a problem (L220–232). `sourceFile` is then overwritten with the *newer arrival's* name even when the older file was kept (L233).
- The version mismatch and "no finish step" are flagged (L234–242).
- **Bug G (verified).** Selecting the folder's files including `dewmark_<code>_marking_scheme.json` produced a third student row, "(no name) | dewmark_sample-mixed-2027_marking_scheme.json". In directory mode, `persistRecord()` writes `dewmark_<code>_marking_record.json` *into the same folder* (L279–289), so the next open will ingest the record the same way. That part is from reading the code.

**Marking.**
- There are three views: the class list (L387), per paper (`openPaper`, L671) and by question (L749–789).
- Each answer space gets a number input (clamped *in the record* but not on screen: typing 99 into a 2-mark box displays 99 and stores 2, verified), plus the following:
  - point checkboxes that sum to the limit (L597–619);
  - a number box per criterion, with the bands shown as text (L620–656);
  - per-answer feedback and a closing comment.
- "Answer any N" takes the best N (L357–365). `counted_override` is read but has no UI.
- Question prose is shown as raw Markdown, with `###` and `$…$` visible (`shots/22`).
- The by-question view is sorted by student number, not anonymised.
- `#subs-pill` is never updated.
- The record autosaves only in directory mode (L311–314). Otherwise the teacher has to press Save, which downloads.
- Loading a record does not check `exam_code`.

**Export.**
- "Export marks…" downloads two CSVs: `<code>_marks.csv`, with per-question totals, section totals, total and status; and `<code>_what_the_columns_mean.csv` (L804–846). There is no xlsx.
- "Graded paper…" is per student via `window.open` (L848–898). It is plain text with no question wording, pictures, MathML or run images (`shots/24`), and says "use Print to save as PDF". There is no batch export.
- Rendering of Python output is duplicated from the exam page.

---

## 4. What loads from the network (what breaks offline)

URLs referenced by the built pages and the workbench: only `cdn.jsdelivr.net/pyodide/v0.27.4/full/`, plus the MathML namespace string.
- **Written exams** (mixed, maths, biology, essay) and the workbench need no network. Fonts are system fonts, and pictures and maths are inlined.
- **Python exams** need the network. A full hvit run fetched **27 requests, 78.8 MB** through my caching mirror:

| Group | What it fetched |
|---|---|
| Pyodide core | `pyodide.js`, `pyodide.asm.js` (1.25 MB), `pyodide.asm.wasm` (10.1 MB), `python_stdlib.zip` (2.4 MB), lock file |
| Packages from the Pyodide CDN | micropip, packaging, sqlite3, **pandas 23.8 MB**, **numpy 12.5 MB**, **matplotlib 16.7 MB**, fonttools 4.3 MB, pillow 3.0 MB, and others |
| From **pypi.org / files.pythonhosted.org** | **openpyxl and et_xmlfile**. They are not in the 0.27.4 lock, so even a local Pyodide mirror still needs PyPI. |

Python reached "ready" about 15 s after Begin even when served from the local cache.

For comparison, the four uploaded PDP pages (technical markers only; I did not examine content) load:
- Pyodide 0.27.4 from jsDelivr;
- CodeMirror 5.65.16 and addons from cdnjs;
- Google Fonts (Atkinson Hyperlegible, Lexend) and OpenDyslexic from jsDelivr.

They have a name screen, a settings pane (font, theme, spacing, width, code font and theme, ruler, jedi completion, timer, reduce-motion), `builtins.input` replaced with a prompt-based shim, and a `sys.settrace` deadline. They are ahead of dewmark on every runtime axis, but depend on more CDNs.

---

## 5. Test results and build outputs

- `pytest tests -q`: **18 passed in 0.23 s** (Python 3.11, Markdown 3.11, PyYAML 6.0.3, latex2mathml 3.81.1).
- **Builds.** Every sample builds in under 0.25 s and produces 4 files:

| Sample | Output folder | student / practice / key / scheme |
|---|---|---|
| hvit-database-practical (14 × python-code) | `out/hvit-database-practical/` | 120 KB / 120 KB / 128 KB / 17 KB |
| maths-for-it-5n18396 (70 answers, `choose`, calculator, 11 refs) | `out/maths-for-it-5n18396/` | 117 / 117 / 133 / 53 KB |
| sample-biology-paper (all 8 written types) | `out/sample-biology-paper/` | 69 / 69 / 74 / 16 KB |
| sample-essay-paper (4 essays, criteria grids) | `out/sample-essay-paper/` | 62 / 62 / 68 / 18 KB |
| sample-mixed-paper | `out/sample-mixed-paper/` | 69 / 69 / 73 / 15 KB |

All paths are under `…/scratchpad/code/`.

- **`dev/smoke_pages.py`: passes** (calculator, MathML, sitting, submission zip, one reload and restore, all three marking methods, CSV).
  - It needed Playwright **1.56.0** to match `/opt/pw-browsers/chromium-1194`, and `DEWMARK_CHROMIUM=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`.
  - Playwright 1.63 and full `chrome-linux/chrome` both died with SIGTRAP, and the script's `find_chromium()` (L44–52) picks the full chrome.
- **`dev/smoke_python_page.py` without help: failed.** Chromium got `ERR_CERT_AUTHORITY_INVALID` through the sandbox proxy. The script then waited the full 240 s, because it polls for "Python ready" and never notices "Python failed".
  - I did not use its `DEWMARK_INSECURE_CERTS` escape hatch. Instead I added a scratch-only `page.route` mirror (`dev/netmirror.py`, `dev/smoke_python_routed.py` in the copy) that fetches through Python with normal TLS.
  - **With the mirror the rehearsal passes in 41 s**: sqlite, pandas table, matplotlib image, xlsx read, stale-output note, submission records, and workbench display.
- **Probe scripts**, in the copy's `dev/`: `explore.py`, `explore2.py`, `explore3.py`, `explore_wb.py`. Logs are in `scratchpad/code/*.log`.
- **Test coverage.** 66 check sites, about 12 distinct messages under test. `docs/DEVELOPMENT.md`'s "every check … has a test" is not true. There are no JS or workbench unit tests, and the browser rehearsals are not in CI (`dewlab/.github/workflows/tests.yml` L98–124).

**Screenshots** in `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/code/shots/`:
- Exam pages: `01-mixed-start-screen.png`, `02-mixed-paper-top.png`, `03-mixed-paper-essay.png`, `04-mixed-label-diagram.png`, `05-mixed-finish-screen.png`, `06-mixed-restore-offer.png`, `07-maths-calculator-reference.png`, `08-maths-describe-a-sketch.png`, `09-maths-at-phone-width.png`
- Python and answer key: `10-python-start-screen.png`, `11-python-loading.png`, `12-python-widget-form.png`, `13-python-table-and-chart.png`, `14-answer-key-start-screen.png`, `15-answer-key-model-block.png`, `16-python-offline-failure.png`
- Workbench: `20-workbench-empty.png`, `21-workbench-class-list.png`, `22-workbench-paper-view.png`, `23-workbench-criteria-grid.png`, `24-workbench-graded-paper.png`, `25-workbench-by-question.png`

---

## 6. Gaps

**Already listed in `docs/DEVELOPMENT.md`:**
- MathML needs 2023+ browsers.
- Python: no stopping a runaway cell, no time or output limit, no room checklist.
- Simplified essay view.
- No keyboard-first marking or feedback phrases.
- No "answer any N" override UI.
- The readable copy is taken from the live DOM.
- The zip reader handles STORED entries only.
- No triple backticks in prose.
- No merging for two markers.
- Partial accessibility.

**Additional, verified by probe:**
- Bugs A (reload wipes saves) and B (shared save slot).
- `input()` broken.
- Widget output dropped (breaks hvit task 3's marking scheme).
- Page freeze on a runaway loop.
- Headings attributed to the wrong question.
- Scheme JSON ingested as a student.
- Mark box shows one value and stores another.
- YAML coercion.
- Untypeset and unchecked `$` outside prose.
- Practice identical to student.
- Unknown keys accepted.
- Misleading finish-screen totals.
- No horizontal fit at phone width.

**Additional, from reading the code:**
- No teacher-facing Pyodide location.
- PyPI dependency for non-lock packages.
- Silent `setup_code` failures.
- No Tab in the code editor.
- Keys hard-coded to `"full name"`/`"student number"`, in the page (L227–228) and the workbench (L219, L403).
- Marking record written into the submissions folder, then re-ingested.
- File System Access (save file, read/write folder) is Chromium-only.
- No institution or module branding.
- No preflight or loading screen before the exam.
- Answer key needs student details and shares storage.
- Graded paper is not a real export.
- Spec items missing: `--preview`, the save timeline, "Restored N answers at…", the freeze remedy in the side panel, re-picking a file after a failure, choosing between duplicate files, and links on the finish screen.

---

## 7. Coupling to dewlab

- **dewmark → dewlab: none in code.** It has no imports and no shared assets. All `../` links resolve inside `dewmark/`. What remains is textual:
  - the CSS comment "repeat the dewlab palette" (`exam-page.css` L1–2) and the `build_exam.py` docstring (L15);
  - `dewmark/…` paths in the error text (`build_exam.py` L415–416), the script docstrings (`smoke_*.py` L14) and `docs/DEVELOPMENT.md`;
  - `planning/THE_EXAM_BUILDER.md` §4 ("part of the dewlab repository");
  - `planning/THE_EXAM_PAGE.md` §6, which relies on "the small helper program that dewlab already provides for its offline bundles" to serve Pyodide. This is a real functional dependency that has not been built.
- **dewlab → dewmark:**
  - `build.py` L128 (`DEWMARK_WORKBENCH = ROOT/"dewmark"/"workbench"`) and L7644–7646 copy the workbench into `site/dewmark/`, so it is published at dewlab's `/dewmark/`. `tests/build/test_site.py` L636–684 covers that step.
  - The `dewmark` CI job is at `.github/workflows/tests.yml` L98–124.
  - `dev/normalise_svg.py` L203–204 excludes `dewmark/`.
  - Textual references: `README.md` L111, `docs/WRITING_TUTORIALS.md` L801, and `DECISIONS_LOG.md` 7.179, which compares against dewmark's grammar.
- **History.** 8 commits in dewlab touch `dewmark/` (from `2f23c03d` to `87e465f6`). `/home/user/dewmark` holds one "Initial commit" (remote `github.com/deweydex/dewmark`).

---

## 8. Code quality

- **Size.** Builder 1,344 lines; runtime 1,058 JS + 290 CSS; workbench 901; tests 323; rehearsals 387. It is readable, with good why-comments and good error messages. The comment and doc drift is small but real: L248–249, the `page_model` docstring, the clone comment, and the DEVELOPMENT.md test claim.
- **Adding a question type touches about 8 places in 3 files and 2 languages:**
  - Python: `check_answer`, `render_answer_space`, `render_model_block`, `leak_fragments`;
  - page JS: `collectAnswer`, `applyAnswer`;
  - workbench JS: `renderStudentAnswer`, `renderModel`.
  There is no shared type registry or schema.
- **Duplication.**
  - The palette is written out twice (`exam-page.css` L4–19 and `workbench` L9–16).
  - Python output rendering is written twice (`exam-page.js` L555–597 and `workbench` L489–516).
  - Model-answer rendering is written in both Python and JS.
  - The CSV and graded-paper paths each rebuild answer text.
- **Fragile spots.**
  - HTML is built by string concatenation in Python f-strings and in the `dewmark_tools` Python-to-HTML helpers.
  - The leak check is a regex over the whole page.
  - YAML 1.1 is used as the authoring layer.
  - Global mutable `state`; the `window.__dewmark*` bridge globals.
  - A hand-rolled zip writer and reader.
  - Python runs on the main thread.
  - `alert`/`confirm` UX.
  - A single-file page that inlines the whole runtime plus base64 data. Base64 inflates data by 33%, and the data is embedded in all three variants.

---

## What this means for dewmark

1. **The code can be lifted cleanly.** Move `build_exam.py`, `assets/`, `workbench/`, `samples/`, `tests/`, `dev/`, `docs/`, `planning/` and `experiments/` as they are, using `git filter-repo --subdirectory-filter dewmark` or `git subtree split`. That keeps the 8 commits of history.
   - Then, in dewlab: delete the CI job, remove or repoint the `build.py` L128/L7644 copy step and its test, drop the `normalise_svg` exclusion, and update README L111.
   - Decide where the workbench is hosted once dewlab stops publishing `/dewmark/`. GitHub Pages on the dewmark repo is the natural choice.
   - Rewrite the `dewmark/…` paths and the "part of dewlab" text in the same commit.
2. **Fix the data-loss bugs before any redesign ships to a room.** That means Bug A (guard `beforeunload` and Begin when a stored state exists) and Bug B (put the variant in the storage and channel key, and make the answer key non-saving). Add probes for each to the rehearsals, and put the rehearsals in CI with the headless shell.
3. **The runtime needs a rethink rather than patches.** The PDP pages already contain the answers to most of its gaps: a settings and name screen, CodeMirror, an `input()` shim, a `settrace` deadline, and a timer. The obvious next shape has four parts:
   - a **preflight/loading screen** with name and details, branding (institution, module, logo from the `exam` block) and asset checks, before Begin;
   - Python in a **Worker**, with an interrupt or deadline;
   - a vendored, bundled editor;
   - a first-class `pyodide_base` / "local runtime" setting in the exam file, with a room kit that mirrors Pyodide **and** any PyPI wheels (openpyxl today).
4. **The grammar needs a pass before formats freeze.** The pass should:
   - attach headings to the *following* block (or make the question block carry its title);
   - reject unknown keys;
   - force strings in option and expected lists, or move to a YAML 1.2 / strict loader;
   - typeset and check `$…$` in every student-visible field;
   - render `hint` for every type;
   - allow fenced code in prose;
   - make student detail keys configurable end to end.
   A per-type registry (a schema plus one renderer, collector and marker-view per type) would make maths and biology types cheap to add.
5. **The workbench needs:**
   - ingestion that filters to submission files, and a record stored outside the submissions folder;
   - Deflate zip support (via `DecompressionStream`);
   - real exports: batch graded papers with question text, maths and images, plus xlsx;
   - keyboard marking;
   - a hook point for the local-LLM idea: a "suggest mark/feedback" call per answer, reading scheme and answer, never deciding.