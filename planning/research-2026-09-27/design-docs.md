# dewmark's written design: what it says, what it leaves out, and where it contradicts itself

**What I read:** `README.md`, `experiments/README.md`, all 11 files in `planning/` and both files in `docs/`, under `/home/user/dewlab/dewmark/`. I checked the claims that matter most against `build_exam.py`, `assets/exam-page.js`, `workbench/index.html`, and dewlab's `DECISIONS_LOG.md`. I looked only at the element structure of the non-live 5N2927 Sample exam and Practice Exam 1. I did not open the content of the 2027 exam. Nothing was written to either repo.

---

## 1. Core model and the five parts

The core model is that a teacher writes one checked file and everything else is built from it. There is no server anywhere. The exam is a file, each submission is a file, and the marks are a file, all kept in folders on one machine (`README.md:12-14`). The design is built around a set of hard rules:

- **Permanent names.** Every section, question and answer space has a name that never changes after a sitting.
- **Everything embedded.** Pictures, data files and typeset maths are all built into the page.
- **Nothing written twice.** Navigation, totals, file lists and reference material are generated from the exam file.
- **A person awards every mark.**

The five parts (`README.md:30-67`):

1. **The exam file.** One Markdown file with typed settings blocks. It holds the questions, marks, marking scheme, model answers, and the names of pictures and data files. It can be written by hand or produced by an LLM "translation assistant" from a Word or PDF exam.
2. **The catalogue of question types and marking methods.** One shared list; any exam can use any mix. The README calls this the most important document.
3. **The exam builder.** `build_exam.py` checks the file strictly. It then writes four outputs: the student paper, a practice paper, an answer key, and a marking-scheme JSON file.
4. **The exam page.** A single self-contained HTML file. It saves after every change to browser storage and to a file the student picks. When the student finishes, it produces a submission zip.
5. **The marking workbench.** A local HTML page that reads a folder of submissions and the scheme. It supports marking one paper at a time or one question across all papers. It exports a graded paper per student and a marks CSV with a companion CSV explaining the columns.

Two further documents cut across all five parts: `APPEARANCE_AND_READABILITY.md` and `OPEN_QUESTIONS.md`. `ROADMAP.md` sets the build order.

## 2. The exam file grammar

**Carrier.** The file is Markdown. `$...$` is maths, typeset when the exam is built. Settings blocks are fenced with three backticks plus a kind, and hold one `key: value` per line (`THE_EXAM_FILE.md:22-34`). In practice the blocks are YAML, parsed with PyYAML (`requirements.txt`), but the spec never uses the word YAML.

**Six block kinds** (`THE_EXAM_FILE.md:36-45`):

| Kind | What it does |
|---|---|
| `exam` | One per file, at the top |
| `section` | Starts a section |
| `question` | Starts a question |
| `answer` | Creates an answer space in the current question |
| `marking` | Attaches a scheme to the answer space directly above it |
| `reference` | A titled side-panel item with a `title` and a `text` |

**How blocks relate to text** (`:47-54`). Structure comes only from blocks, and headings are cosmetic. A section runs until the next section. A question runs until the next question or section. Prose belongs to whichever section or question is open where it appears.

**Keys in the `exam` block** (`:150-198`):

- `title`
- `exam_code`: permanent, and part of every output file name.
- `version`: `YYYY.MM.DD.n`. The workbench warns when a submission and the scheme come from different versions.
- `total_marks`: the builder recomputes the total after applying "any N" rules and refuses a mismatch.
- `time_allowed`: shown on the opening screen, not enforced.
- `student_details`: a list such as `[full name, student number]`.
- `calculator: scientific`
- `instructions`: the builder checks that each section's "any N" rule is mentioned here.
- `data_files`: a list of `path`, optional `as` (the name students see), and `description`. All are embedded when the exam is built; the page never fetches anything.
- Python only: `python` (the package list, required whenever the exam has a Python question) and `setup_code`.

The code requires `title, exam_code, version, total_marks, student_details, instructions` (`build_exam.py:265-267`).

