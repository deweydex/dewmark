# PDP 5N2927 exam pages: technical teardown and comparison with dewmark

Working copies, extracted parts, test scripts and screenshots are in `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/pdp/`. That folder is private scratch space, and it holds a copy of the live 2027 paper and screenshots of it, so none of it should be published or committed. Nothing under `/home/user/dewlab` or `/home/user/dewmark` was modified.

Line references like `js:NNN` point to `scratchpad/pdp/script-2027.js`, the inline script pulled out of the 2027 page. Add 647 to get the line number in the original 2027 HTML file. For example, `KIT_PY` is at `js:259`, which is line 906 of the original.

## 1. Summary

- There are four copies of one hand-maintained runtime, and they have already drifted apart. The DOM template (`body.html`) is byte-identical in all four pages. Sample, Practice 1 and Practice 2 share an identical script (50,776 B) and CSS (23,206 B). The 2027 page has a newer runtime (50,959 B script, 23,648 B CSS) with four script changes and seven lines of CSS the other three lack.
- The paper format is small and readable: flat YAML-ish front matter, Markdown, and five fence kinds. Structure and marks come from heading text (`## Question N: Title (M marks)`). Marks are never checked, and `total_marks` is never read.
- This is the best student-facing Python exam experience seen so far in the project. It has CodeMirror, Jedi completion, an `input()` bridge, a per-run time limit, friendly tracebacks, a large reading-settings drawer, a searchable reference sheet, per-question progress and `.ipynb` export.
- It has no teacher side. There are no marking schemes, no model answers, no per-answer marks as data, no stable answer names and no workbench. Hand-in is a JSON file plus a PDF uploaded to Moodle.
- I verified these serious defects in headless Chromium:
  1. With no network the page is completely dead.
  2. After one runaway `print` loop, browser autosave fails silently for the rest of the sitting while the status bar still says "Saved in browser".
  3. The time limit can be swallowed by `except Exception`, which freezes the tab permanently.
  4. Long C-level calls ignore the limit: one ran for 66 s under a 10 s limit.
  5. Pressing Cancel on an `input()` prompt inside a `try/except` loop traps the student in the loop.

## 2. Files and drift

| Page | `exam-src` | Script | CSS | `<title>` |
|---|---|---|---|---|
| Sample_Exam | 8.7 KB | older | older | hand-typed, then overwritten by JS |
| Practice_Exam_1 | 8.6 KB | older | older | same |
| Practice_Exam_2 | 8.8 KB | older | older | same |
| Exam_2027 | 12.7 KB | **newer** | **newer** | same |

The 2027 runtime adds four things over the older copy:

1. `start=N` on display fences, which offsets line numbering (`js:566`, `js:620`). None of the four papers uses it.
2. `figure` and `div` pass through the paragraph wrapper (`js:589`).
3. A nav label fallback, `q.label || "Question " + q.num` (`js:736`).
4. CSS for `.frac`, `.sqrt` and `.exam-fig`, plus print `break-inside` rules for figures (`style.css:149-155, 319`).

The three older pages would render the 2027 paper's maths and figure badly, which is the "hand-edited copies" problem dewmark's builder exists to remove.

`exam-src` is stored as a single JSON-encoded string on one line (`<script type="application/json" id="exam-src">"---\nexam_id: …"`), so it cannot realistically be edited inside the HTML. An authoring or embedding step presumably exists outside these files, but none is visible.

## 3. The `exam-src` format

### 3.1 Front matter

`parseFrontmatter` (`js:540-545`) needs `---\n…\n---\n` at the very start. It splits each line on the first `:` and keeps every value as a string. There are no lists or multi-line values.

| Key | Read at | Effect |
|---|---|---|
| `exam_id` | `js:24` | Storage key `pdp-exam:<id>`; file names `<id>_<name>_<YYYY-MM-DD>.json/.ipynb` (`js:832-835`); `exam_id` in the JSON; mismatch warning when a file is loaded (`js:861`). |
| `title` | `js:190,194,772,845,884,929` | `document.title` ("title: module"), name card ("title, 2 hours"), header ("module: title"), JSON `exam_title`, ipynb H2, print header. |
| `module` | same places | Name card, header, print, JSON, ipynb H1. |
| `session` | `js:845,929` | JSON `session`; print header "(2025–2026)". Not shown on screen. |
| `institution` | `js:191` | Name card only (small uppercase line). |
| `college` | `js:192` | Name card only (large accent serif line). |
| `kind` | `js:16,700-711` | `exam`, `sample` or anything else (treated as practice). Changes only the end-banner wording and step 3. |
| `duration_minutes` | `js:17,194,784` | Name card text and a countdown timer from the moment Begin is pressed. Not enforced: after zero it shows "Time is up (+m:ss)". |
| `allow_completion` | `js:18` | Anything except the exact string `"false"` counts as on. When off, the Jedi settings group is replaced by a note (`js:113-116`). |
| `show_reference` | `js:19,187` | Hides the reference button. |
| `reference_theory` | `js:20,188` | **Dead key.** It removes `#ref-list [data-theory]` elements, and the template has none. |
| `time_limit_seconds` | `js:21,441` | Per-run limit through `sys.settrace`; `0` turns it off. The reference sheet still says "Stopped after 10 seconds" (original HTML line 480). |
| `error_hints` | `js:22,478` | Friendly hint under a traceback. It is **false in the live 2027 paper** and true in the sample and practice papers. |
| `total_marks` | never | **Unused.** Nothing checks it. |

Parsing is brittle. `False` or `True` with a capital letter is ignored, so completion stays on. A file with CRLF line endings loses all its metadata (tested in Node: `parseFrontmatter("---\r\ntitle: x\r\n---\r\n") → {}`), and its fences break too.

### 3.2 Fences (`parseExam`, `js:546-571`)

The fence regex is ```` ^```([^\n]*)\n([\s\S]*?)^```[ \t]*$ ````. It only supports three backticks, so a fenced block can never contain a fence. The first word of the info string is the kind, and the rest (`arg`) is the label.