**`section`:** `name`, plus optional `choose: N` for "answer any N" (`:202-213`).

**`question`:** `name`, `marks`, optional `topic` (used in the spreadsheet), and optional `provided_code` (read-only code that runs automatically). The marks of the answer spaces must add up to the question's marks (`:215-218`).

**`answer`:** `name`, `type`, `marks`, plus keys specific to the type (see §3). Other keys:

- `hint`: kept in the practice build, stripped from the exam build (`:243-248`).
- `model_answer` or `model_answer_code`.
- `expected` or `correct`.
- `draft`: not in the grammar doc at all. It appears only in `TRANSLATING_AN_EXISTING_EXAM.md:54-62`, and the code honours it at `build_exam.py:889`.
- `image_description`: required by the code but not named in the spec, which only says "a written description".

**Names** (`:220-230`) are lower-case identifiers such as `a1` or `a1.roots`, unique across the whole exam, and never renamed after a sitting.

**Leak protection** (`:232-241`). The student paper has all expected, correct, model and marking material stripped out. The builder then searches its own output for every fragment and stops if it finds one.

**Marking blocks.** The method is inferred from which keys are present: `points` means points-with-a-limit, `criteria` means a criteria grid, anything else means marks out of a total (`build_exam.py:570-640`). The spec never states this rule. Points and bands are small text formats inside YAML strings: `"2 marks - text"` and `"16 to 20 - text"` (`POINT_RE` and `BAND_RE` at `build_exam.py:61-63`).

## 3. Question types and marking methods

**Marking methods** (`QUESTION_TYPES_AND_MARKING.md:74-151`). Every answer space uses exactly one:

| Method | What the teacher writes | How the workbench presents it |
|---|---|---|
| Marks out of a total | `marks` plus optional `guidance` lines | Marker types one number, in half-mark steps |
| Points list with a limit | `limit` plus `points: - N marks - text` | Tick boxes; the sum stops at the limit; marker can adjust by hand |
| Criteria grid | `criteria:` with `name`, `marks`, and `bands: - lo to hi - text` | Marker picks a band, then an exact mark, per criterion; a comment per criterion; the criteria sum to the space's total |

**Rules that apply to all methods** (`:153-183`):

- Feedback can go on each answer space, plus a closing comment on the paper.
- "Not attempted" (never touched) and "left blank" (opened, left empty) are distinguished. Both score zero.
- "Any N": the page counts attempts but never blocks extra ones. The workbench marks everything, counts the best N, shows which counted, and lets the marker override.
- Marks are stored by name. The spreadsheet has one column per question plus section and paper totals, and a companion sheet explains each column.

**All marking is done by a person.** Nothing is automatic (`:64-72`, `THE_MARKING_WORKBENCH.md:162-167`).

**Question types:**

| Type | What the student does | Teacher writes | How marked | Auto, assisted, or human |
|---|---|---|---|---|
| `multiple-choice` | Picks one option, or several with `choose: several`. Options can be text or small pictures. Fixed order, no shuffling | `options`, `correct: <1-based position>` | Out of a total; no negative marking; for `several`, the scheme states which combinations earn what | Human ("confirm with one keypress") |
| `fill-in-the-blank` | Types into gaps inside a sentence | `text:` with `{word}` for each gap | Out of a total, usually 1 per gap; accepted alternatives "can be listed" | Human |
| `short-written-answer` | Small text box that grows | `prompt`, `model_answer` | Out of a total with a model answer | Human |
| `long-written-answer` | Larger box, sized from the marks | `prompt`, then a marking block | Any method; points list is typical | Human |
| `essay` | Writing view with the title in a strip, live word count against `guide_words`, and an unmarked `planning_box` | `guide_words`, `planning_box` | Criteria grid | Human |
| `numeric-answer` | Labelled final-value boxes plus a working box | `boxes: [{label, expected}]`, `working_box` | Out of a total, split between method and result; ranges such as "accept 3.14 to 3.142" | Human |
| `complete-the-table` | Grid with some cells pre-filled | `columns`, `rows`, with `"?"` marking a cell to fill | Out of a total, equal share per cell by default; guidance on error carried forward | Human |
| `describe-a-sketch` | Chooses the overall shape, then types feature values | `shape: {prompt, options, correct}`, `features: [{label, boxes, expected}]` | Out of a total, split across shape and features | Human |
| `label-the-diagram` | Picture with numbered pointers and matching typing boxes | `image`, `labels: [{number, expected}]` | Out of a total, 1 per label, with alternatives | Human (the builder checks the numbers match, not what the pointers point at) |
| `python-code` | CodeMirror-style editor, Run button, output area. One Pyodide session shared across the whole exam | `starter_code`, `model_answer_code`; exam-level `setup_code`, `provided_code`, `data_files` | Out of a total with guidance. Submission holds the code, the last run's output, and an "edited after run" flag. The workbench "can re-run" the code | Human, with the re-run as an aid |

A type an older tool does not recognise must be refused, never guessed at (`:582-591`). There is no drawing or photo type (Q9).

## 4. Submission, workbench flow, and exports

**Submission** (`THE_SUBMISSION.md`):

- A zip named `dewmark_<code>_<number>_<surname>-<first>.zip` (`:16-29`).
- It contains exactly two files (`:33-68`):
  - `answers.json`: exam code and version, student details, start, save and finish times, every answer by name (for Python: the code, the output of the last run, and the edited-after-run flag), attempts per "any N" section, and a format version.
  - `your-exam.html`: a readable copy with no scripts, never read by tools.
- The file saved continuously during the exam *is* `answers.json`. A bare answer file can therefore be handed in after a crash, and is flagged "collected without a finish step" (`:70-84`).
- Duplicates: the newest by save time is used for each student number, and the marker can override. A version mismatch is flagged (`:86-96`).

**Workbench flow** (`THE_MARKING_WORKBENCH.md`):

1. Load the scheme JSON and open the submissions folder. Opening a folder and saving into it needs Chrome or Edge; other browsers have a manual path (`:13-33`).
2. The workbench validates every submission and lists problems rather than stopping. It treats submissions as data only and never executes anything from them (`:35-51`).
3. The class list shows attempts, marking status, and a running total (`:55-59`).
4. Marking one paper: the answer on the left, the scheme on the right. The design promises a keyboard-first flow (digits, then Enter) and reusable feedback phrases that are copied in, not linked (`:63-93`).
5. Python answers: a warning when the output on file is stale, plus a re-run (`:95-101`).
6. Live totals, with an override for "any N" (`:103-107`).
7. Marking by question, with a blind-marking checkbox (`:111-118`).
8. The marking record is saved into the folder after every change, including the marker's name (`:122-129`).

**Exports**, written to an `exports/` folder (`:133-158`):

- One printable graded paper per student, printed to PDF one at a time.
- `marks` CSV with column headings like `a3 (4)`.
- A companion CSV of names, marks, topics and wording.
- The marking record itself stays as the audit trail.

## 5. Appearance and accessibility promises

`APPEARANCE_AND_READABILITY.md`:

- **Look.** dewlab's navy and orange, a serif face for questions, a sans face for controls (`:12-16`).
- **Exam band.** A formal band with the institution, module and "Examination", distinct from a "Practice" band. It should be recognisable "from across a room" (`:18-25`).
- **Reading.** About twelve words per line. Marks shown as "(4 marks)" on questions and "(2)" on answer spaces, generated from the file. Answer boxes tinted with an edge that changes colour when filled, plus a non-colour mark. Box height set from the marks. No hover-only UI; Escape closes things (`:29-52`).
- **Screen.** One scrolling document with a slim fixed top bar and a collapsible side panel. Only tables and code may scroll sideways (`:56-63`).
- **Student settings.** Text size and line width, remembered per browser, plus light and dark schemes (`:65-68`).
- **Printing.** Boxes expanded, name, number and code on every page, no splits between a question and its answer, "not attempted" printed, no controls printed (`:72-87`).
- **First-release commitments, checked by tests** (`:91-102`): labelled controls, heading and keyboard navigation, visible focus, required alt text, WCAG AA contrast, no meaning carried by colour alone. The doc states frankly that screen-reader sittings of code and maths exams are not solved (`:104-114`).
- **Voice.** Calm, three-part error messages; the finish screen leads with counts; no exclamation marks (`:116-123`).