| Fence | Block | Behaviour |
|---|---|---|
| ` ```python setup ` | `setup` | Runs silently once Python is ready. Errors only reach `console.warn` (`js:380-385`). None of the four papers uses it. |
| ` ```python LABEL ` | `code` | CodeMirror cell whose body is the starter code. Cells share one `__main__` namespace. |
| ` ```answer LABEL ` | `answer` | Auto-growing textarea. The body is **pre-filled text**, for example the Sample's "Permitted:\n\nNot permitted:\n\nMy fixed versions:". It has a word count. |
| ` ```fields LABEL ` | `fields` | Each body line becomes a labelled row: label in a grid column, textarea beside it. Labels go through `mdInline`. |
| anything else (` ```text `, ` ```py `, ` ```pseudo `) | `display` | Read-only `<pre>`. `py`, `python` and `text` are syntax-highlighted **with line numbers** (`js:621`). Other kinds (e.g. `pseudo`) are escaped plain text with no numbers. `start=N` is optional. |

Labels (`js:558-565`):
- If `arg` is present, it is the label: `1A (i)`, `4B (i): your function`, `1(a)`, `2(d)(i)`, `4(e): main limitation`, `Question 1: rough work (optional)`.
- Otherwise the label is the most recent `##`/`###` heading with its trailing parenthesis stripped (`js:560`). That regex is lazy but anchored at the end, so it matches from the *first* `(`: a heading like `1(a): Title (3 marks)` becomes the label `1` (verified). This is probably why every 2027 fence carries an explicit label.

Cell ids are **positional**: `"b" + n` in document order (`js:562`).

### 3.3 Headings and marks

- `scanProse` (`js:550-555`) sets the current question number from `## Question N` and nothing else. Any other `##` heading resets it to 0.
- `questionList()` (`js:717-722`) re-reads the raw source with `^##\s+Question\s+(\d+)\s*[:.]?\s*(.*?)\s*\((\d+)\s*marks?\)\s*$`. Only headings that match appear in the nav, with their marks.
- Sub-part marks ("### 1A: … (3 marks)", "**(i) … (4 marks).**") are display text only and nothing sums them. By hand they are correct in all four papers.
- Nav progress (`js:723-743`) counts a cell as "started" when its value differs from the starter code ignoring whitespace. Cells whose label contains `optional` are left out of the count.
- There are no sections, no "answer any N", no machine-readable per-answer marks, and no student-number field.

### 3.4 Markdown and inline HTML

`mdToHtml` (`js:574-592`) supports `#`–`######`, `---`, pipe tables, `**`, `*`, `>` quotes, `-`/`*` lists, `1.` lists and inline code, and turns single newlines into `<br>`. **Raw HTML passes through unescaped**, which is how the 2027 paper gets its maths and figure:

- `<span class="frac"><span>num</span><span>den</span></span>`, `√<span class="sqrt">…</span>`, `<i>x</i>²`: three inline-maths occurrences in 2027.
- One `<figure class="exam-fig" aria-label="…"><svg viewBox role="img"><title>…</title>…</svg></figure>` on a single line (a flowchart).

Side effects, verified in Node:
- Prose like `If a<b and b>c` renders as a real `<b …>` element and the text disappears.
- `2 * 3 * 4` becomes `2 <em> 3 </em> 4`, which matters a great deal for a maths paper.

### 3.5 Paper shapes (structure only)

- **Sample and Practice 1/2** have the same skeleton:
  - Q1 has parts A–D (3+3+3+6); Q2 A–B (10+5); Q3 A–C (8+2+5); Q4 A–B (6+9).
  - 17 answer spaces: 5 `answer`, 11 `python` (1 optional), 1 `fields` with 6 rows, and 1 `text` display.
  - 4B pairs a "your function" cell with a "your tests" cell for each sub-part.
  - Two parts have more than one marked space, with the marks not split between them.
- **2027** has 4 questions × 15 marks and 21 parts labelled `N(a)`…`4(f)`, mostly 3 marks each.
  - Answer spaces: 17 `answer`, 10 `python` (including 2 per-question "rough work (optional)" cells), 1 `fields` with 7 rows.
  - Display blocks: 8 `text` and 1 `pseudo`.
  - Four parts have more than one marked space.

## 4. The student flow, screen by screen

Screenshots from headless Chromium 1194. The CDN was reached through Playwright request routing that fetched with the proxy's CA bundle.

1. **Name screen** (`#name-screen`, original line 351):
   - Content: institution, college, a rule, module, "title, 2 hours", **Your full name**, and a checked box "Save my work to a file on this computer as I go". The box is hidden when `showSaveFilePicker` is missing.
   - A tinted note explains saving; it has two wordings (`js:198-200`).
   - Links: **Reading and display settings** (opens the drawer on the name screen) and **Open a saved .json file**.
   - A status dot reads "Python is loading in the background…" and turns green at "Python is ready." Load took 5–15 s cold on this network.
2. **Resume box** (`js:202-208`): if `localStorage` holds work for this `exam_id`, the page shows "This browser has saved work for <b>Name</b>, last saved <time>", **Continue where I left off**, and **Start this paper again** (confirm, then clear). Continuing asks no identity question. Because the hidden checkbox stays ticked, the file picker pops up again with no explanation (`js:750,760`).
3. **Begin** (`js:746-781`):
   - An empty name gives `alert()`.
   - With the box ticked, `showSaveFilePicker({suggestedName: <exam>_<name>_<date>.json})` opens. Cancelling it silently falls back to browser-only saving.
   - The start time is recorded, so the timer runs per student from Begin.
   - The file handle is not persisted, so every reload needs a new pick.
4. **Main view**:
   - Header: title, student chip, timer (warning colour under 10 min, error colour after zero; the student can hide it), Python status chip, save status, and the buttons **Python reference**, **Settings**, **Save**, **Export .ipynb** and **Print / PDF**.
   - Left panel: student, question list (number badge, title, "15 marks", "n/m started", progress bar), "Your work" save explanation, **Open a saved .json file**, and keyboard shortcuts.
   - Main area: the paper at a fixed reading measure. Run buttons read "Loading" (disabled) until Python is ready.
   - Buttons are enabled *before* setup blocks run (`js:353-354`), which creates a race if a paper uses setup code.
5. **Running a cell** (`js:427-459`):
   - Ctrl/Cmd+Enter or Run.
   - Output goes into a per-cell `<pre>`, with stderr in a span.
   - Status shows "Ran 11:49" or "Error".
   - **Reset** restores the starter code after a confirm.
6. **Errors** (`js:461-482`):
   - The traceback is filtered to frames in `"<your code>"` and rewritten as "Line 3 of your code" or "…, inside the function work".
   - When `error_hints` is on, a one-line hint follows from a table of 12 exception types (`js:412-425`).
7. **`input()`** (`js:287-300`, `394-409`):
   - `builtins.input` is replaced with a function that calls a **synchronous `window.prompt`**. The dialog text is the last four output lines plus the prompt.
   - Time spent typing is added back to the deadline.
   - Cancel raises `InputCancelled` ("You closed the input box, so the program stopped.").
   - The typed value is echoed into the output as a highlighted span.
   - The student instructions and the reference sheet call the dialog "a small box at the top of the screen".
8. **Time limit** (`js:270-285`): `sys.settrace` compares `time.monotonic()` with a deadline on every line and raises `TimeoutError("Your code ran for more than 10 seconds…")`. Verified: a plain `while True` stops at 10.0 s.
9. **Jedi** (`js:370-379`, `485-537`):
   - The `jedi` and `parso` wheels load after Python is ready.
   - Hints pop up after 180 ms on word characters or `.`, skipping comments and strings; Ctrl+Space also triggers them.
   - A signature tip under the cell shows the current parameter in bold and the first docstring line.
   - Verified: `prin` + Ctrl+Space offers `print`, and typing `print(` shows the full signature and doc line.
10. **Settings drawer** (original line 416): a right-hand drawer with these options, stored in `localStorage["pdp-exam-settings"]` and applied across every paper:
    - **Reading**: font (Georgia, system sans, Atkinson Hyperlegible, Lexend, OpenDyslexic), text size 14–28 px, line spacing 1.3–2.4, letter/word spacing (normal/wide/wider), text width (60/75/95ch/full), colours (light, cream paper, blue tint, dark, high contrast), reading ruler, live preview.
    - **Code editor**: font (Courier New, system mono, Atkinson Hyperlegible Mono), size 12–26 px, colours (auto/light/dark using Dracula), wrap, auto-close brackets.
    - **Suggestions**: on, pop up while typing, signature hints.
    - **Exam**: show timer, reduce motion, **Reset all settings**.
    - The note says print always uses a standard layout.
11. **Reference sheet** (original line 472): 11 collapsible sections, all hard-coded in the template rather than taken from `exam-src`:
    - "This exam tool", values and types, operators, strings, I/O, if, lists/range, loops, functions, comments, error names.
    - A search box filters and expands sections; code samples are highlighted and have Copy buttons.
12. **Saving** (`js:793-831`):
    - Every edit marks the page dirty. After 1.5 s (50 ms after a run) it writes `localStorage` and, if there is a file handle, writes the file. It also flushes every 15 s.
    - `beforeunload` writes and asks for confirmation.
    - Ctrl+S or **Save** writes the handle, or downloads the JSON (a new download each time).
    - Status messages: "Saving", "Saved in browser HH:MM", "Saved to file HH:MM", "Downloaded HH:MM", "File save failed".
13. **Opening a `.json` file** (`js:857-877`):
    - Validates that `cells[]` exists and warns on an `exam_id` mismatch ("Answers are matched by position…").
    - Restores values, **restores `output_html` through `innerHTML`**, and takes the start time from the file.
14. **End banner** (`js:698-714`), "the three steps":
    1. **Print a PDF for the assessor** through Print / PDF and "Save as PDF".
    2. **Save your submission file (.json)**.
    3. For `kind: exam`: "Upload your .json file and your PDF to the exam submission link on **Moodle**. Then raise your hand so your invigilator can confirm your submission." For sample and practice: "Keep your files", plus a mention of .ipynb.

    Moodle is hard-coded in the runtime.
15. **Print** (`js:912-931`, CSS 293-323):
    - Editors are replaced by highlighted, numbered `<pre>` blocks, and answers become text, with "(no answer)" in grey italics.
    - Each `## Question N` starts a new page.
    - One bordered header block on page 1 only: name, "module: title (session)", printed time, "Time since starting: N minutes".
    - Institution and college do not appear. The Sample printed to 10 pages.
16. **`.ipynb` export** (`js:880-904`):
    - A header markdown cell.
    - Prose becomes markdown cells, display code becomes fenced markdown, and code cells keep `metadata.exam_label` and one stream output. If the run errored, all of that output is labelled `stderr`.
    - Answers become quoted markdown ("**Your answer: 1B**").

**Submission JSON** (`format: "pdp-exam/1"`, `js:836-848`, confirmed against a real download):

```json
{ "format": "pdp-exam/1", "exam_id": "pdp-5n2927-sample", "exam_title": "Sample Examination",
  "module": "Programming and Design Principles 5N2927", "session": "2025–2026",
  "student_name": "Aoife Test", "started_at": "ISO", "exported_at": "ISO",
  "cells": [
    {"id":"b0","type":"answer","question":1,"label":"1A (i)","answer_text":"…"},
    {"id":"b5","type":"code","question":1,"label":"1C","student_code":"…",
     "output_text":"…","output_html":"<pre class=\"stdout\">…","has_error":true,"last_run":"ISO|null"},
    {"id":"b12","type":"fields","question":4,"label":"4A",
     "fields":[{"label":"Function name","answer":"…"}]} ] }
```

`localStorage["pdp-exam:<id>"]` holds a different shape: `{savedAt, name, startedAt, values:{b0:"…", b12:["…"]}, outputs:{b5:{html,text,hasError,lastRun}}}`.

The submission has no version, no paper hash, no student number, no "edited since last run" flag and no per-answer marks.

## 5. Branding

The only branding is text from front matter. It appears in these places:
- Name card: `institution` (0.72rem uppercase, muted), `college` (1.45rem bold accent serif), then `module` in bold and "`title`, 2 hours".
- Header bar: "`module`: `title`" in accent colour, with the student chip.
- `document.title`: "`title`: `module`", overwriting the static `<title>` that was hand-typed into each file.
- Print header: name, module, title and session, with no institution or college.
- ipynb header: module and title. JSON: `exam_title`, `module` and `session`.
- The H1 inside `exam-src` repeats "module: title" by hand.

There is no logo, no institution colour (accent is hard-coded `#2c5f8a`, `style.css:7`), no candidate or student number, and no visual difference between exam and practice in the main view. `kind` only changes the end banner. The Moodle and invigilator wording is baked into the runtime.

## 6. Accessibility

**Present:**
- Five fonts, including OpenDyslexic, Atkinson Hyperlegible and Lexend, plus size, line-height, letter/word spacing and measure controls.
- Five colour themes, including high contrast, and separate code font, size and colour settings.
- Reading ruler, option to hide the timer, reduce motion.
- `lang="en-IE"`, `:focus-visible` outlines, `aria-live` on cell output and save status, `aria-pressed` on the drawer toggles.
- Labelled textareas ("Answer 1A (i)") and `<label for>` on field rows.
- The SVG figure has `role="img"`, a `<title>` and an `aria-label`.
- Friendly error text, word counts, and a print layout that ignores screen settings.

**Gaps:**
- Tab in CodeMirror inserts spaces (`js:644`) and nothing leaves the editor, so keyboard users are trapped in it (WCAG 2.1.2).
- The closed drawer is `aria-hidden` but still focusable. I counted 32 tabbable controls in it while closed, and it is not `inert`.
- The ruler follows the mouse only.
- The page ignores `prefers-reduced-motion` and `prefers-color-scheme`.
- The low-time warning is signalled by colour alone.
- The disabled "Loading" button is white on `#999`, about 2.8:1.
- The name card has `role="dialog"` without `aria-modal`.
- The editor's `aria-label` sits on the wrapper, not on CodeMirror's hidden textarea.
- `input()` uses the native prompt, which is accessible but blocking.
- OpenDyslexic and the other fonts only load from a CDN.

## 7. Network dependencies and offline behaviour

**Loaded, render-blocking, in `<head>`:**
- `cdn.jsdelivr.net/pyodide/v0.27.4/full/pyodide.js`.
- Seven CodeMirror 5.65.16 scripts and three CSS files from cdnjs (core, python mode, show-hint, runmode, matchbrackets, closebrackets, comment, dracula).
- Google Fonts (Atkinson Hyperlegible, Atkinson Hyperlegible Mono, Lexend) and `@fontsource/opendyslexic@5` 400 and 700 from jsdelivr.

**Loaded at runtime:** `pyodide.asm.wasm` (10.1 MB), `python_stdlib.zip` (2.4 MB), `pyodide.asm.js` (1.25 MB), `pyodide-lock.json`, and the jedi (4.9 MB) and parso (0.35 MB) wheels. The measured total is about **19.3 MB** per cold machine.

**Offline, verified with a Playwright `offline=True` context:**
- `prepareReference()` calls `CodeMirror.runMode`, which throws `ReferenceError: CodeMirror is not defined` inside the `DOMContentLoaded` handler (`js:186`).
- Everything after that line never runs. The name card is blank (no institution or module), **Begin does nothing**, and the status says "Python is loading…" forever.
- Even the written questions cannot be reached. Screenshot: `shots/offline_Sample_Exam_name_screen.png`.
- Because the CDN scripts are synchronous in `<head>`, a slow CDN (as opposed to an unreachable one) blocks the whole page from rendering.
- The error text written for a Python failure ("Check your internet connection…", `js:358`) can never appear in the fully offline case.

## 8. Weaknesses and bugs

Items marked **V** were verified in the browser or in Node; the rest come from reading the code.

1. **V – Offline means a dead page** (section 7). Written answers are blocked by missing code-editor assets.
2. **V – Silent autosave failure.**
   - Scenario: `while True: print(i)` produced 1.37 M lines and 16.7 MB of output in 10 s (20–24 s wall time).
   - After that, every `localStorage.setItem` threw `QuotaExceededError`, which is only `console.warn`ed (`js:805-808`).
   - `flushSaves` still reports "Saved in browser HH:MM" (`js:801`).
   - An answer typed afterwards was absent from storage.
   - The cause is storing `output_html` and `output_text` without a size cap, which also bloats the JSON file.
3. **V – The time limit can be swallowed.**
   - `TimeoutError` is an `Exception`. When the trace function raises, CPython unsets the tracer.
   - A loop that calls a function inside `try: … except Exception: pass` therefore catches the timeout once and then runs forever with tracing off. The tab stayed frozen past 140 s.
   - Control run: the same code with `except ValueError` stopped at 10.1 s.
   - This is a common student pattern in "keep asking until valid" questions.
4. **V – Long C-level calls ignore the limit.** `sum(range(10**9))` ran for 66 s before the tracer got a line event. The UI is frozen throughout, with no Stop button.
5. **V – Cancel on `input()` inside `while True: try … except:` re-prompts endlessly.** `InputCancelled` is caught, so the only way out is to type valid input.
6. **Shared computers.** Work stays in `localStorage` after hand-in, and nothing clears it. On `file://` all pages share one origin in Chrome. The next person on that login sees "saved work for <name>" and can continue it without any identity check.
7. **Positional ids** (`b0…`). Editing the paper shifts every answer, and loading a file into a revised paper puts answers in the wrong places. The confirm dialog even admits this.
8. **`output_html` → `innerHTML` on load** (`js:660,868`). A crafted student file can run script in the browser of any teacher who opens it with this page.
9. **Markdown renderer**: raw `<` in prose turns into HTML, `a * b * c` becomes italics, CRLF files break, only lowercase `false` is recognised, default labels are truncated, there are no four-backtick fences, and `## Section …` headings drop cells out of the nav.
10. **Dead or stale configuration**: `total_marks` and `reference_theory` are never used. The reference sheet hard-codes "10 seconds" and "box at the top of the screen", and Moodle is hard-coded.
11. **Setup race**: Run buttons are enabled before setup blocks finish, and setup errors are silent.
12. **Print**:
    - The name appears on page 1 only.
    - Chrome's default headers and footers print the local `file:///…` path.
    - The flow depends on students choosing "Save as PDF" rather than a lab printer.
    - Two artefacts (JSON and PDF) must be matched up by hand.
13. **UX details**:
    - Resume re-opens the file picker without explanation.
    - The file handle is not persisted.
    - File dates come from `toISOString`, i.e. UTC.
    - `formatDuration(90)` gives "90 minutes".
    - The nav puts a `<div>` inside a `<span>`.
    - Jedi runs synchronously on the main thread on every debounced keystroke.

## 9. Comparison with dewmark's specification

### 9.1 What the PDP pages do better

**For students:**
- A real editor with highlighting, line numbers, soft tabs, bracket matching, comment toggling and Ctrl+Enter. dewmark's page uses a plain `<textarea class="dm-code">` (`build_exam.py:753`).
- Optional Jedi completion and signature hints.
- An `input()` bridge that shows context and echoes the reply.
- A per-run time limit that works from `file://`. This partly answers dewmark's OPEN_QUESTIONS Q8, whose current assumption is "no Stop button, close and reopen".
- Tracebacks trimmed to the student's code, and toggleable hints.
- A reading-settings drawer far beyond dewmark's plan, which offers only size, width and light/dark (`APPEARANCE_AND_READABILITY.md` §3).
- A searchable Python reference, per-question progress, word counts, `.ipynb` export, pre-filled scaffolds in answer boxes, line-numbered display code for "explain line 4" questions, optional rough-work cells, Python warming up while the name screen is still showing, and practice papers that rehearse the real hand-in steps.

**For the teacher:** the paper source is 8–12 KB of plain Markdown with five fence kinds. A teacher could write a new practice paper in well under an hour.

### 9.2 What dewmark has that PDP lacks

- Marks stored as data on every answer space, checked against `total_marks`.
- Sections with `choose: N`.
- Ten question types: multiple choice, fill in the blank, numeric with working, complete the table, describe a sketch, label the diagram, essay with a planning box, and others.
- `marking` blocks (marks with guidance, points with a limit, criteria grids) and model answers that are stripped from the student page and leak-checked.
- An answer key, permanent names, `version`, `student_details` (name and number), embedded `data_files`, `python` package lists, `provided_code` and `reference` blocks per exam.
- A calculator, build-time maths typesetting (`$…$`), and required alt text on pictures.
- A finish/check screen and a zip submission containing `answers.json` stored under names plus a readable HTML copy.
- An "edited since last run" flag.
- A workbench, graded papers and a marks spreadsheet.
- Lazy Pyodide loading with a retry button and a `DEWMARK_PYTHON_BASE` override (`assets/exam-page.js:711-775`), so non-Python papers need no network.

dewmark's exam block has **no `institution`, `college` or `module` keys**, even though APPEARANCE §1 and OPEN_QUESTIONS Q13 assume a header band that shows them. That is a gap to close.

### 9.3 Converting one format to the other

**PDP to dewmark** is mechanical apart from five format gaps.

- **Direct mappings:**
  - `exam_id` → `exam_code`, `duration_minutes` → `time_allowed`, `total_marks` → `total_marks`.
  - `## Question N (M marks)` → a `question` block.
  - `answer` → short or long written answer, `python` → `python-code` with `starter_code`, `python setup` → `setup_code`.
  - `frac`/`sqrt` HTML → `$\frac{}{}$`; the inline SVG → a `pictures/*.svg` file referenced as `![description](path)`.
- **Gaps that block conversion:**
  1. `fields` has no equivalent. It is closest to numeric-answer `boxes` without `expected`, or a two-column complete-the-table.
  2. Optional rough-work cells need an unmarked (`marks: 0`) answer space.
  3. Several spaces sharing one part's marks (1A (i)–(iii) at 3 marks; function and tests cells at 4 marks). dewmark's per-space marks force the teacher to split marks. This affects 2 parts in each practice paper and 4 in 2027.
  4. Pre-filled answer text: dewmark's `hint` is a placeholder that the exam build strips.
  5. Line-numbered display code with `start=`.
- **New Python settings needed:** `completion`, `error_hints` and `time_limit_seconds`. The Python reference sheet would become a standard `reference` block.
- **Effort:** a converter is about 150 lines, reusing PDP's own regexes. The only real authoring work is writing marking schemes and model answers, which none of the PDP papers has.

**dewmark to PDP** is not possible for most of the catalogue. Multiple choice, blanks, tables, sketches, diagrams, sections and choice rules, calculator, data files, matplotlib output (PDP captures stdout only) and marking all have no PDP equivalent. From the dewmark samples, only `python-code`, short and long written answers and essay-as-textarea would survive, so the maths and biology samples would lose most of their structure.

## What this means for dewmark

- **Use PDP's student runtime as dewmark's Python engine, and fix it.**
  - Keep CodeMirror (give it an Escape-to-leave key), Jedi as an exam setting, the `input()` bridge, trimmed tracebacks and hints, and line-numbered display code.
  - Fix the timeout: raise a `BaseException` subclass and re-arm the tracer so `except Exception` cannot swallow it. Cap stored output (for example 200 KB per cell), and never store or re-inject HTML.
  - Keep dewmark's `edited-since-run` flag.
- **Adopt the settings drawer wholesale** as dewmark's readability panel, and add the fixes from section 6.
- **Open with a settings screen.** Josh's idea fits naturally:
  - Identity: name and student number.
  - Reading settings, previewed live.
  - A loading checklist covering fonts, editor, Python and suggestions, each with a state and a retry.
  - A clear "written questions are ready now" message that never depends on Python.
- **Bundle everything except Pyodide into the page**: editor, fonts and reference, with no render-blocking CDN tags. Pyodide should come from a local folder or room server, with PDP's time-to-ready shown to the student.
- **Branding should be data.** Add `institution`, `centre`/`college`, `module` (name and code), `session`, `kind` (exam/practice/sample), an optional embedded logo and accent colour, and a configurable `hand_in` text in place of hard-coded Moodle. Show them in a header band on screen, on every printed page, in the JSON and in file names.
- **Add to the spec for PDP parity:**
  - A labelled-short-answers type for `fields`.
  - Unmarked rough-work spaces.
  - `starter_text` for written answers.
  - Marks at part level shared across several answer spaces.
  - A standard Python `reference` block.
- **Handle shared computers**: clear or lock browser storage after finishing, ask for identity again on resume, and use stable names instead of positions.
- **Two conversion tools make natural early milestones.** A `pdp-exam` Markdown to dewmark converter would prove dewmark's format is a superset. A workbench importer for `pdp-exam/1` submissions (keyed on `exam_id` + `label`) would let papers already sat in PDP be marked in dewmark.

**Screenshots** (all in `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/pdp/shots/`; the `Exam_2027_*` files show the live paper and must stay private):
- Name screen and main view for each paper: `Sample_Exam_{1_name_screen,2_name_screen_python_ready,3_main_view}.png`, and the same three for `Practice_Exam_1_*`, `Practice_Exam_2_*` and `Exam_2027_*`.
- Sample walkthrough: `Sample_Exam_4_error_hint.png`, `5_input_echo`, `6_jedi`, `7_settings`, `8_reference`, `9_dark_dyslexic_ruler`, `10_end_banner`, `11_resume_box`, `12_print_p1/p3/p4`.
- `offline_Sample_Exam_name_screen.png`: the dead page with no network.

**Other artefacts** in `scratchpad/pdp/`: `saved_sample.json`, `saved_sample.ipynb`, `print_sample.pdf`, `parts/<page>/{script.js,style.css,body.html,exam-src.json}`, and the test scripts `shoot.py`, `interactB.py`, `interactC.py` and `offline.py`.