## 6. Roadmap and where things stand

`ROADMAP.md` phases:

| Phase | Scope | Exit test |
|---|---|---|
| 1 | Builder plus page for all non-code types, saving, finish, submission | Two real past papers sat with the network off; samples published |
| 2 | Workbench | A mock marking session, with the exports read cold by an outsider |
| 3 | Python | A real database practical sat in a room without internet, using locally served Pyodide |
| 4 | Translation assistant, descriptor assistant, teacher guides, then possibly a point-and-click creation tool | — |
| 5 | Improvements justified by real use | — |

Standing rules (`:76-84`): code lands with its document and its tests, and the formats are frozen before any real sitting.

**Current state.** All three runtime parts exist as drafts and all ten types render. The roadmap has no status markers, and **no phase's exit test is recorded as met**. Phase 3 is largely built ahead of phases 1 and 2's exit tests. `docs/DEVELOPMENT.md:66-109` lists the known gaps:

- Maths is typeset as MathML.
- No Stop for a runaway cell, no time or output limits, and no room checklist.
- The essay view is simplified.
- There is no keyboard-first marking and no feedback phrases.
- The "any N" count cannot be overridden in the interface.
- The readable copy is scraped from the live page.
- Only dewmark's own uncompressed zips can be read back.
- Question prose cannot contain a line of three backticks.
- Two markers on one folder means the last save wins.
- The accessibility audit has not been done.

**Further gaps I verified that DEVELOPMENT.md does not list:**

- There is no `--preview` flag (`build_exam.py:1322-1327` has only `--output` and `--check`), although `THE_EXAM_BUILDER.md:34-39` describes it prominently.
- The workbench has no Python re-run and does not show the "draft" label; the label appears only in the answer key (`build_exam.py:889`).
- Exports are browser downloads named `<code>_marks.csv` and `<code>_what_the_columns_mean.csv` (`workbench/index.html:834,844`), not files written to `exports/`.
- The workbench does not record the marker's name.
- The CSS has no dark scheme and no control for text size or line width. There is no `prefers-color-scheme` rule, only `@media print` at `exam-page.css:283`.
- The header band has no institution or module (`build_exam.py:1136-1141`). No key for them exists.
- Pyodide loads from jsdelivr v0.27.4 unless `window.DEWMARK_PYTHON_BASE` is set (`exam-page.js:714-715`). Only the smoke test sets it (`dev/smoke_python_page.py:118`), so a teacher has no way to use the "serve from a laptop" option.
- Packages are installed with micropip from PyPI at sitting time (`exam-page.js:750-757`). That is a network fetch mid-sitting, which contradicts the "nothing fetched" promise.

## 7. Open questions (Q1-Q19)

No question is closed. Each is listed with the assumption the project builds on until it is answered.

| # | Question | Working assumption |
|---|---|---|
| Q1 | Where real exams and submissions live | Teacher's private storage |
| Q2 | Exporting all graded papers as PDFs in one step | One print per student, with auto-advance (auto-advance not built) |
| Q3 | A native Excel file | Two CSVs |
| Q4 | A timer | None; the time is shown only on the opening screen |
| Q5 | Building the class list into the exam | No. Students type their details, and the workbench cross-checks against an optional class list (that cross-check is not in the workbench doc or the code) |
| Q6 | "Any N" counting rule | Best N, overridable and recorded; needs a QA decision before a real sitting |
| Q7 | Getting Pyodide into the room | Open each machine the day before, or a local server. The doc says "both options already work"; see §6 |
| Q8 | "Close and reopen" as the remedy for a frozen page | Accepted. Changing it is claimed to be "substantial" |
| Q9 | Drawn or handwritten answers | Those parts go on paper |
| Q10 | Guided creation tool re-using the Python checks | Deferred; the checks are to be written so they can run in a browser |
| Q11 | The name "dewmark" | Kept; must close before a real sitting |
| Q12 | Marking outside Chrome and Edge | Chromium is the supported environment |
| Q13 | Header design | A navy band |
| Q14 | Browser copy and file disagree | Ask the student, whenever they differ by more than a few seconds |
| Q15 | Pre-checking answers, or LLM-drafted feedback | No |
| Q16 | Screen-reader sittings | Baseline only; alternative arrangements remain |
| Q17 | Typing symbols | Plain text, published conventions, and a palette. The palette is not built |
| Q18 | Comments on a chosen essay passage | Not in the first version |
| Q19 | Descriptor assistant drafting questions | Suggests types only, each with the passage that prompted it |

## 8. Lessons from the 2025-26 experiments

`LESSONS_FROM_THE_EXPERIMENTS.md` covers three experiments: a database practical, a practice paper on image arithmetic, and the two-version MIT maths paper. `experiments/README.md:3` says "two" exams, because the image-arithmetic paper is not included.

**What they got right** (`:28-61`):

- One file, no server, no installation.
- Several versions produced from one paper.
- Describing a sketch instead of drawing one.
- Saving two ways, with an indicator for each.
- Printing taken seriously.
- Answer boxes sized by marks.

**What failed, and the rule each failure produced** (`:63-138`):

| Failure | Rule it produced |
|---|---|
| Answers saved by position (a 115-entry list) | Names everywhere |
| Structure written out three times, and the copies drifted, so a model answer crashed | Generate everything |
| Marks existed only as wording | Marks and choice rules are settings the builder verifies |
| Spreadsheets fetched at sitting time and failed silently | Embed at build time |
| Silent failures when saving or running | Visible indicators, and saving on every change |
| Restore over-promised and crashed across versions | State exactly what came back; code and version checked before anything is restored |
| Outputs saved as HTML and put back into the page | Submissions contain data only |
| No marking tool at all | A workbench, and submissions named by student |

## 9. Critique

### Internal inconsistencies

1. **Multiple choice: "confirm with one keypress" versus "no pre-fill".** `QUESTION_TYPES_AND_MARKING.md:71-72,229-230` says the marker confirms a multiple-choice mark with one keypress. `THE_MARKING_WORKBENCH.md:162-167` says the workbench does not compare answers or pre-fill anything, "even for multiple choice". There is nothing to confirm unless something is proposed. This contradiction is also the policy crux for Q15.
2. **Standalone versus part of dewlab.** `THE_EXAM_BUILDER.md:98-106` says the builder "is part of the dewlab repository and follows its conventions… one well-commented Python file with a companion explanation document". `docs/DEVELOPMENT.md:8-17` says dewmark "stands alone". No companion document exists. Other dewlab dependencies:
   - `THE_EXAM_PAGE.md:162` relies on "the small helper program that dewlab already provides" (`dewlab/dev/fetch_pyodide.py`).
   - `ROADMAP.md:80` and `OPEN_QUESTIONS.md:8-9` point at "the repository's decision log", which is dewlab's.
   - The colours are "dewlab's" (`APPEARANCE:12-16`).
   - dewlab's `build.py:128,7644-7646` copies `dewmark/workbench` into `site/dewmark/`.
   - dewlab's `.github/workflows/tests.yml:98-123` runs dewmark's tests.
   
   All of these break or change when dewmark moves.
3. **"Two settings control help" but only one is described.** `THE_EXAM_FILE.md:243` says two settings do this, and only `hint` is described. The practice build is otherwise the exam build with hints kept, which undersells practice mode.
4. **"Three layers of saving"** (`ROADMAP.md:20`), when every other document describes two.
5. **Save button name.** The spec calls it "Save" (`THE_EXAM_PAGE.md:37`); the teacher guide and the code call it "Save a copy".
6. **Submission name order.** The spec's `<surname>-<first name>` (`THE_SUBMISSION.md:24`) cannot be produced. The code slugifies the literal "full name" field (`exam-page.js:225-229`). It also silently depends on `student_details` containing the exact strings `full name` and `student number`, although the spec presents `student_details` as a free list.
7. **"Data only, no program code".** `THE_SUBMISSION.md:55-56` says this about `answers.json`, while the same file stores student Python code. That is fine as text, but the wording needs care.
8. **When Python loads.** Pyodide is said to download "the first time the page runs code" (`QUESTION_TYPES:571-573`, `THE_EXAM_PAGE:157-159`). The same documents say setup code runs "before the student starts", and the code starts Pyodide at Begin (`exam-page.js:297`).
9. **Q7 says "both options already work".** They do not work for a teacher; see §6.
10. **The essay view does not fit the page model.** The "full-screen writing view" does not fit the single scrolling document with no trapped scrolling (`APPEARANCE:56-60`).

### Under-specified

- **No keys for branding or the finish screen.** No institution, module, college, logo or hand-in instructions exist in the grammar. The opening screen (`THE_EXAM_PAGE.md:18-21`), the band (`APPEARANCE:18-25`) and the finish screen (`THE_EXAM_PAGE.md:121-123`) all need them.
- **Promised syntax that is never defined:**
  - accepted alternatives for blanks and labels (they exist only as prose guidance in the samples);
  - how `choose: several` marks each combination;
  - "the marking block can assign shares differently" for tables;
  - whether a box-size override exists;
  - `draft`;
  - `image_description`;
  - the rule for inferring the marking method;
  - that `limit` must equal marks (the code enforces this, which makes it redundant);
  - which answer spaces require a marking block (the builder check is described, but no rule defines it and the code does not enforce it).
- **What "attempted" means**, which drives "any N" counting, and how "not attempted" versus "left blank" is recorded in `answers.json` (not listed there; the draft shows only "not attempted").
- **Formats never specified:** the marking record, the scheme JSON, and the `answers.json` schema are not specified anywhere, yet the roadmap says they are to be "frozen".
- **What version mismatches do.** Version semantics beyond "warn" are undefined, for example what happens when a mark allocation changed between versions.
- **The translation assistant has no technical design:** no model, no API, no prompt contract, no local or offline option, and no statement of how it "runs the builder on the teacher's behalf" (`THE_EXAM_BUILDER.md:41-46`). This is the main gap given Josh's local-LLM idea.

### Over-specified or brittle

- **YAML is exposed to non-programmers without being named.** Indentation matters. An option list containing `yes` or `no` parses as booleans. An unquoted `:` breaks a line. `0.10` becomes `0.1`. Answers in two small text formats (`2 marks - …`, `16 to 20 - …`) live inside YAML strings.
- **`correct: 3` by position** contradicts the file's own "never by position" principle. Reordering the options silently breaks the answer key, and the builder cannot catch it. dewlab's newer `question` fence (DECISIONS_LOG 7.179, `DECISIONS_LOG.md:3889-3895`) deliberately chose "markdown after the header rather than YAML throughout" and put correctness on the option itself. dewlab now has a **diverging grammar for the same two types**. The log also claims `{a|b|c}` dropdown gaps are "dewmark's own convention", but dewmark's spec and code have only `{word}`.
- **Duplicated marks.** `marks` appears in both the `answer` and `marking` blocks (`THE_EXAM_FILE.md:94,105`), with a check that they agree. That contradicts "nothing written twice".
- **No auto-checking for closed items**, on principle, even for a practice build with no marker at all. It costs roughly 25 students × N closed items in keystrokes, and it forecloses self-marking practice papers.

### Hurdles for a teacher who is not a programmer

- Building requires Python, `pip install`, and a command line (`FOR_TEACHERS.md:59-61`), in a guide that "assumes no programming knowledge".
- The point-and-click tool is Phase 4 "if demanded".
- The file format and the conversion route both assume an LLM assistant that does not exist.
- The Pyodide room preparation is a manual, per-machine ritual, and the checklist is not written.
- Marking effectively needs Chrome or Edge.

### What the docs already say on branding, the start screen, loading, settings, and AI

- **Branding:** dewlab's navy and orange with an "Examination" or "Practice" band; the design is left to Q13. No logo or institution data exists.
- **Start screen:** title, institution and module, time, instructions and details inputs, then Begin, which triggers the file picker (`THE_EXAM_PAGE.md:18-44`). There is no separate settings step.
- **Loading:** the documents mention only a "one-time download" warning, a retry on failure, and a Python status pill. There is no loading screen.
- **Settings:** text size, line width, and light and dark schemes (`APPEARANCE:65-68`). None of it is built.
- **Timer:** explicitly rejected for now (Q4).
- **AI:** an LLM translation assistant with three rules (marks never invented, drafts labelled, uncertainty raised as a question), a descriptor assistant that suggests question types only (Q19), and no LLM marking or feedback (Q15).

**Context from the uploads, structure only.** The newer hand-built 5N2927 pages have moved well beyond this design:

- A `name-screen` with institution, college, module and paper lines, a load-a-file button, a settings link, and a Python readiness indicator (`nc-py`, `nc-dot`).
- A settings pane of about 18 controls: font, size, line height, spacing, width, themes (dark, cream, blue, contrast), code font, size and theme, brackets, Jedi completion, reduced motion, ruler, wrap, and a student-toggleable **timer**.
- CodeMirror 5 from cdnjs, an `.ipynb` export, print, resume or fresh start, and an embedded `exam-src` JSON.

The written design contradicts or omits most of these.

## What this means for dewmark

- **Keep the rules that came from failures.** Names as the key, build-time embedding, leak self-check, submissions as data only, two visible saving routes, human-final marking, no server. They are the design's strongest part, and each is backed by a real incident.
- **Redesign the authoring grammar before freezing it.** Choose one approach shared with dewlab's newer `question` fence: prose options with the correct answer marked inline, and structured keys only where machines need them. Name the carrier explicitly, whether YAML or a stricter subset. Add first-class syntax for accepted alternatives, a named marking method, and draft labels. Remove the duplicated `marks`.
- **Add an explicit "presentation" layer to the exam block and treat the start sequence as a designed flow.** Keys: institution, college, module code, logo, paper kind, hand-in instructions. Flow: identity, then settings, then an asset-loading gate with progress (Pyodide, packages, data), then Begin. The uploads already prove Josh wants this. Settings and a timer need their Q4 and APPEARANCE entries reopened.
- **Specify the three saved formats** (answers, scheme, record) as schemas now, and add a `touched` flag.
- **Make offline Python real.** Add a teacher-settable Pyodide base URL, vendor the packages (no micropip at sitting time), and write the room checklist. Revisit Q8, since a worker plus `terminate()` may give a Stop button without SharedArrayBuffer; this needs checking under `file://`.
- **Decide Q15 differently for practice and for exams.** Auto-check closed items in practice builds, and propose-then-confirm in the workbench. That resolves the multiple-choice keypress contradiction.
- **The LLM assistant needs its own spec.** It should be a provider-neutral interface (for example an OpenAI-compatible chat endpoint, so a local box works) that takes a document and returns an exam file. The builder's `--check` output is the feedback loop. The three trust rules are unchanged, and offline or local is the default.
- **For the move out of dewlab:**
  - Fix `THE_EXAM_BUILDER.md:98-106`.
  - Give dewmark its own decision log and CI job.
  - Take over or re-home `fetch_pyodide.py`.
  - Keep the samples and the experiments.
  - Remove dewlab's `build.py` workbench copy step and its test.
  - Refresh `DEVELOPMENT.md`'s gap list with the verified gaps in §6.
  - Record no roadmap phase as complete.