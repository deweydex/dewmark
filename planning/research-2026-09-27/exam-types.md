# Question types for dewmark beyond programming: research report for the lead designer

## 0. Headlines

- **The real gap in maths is the answer box, not the list of types.** In `dewmark/samples/maths-for-it-5n18396.exam.md`, 65 of the 70 answer spaces are `short-written-answer` (50) or `long-written-answer` (15). Two are `complete-the-table`, three are `describe-a-sketch`, and none uses `numeric-answer`. Getting typed maths right matters more than adding new types.
- **Keep plain text as the stored answer. Add a live rendered preview, a symbol palette, and an "answer on paper" type.** Leave the WYSIWYG editor (MathLive), graph plotting and freehand drawing until later. This agrees with dewmark's current assumption in Q17 (`planning/OPEN_QUESTIONS.md`) and with Kobel-Keller and Sangwin (2026). Sangwin wrote STACK.
- **Biology needs three cheap additions:** matching, ordering, and a label-bank option on `label-the-diagram`. It also needs structured tolerance, significant-figure and unit settings on `numeric-answer`. Biological drawing and plotting a graph from data should stay on paper for now.
- **"Assisted" marking gives the most for the effort.** The workbench would sort answers and suggest a mark: numeric tolerance checks, algebraic equivalence by evaluating at random points (as Numbas does), and running hidden tests on submitted code. The marker confirms every mark. Q15 ("no automatic checking of any kind") has to be reopened explicitly to allow this.
- **Interoperability:** do GIFT export for the easy subset and Moodle XML for most of the rest before attempting QTI 3.0. Store answer keys as structured data rather than prose so that all three exports are mechanical.
- **QQI:** the exam file needs `technique`, `weighting` and `outcomes` fields. The marks export needs a percentage, the grade band, a receipt log for submitted evidence, and a record of any accommodations.

## 1. What is already designed

- **The catalogue.** `planning/QUESTION_TYPES_AND_MARKING.md` §3 defines ten types, and `build_exam.py:40-51` (`SUPPORTED_TYPES`) implements the same ten: multiple-choice, fill-in-the-blank, short and long written answer, essay, numeric-answer, complete-the-table, describe-a-sketch, label-the-diagram and python-code.
- **Marking.** §2 defines three methods: marks out of a total, a points list with a limit, and a criteria grid. Every mark is entered by a person (§2, lines 64-72).
- **Typed maths.** Short answers are plain text plus a symbol palette (§3.3, lines 301-306; Q17). The maths sample adds a "Typing mathematical notation" reference card (`maths-for-it-5n18396.exam.md:18-37`), which asks students to be consistent within an answer ("`x^2`, `x**2`, and 'x to the power 2' all mean the same thing").
- **Maths in the question text** is converted to MathML at build time by `latex2mathml` (`requirements.txt`; `build_exam.py:644-666`). The exam page has an offline calculator (`assets/exam-page.js:915ff`).
- **Declared limits.** No drawing type (§3.8, lines 488-491; Q9). Tolerance is written as prose in the guidance ("accept 3.14 to 3.142", §3.6 lines 413-414).
- **The hand-built 5N2927 pages** (Sample, Practice 1 and 2, Exam 2027) each hold their source as markdown inside `<script id="exam-src">`. They use only four block kinds:
  - `answer`: a free-text box.
  - `python`: a runnable cell.
  - `fields LABEL`: one short box per line of the block body. The Sample uses it for its question 4A. dewmark has no equivalent.
  - display blocks (`text`, and `pseudo` in the 2027 paper), rendered read-only.

  Front-matter keys are `exam_id, title, module, session, institution, college, kind, total_marks, duration_minutes, allow_completion, show_reference, reference_theory, time_limit_seconds, error_hints`. The pages stop runaway Python with a `sys.settrace` deadline (Sample HTML lines 907-935; typing time is excluded). That works on a page opened as a local file, which partly answers Q8. The pages also open on a name card with a "Reading and display settings" link (lines 345-367), and settings persist in `localStorage["pdp-exam-settings"]`.

## 2. What established systems do

### Maths engines

- **Numbas** (Newcastle; Apache-2.0; runs in the browser; SCORM or "standalone .zip" download).
  - Part types: mathematical expression, number entry, matrix entry, match text pattern, choose one, choose several, match choices, gap-fill, information only, and extension.
  - **Expression marking evaluates the student's answer and the key at random values of the variables.** Settings: `checkingType` (absolute difference, relative difference, decimal places, significant figures), `checkingAccuracy`, `vsetRangePoints`, `failureRate`, and `mustMatchPattern` to enforce a form (factorised, expanded and so on).
  - Number entry settings: `minvalue`/`maxvalue`, `allowFractions`, `mustBeReduced`, `precisionType` (dp or sigfig), `precision`, `strictPrecision`, `precisionPC` (partial credit when the precision is wrong), and `notationStyles`.
  - **"Adaptive marking"** is error carried forward done mechanically: a later part is re-marked using the student's own earlier answers in place of the question's variables.
  - The JME parser (`runtime/scripts/jme.js`) is Apache-2.0 and could be reused.
- **STACK** (Moodle plugin; the Maxima computer algebra system on a server).
  - Inputs: algebraic, numerical, units, matrix, true/false, string/notes, multi-line (textarea or **equivalence reasoning**), JSXGraph, GeoGebra, drag-and-drop.
  - Useful ideas to copy: **"Student must verify"**, where the input is shown back in typeset form before it is accepted; syntax hints; forbidden words; forbid floats; require lowest terms.
  - The equivalence-reasoning input treats each typed line as a step and checks that each line is equivalent to the one before. This is the automated version of "show your working".
  - It needs a server, so it does not fit dewmark. Its interface ideas do.
- **Möbius** (DigitalEd; commercial; Maple-graded). Response areas include math formula, Maple-graded, numeric, **sketch** (a click-and-drag sketch board), **clickable image**, free-body diagram, sorting, matching, and document upload.

### Typed maths input

- **MathLive `<math-field>`** (MIT; v0.107).
  - Size: `mathlive.min.js` is 844 KB raw and 226 KB gzipped. Twenty KaTeX `.woff2` fonts add about 260 KB. Offline use means setting `fontsDirectory` and setting `soundsDirectory` to null, or inlining the files.
  - It has a virtual keyboard, a speech command, and outputs LaTeX, ASCIIMath, MathML, MathJSON and spoken text.
  - Its sibling, the Cortex Compute Engine (MIT), can check equivalence in JavaScript.
- **Kobel-Keller and Sangwin, "Typed Mathematical Text for On-screen Examinations"** (arXiv 2605.25276, 2026) is a position paper; it reports no experiments.
  - It argues for a human-editable text format as the source of truth: Unicode plus Markdown plus "Space Math" (AsciiMath-like, where spacing tells function application apart from multiplication), with an immediate twin-pane preview and optional equation editors.
  - On WYSIWYG editors: "switching from typing at a keyboard to clicking/dragging a mouse interrupts the train of thought."
- **Finland's Abitti** has run the matriculation examinations fully digital and offline (USB-booted machines on a local server) since 2019, including mathematics. Its maths editor, `digabi/rich-text-editor`, is open source. It combines text, LaTeX formulas and screenshots from permitted tools such as GeoGebra. It is the closest real-world precedent for dewmark.

### Graphs and sketches

- **JSXGraph** (MIT or LGPL; v1.13.3). `jsxgraphcore.js` is 969 KB raw and 251 KB gzipped. STACK and Numbas both use it for "drag the vertex or roots" and "place points" inputs.
- **GeoGebra** can be self-hosted from the "Math Apps Bundle" (`deployggb.js`), but under a **non-commercial licence**, and the bundle is large. It is a poor fit for a public repository or a single-file page.

### Science and biology

- **Moodle core** covers most science formats: drag-drop onto image (`ddimageortext`), drag-drop markers (`ddmarker`), drag into text (`ddwtos`), select missing words (`gapselect`), and ordering (moved into core in Moodle 4.4).
- **Inspera** handles "complex mathematics, drawings" with **InsperaScan**: pre-printed answer sheets carry a per-candidate, per-question code, and scanned pages are attached automatically to the right candidate and question.

### Programming

- **CodeRunner** (Moodle) marks against test cases, some of them hidden, either all-or-nothing or per test. The code runs on a Jobe server.
- **Parsons problems** ask students to put given lines in order, possibly with distractor lines. They were validated as exam questions by Denny, Luxton-Reilly and Simon (ICER 2008), who found them discriminating and quick to mark.

## 3. Taxonomy

Effort key: **Exists** means it is in `SUPPORTED_TYPES`. **S** means days of work reusing current machinery. **M** means one to three weeks, including a keyboard route, the workbench view and tests. **L** means a new component or library, plus accessibility design.

| Question type | Subjects | What the page must provide | Marking | QTI 3.0 / Moodle XML / GIFT | Effort |
|---|---|---|---|---|---|
| Multiple choice (single; true/false as a special case) | all | Radio list; picture options | auto (marker confirms) | `qti-choice-interaction` max-choices=1, `match_correct` / `multichoice`, `truefalse` / yes | Exists |
| Multiple response | all | Checkboxes, "choose N" hint | auto with partial-credit rule | choice max-choices>1 + `map_response` / `multichoice single=false` / % weights | Exists (`choose: several`); needs a structured scoring rule (S) |
| Matching (term to definition, symbol to meaning, graph to equation) | bio, prog, maths | One drop-down per row, not drag | auto | `qti-match-interaction` / `matching` / yes | S |
| Ordering / sequence (mitosis stages, digestion route, "oldest to newest") | bio, prog | Up/down reorderable list | auto (exact, or adjacent-pairs partial credit) | `qti-order-interaction` / `ordering` (core since 4.4) / no | S |
| Fill in the blank (typed) | all | Inline boxes | assisted (accepted alternatives) | `qti-text-entry-interaction` / `cloze` SHORTANSWER / missing word (one blank) | Exists |
| Drop-down cloze / word bank | bio | Inline selects | auto | `qti-inline-choice-interaction`, `qti-gap-match-interaction` / `gapselect`, `ddwtos` / no | S (option on fill-in-the-blank) |
| Labelled boxes ("fields") | prog, all | N labelled one-line boxes | human | several `qti-text-entry-interaction` / `cloze` | S (in the hand-built pages, missing in dewmark) |
| Short / long written | all | Growing textarea | human, points list | `qti-extended-text-interaction` + `qti-rubric-block view="scorer"` / `essay` + graderinfo / essay | Exists |
| Essay with criteria grid | all | Full-width writer, word count, planning box | human, criteria grid | extended-text + rubric-block / `essay` (Moodle rubrics live in Assignment) | Exists |
| Numeric with tolerance, sf/dp and units | maths, bio | Value box, optional unit box, working box | assisted | text-entry (float) + `qti-equal tolerance-mode` or `qti-equal-rounded` / `numerical` (tolerance, units) / `{#x:tol}`, `{#a..b}` | Exists; add a structured `accept:` block (S) |
| Exact or fraction form (`sqrt(3)/2`, `3/8` in lowest terms) | maths | Text box + rendered preview | assisted (evaluate, then check form) | text-entry + custom operator / STACK only | M |
| Algebraic expression or equation (final answer) | maths | One-line input, preview, "we read this as…" echo | assisted (random-point equivalence, form patterns) | text-entry + custom operator or PCI / STACK only | M |
| Typed working (multi-line steps) | maths | Multi-line box, per-line preview | human (method marks, error carried forward) | extended-text / STACK equivalence reasoning | S (preview); M (per-line) |
| Matrix / vector entry | maths L6 | Grid without headers | assisted | text-entry grid / STACK matrix | S (a complete-the-table variant) |
| Complete the table (value tables, truth tables, Punnett squares, trace tables) | all | Table with cell inputs | assisted per cell | text-entry in table / `cloze` in an HTML table | Exists |
| Describe a sketch | maths, bio | Shape choice + feature boxes | assisted | choice + text-entry | Exists |
| Place points / sketch on axes (vertex, roots, plotted data, best-fit line) | maths, bio | JSXGraph board, with coordinate boxes as the keyboard route | assisted (coordinate tolerance); human for scale and labels | `qti-select-point-interaction`, `qti-position-object-interaction` or PCI / none in core | L |
| Shade regions (Venn diagrams, inequality regions) | maths | Clickable regions, with a checkbox list as the equivalent route | auto | `qti-hotspot-interaction` max-choices>1 / none in core | M |
| Label the diagram (typed, numbered pointers) | bio | Image + numbered boxes | assisted | text-entry / `cloze` | Exists |
| Label from a bank | bio | Drop-down per pointer (drag optional) | auto | `qti-graphic-gap-match-interaction` / `ddimageortext` | S (drop-downs); M (drag) |
| Hotspot ("click the organelle") | bio | Image regions + keyboard list | auto | `qti-hotspot-interaction` / `ddmarker` (approximate) | M |
| Data response / interpret an experiment | bio, science | **Stimulus panel** (table, chart, method) kept beside the sub-questions | mixed | shared stimulus (`qti-assessment-stimulus-ref`) + items / description + questions | S (only the stimulus panel is new) |
| Plot a graph from data | bio, maths | Axis setup, plotting, best-fit line | assisted and human | PCI | L; paper for now |
| Freehand drawing (biological drawing, flowchart) | bio, prog | Canvas (stylus) | human | `qti-drawing-interaction` / plugins only | M, with fairness problems; paper for now |
| Python code | prog | Editor, Run button, output | human; re-run | extended-text (preformatted) or PCI / CodeRunner | Exists |
| Code with hidden tests | prog | No change on the page; the **workbench** runs the teacher's tests | assisted | CodeRunner test cases / none in QTI | M |
| Predict the output / explain each line | prog | Read-only code + boxes (or the 5N2927 "comment each line" pattern) | assisted (exact compare) | text-entry / extended-text | S |
| Parsons problem | prog | Keyboard-reorderable lines, distractors, indent buttons | auto (order); assisted (run) | `qti-order-interaction` (+ PCI for indentation) / `ordering` | M |
| Debugging (fix given code) | prog | python-code with a buggy starter; workbench shows a diff from the starter | human | CodeRunner with preload | S |
| Pseudocode | prog (5N2927 LO 2) | Monospace box, no Run button | human | extended-text | S |
| File upload | any | File picker, embedded in the submission | human | `qti-upload-interaction` / essay attachments | M; risky in the exam room |
| **Answer on paper** | any | "Answer on sheet A3(c)" placeholder, printed labelled sheets; marks entered in the workbench | human | none / `essay responseformat=noinline` | **S** |

**Mapping notes.**
- Moodle XML essays carry `responseformat`, `responsefieldlines`, `attachments`, `graderinfo` and `responsetemplate`, so dewmark's written types and their guidance export cleanly.
- GIFT covers only multiple choice, true/false, short answer, matching, a single missing word, numerical and essay.
- QTI 3.0 has 21 or more interaction types. Its `qti-companion-materials-info` element (calculator, rule, protractor) maps to dewmark's `reference` and `calculator` settings.
- QTI 3.0's Personal Needs and Preferences (PNP 3.0) alignment maps to accommodations.
- **No standard format has a computer-algebra answer type.** STACK and Numbas each use their own formats (Moodle XML with `type="stack"`; Numbas `.exam`).

## 4. QQI context

**Techniques named in the component specifications I checked:**

| Component | Assessment techniques | Notes |
|---|---|---|
| 5N2927 Programming and Design Principles | Skills Demonstration 70%, Examination-Theory 30% | |
| 5N18396 Maths for IT | **Assignment 100%** | The "exam" dewmark builds for this module is formally an assignment instrument, even though it is sat under exam conditions. |
| 5N1833 Mathematics (L5) | Assignment 60%, Examination-Theory 40% | Specific validation requirement: "Each candidate will be supplied with a set of Formulae and Tables at examination Calculators are available to each candidate at examination". |
| 6N3395 Mathematics (L6) | Examination-Theory 60%, Assignment 40% | Covers matrices, vectors, Venn diagrams and integration. |
| 5N2746 Biology | Examination-Theory 50%, Learner Record 25%, Skills Demonstration 25% | Requires access to a science laboratory. |

Every one of these uses the same grading bands: Pass 50–64%, Merit 65–79%, Distinction 80–100%. The specifications' definitions:
- Examination: "…within a set period of time and under clearly specified conditions."
- Skills demonstration: "a task or series of tasks that demonstrate a range of skills."
- Assignment: "an exercise carried out in response to a brief…".

dewmark fits Examination-Theory and timed, supervised skills demonstrations and assignments. Learner records, projects and collections of work belong in Moodle.

**What the QQI *Quality Assuring Assessment Guidelines for Providers* (interim 2025 edition) says:**
- For each technique the provider develops "an assessment instrument…, accompanying instructions, assessment criteria…, a marking scheme".
- Theory exams "may require responses to a range of question types, for example, objective, short answer, structured essay".
- **Records (§4.2.7)** include the learner's name, "any specific learner requirements", the assessor(s), the internal verifier(s) and external authenticator(s), dates and details of feedback, dates and results cross-referenced to the award, and the results-approval and appeal outcome. Also: "each item of assessment evidence submitted by the learner should be recorded as having been received (description, date and time)".
- **§4.2.6:** assessment records are personal data under GDPR, and submissions are kept "until appeals processes are exhausted."
- **Reasonable accommodation (§4.2.8)** can be granted by the provider without asking QQI. The listed examples are "modified presentation… e.g. enlargements", "scribes/readers", "rest periods", "adaptive equipment/software", "use of assistive technology" and "extra time".
- **Internal verification (§5.2.3)** samples scripts and checks "that marks are totalled, and percentage marks are calculated correctly" and that grades are consistent.
- **External authentication (§5.3.1)** moderates a sample and reviews the internal verification report.

**What follows for dewmark:**
- **Exam file:** add `technique`, `weighting` (the hand-built Sample already states "30% of the module (60 marks, divided by 2)"), and per-question `outcomes: [7, 8]`. The hand-built pages already list "Learning outcomes assessed", and dewmark's `topic:` is the natural place.
- **Marks export:** columns for raw mark, percentage, weighted mark and band. A learning-outcome coverage sheet.
- **Evidence received:** the finish screen shows a short receipt hash, and the workbench keeps a "received" log (file, hash, time).
- **Accommodations:** a column for any accommodations applied.
- **Marking record:** marker identity and date on each mark, and internal-verifier changes logged with a reason.
- **Authenticator pack:** the sampled scripts, the scheme, and the internal verification report.

## 5. Exam-room practicalities

- **Lockdown.** Safe Exam Browser (SEB) is a Chromium-based browser.
  - Downloads and uploads are **off by default**, and 3.9 changed the upload default to disabled.
  - The start URL is normally http or https. SEB has long allowed "full HTML5 web apps… as embedded Additional Resources… in a fully offline exam scenario."
  - For dewmark this means: the submission download and any File System Access API use must be tested inside SEB. The page must work with only localStorage plus a download. Serving the page from a laptop over local http is the SEB-friendly route.
  - `THE_EXAM_PAGE.md` §7 is right that the page should not claim to lock anything down. It should, however, ship a tested `.seb` configuration.
- **Offline.** Build-time MathML is correct. Every new library should be inlined only when its question type is used, which follows the existing rule for per-type machinery in §1 of the catalogue. The costs:
  - MathLive: about 1.1 MB including fonts.
  - JSXGraph: about 1 MB raw.
  - SymPy for Pyodide 0.27.4: a 17 MB wheel. It belongs in the **workbench**, never on the student page.
- **Crash recovery.** dewmark's design (continuous localStorage saving, an answer file, and a choice screen when copies disagree) is sound. The hand-built pages' `settrace` deadline should be adopted to soften Q8.
- **Invigilator controls.**
  - A reopen/extend code after Finish.
  - An optional **encrypted paper**: encrypt the questions at build time with WebCrypto AES-GCM and reveal the passphrase at the start of the exam. This protects a live paper copied to machines the day before. Whether `crypto.subtle` is available on `file://` in Edge, Chrome and SEB still needs checking.
  - A room or seat field.
- **Accommodations** belong on a settings screen *before* the start button:
  - Text size, font, spacing and contrast. The hand-built pages already have these, and note that they "do not change the printed PDF".
  - Read-aloud through `speechSynthesis`, which uses the operating system's voices offline on Windows.
  - MathML, so screen readers can read the maths.
  - No timer by default (Q4), which avoids conflicts with extra time.
  - The accommodation applied is written into the submission metadata, for QQI §4.2.7.

## 6. The maths input question

Handwriting and typing do different jobs. Final answers are short and structured, and typing suits them. Working needs two-dimensional layout and speed, and paper still does that better at Level 5. I recommend four tiers.

1. **Tier 0 — do now.** Keep plain text in every maths answer space and add:
   - A **live rendered preview** under the box, converting AsciiMath-style text to MathML. A small AsciiMath converter (the MIT-licensed `ASCIIMathML.js` family) is tens of KB. The preview is only a mirror; the stored answer stays text.
   - A **palette** that inserts text tokens (`sqrt()`, `^2`, `π`, `≤`, `±`, `∪`, `∩`, `∈`, `θ`, `∞`).
   - The existing conventions card.

   This answers "did I type what I meant?", which is the main failure of typed maths. Screen readers still work, stored answers stay reversible (the Q17 assumption holds), and it follows Kobel-Keller and Sangwin's recommendation.
2. **Tier 1 — do next.** A `math-expression` answer space for *final answers only*:
   - One line, preview, and STACK-style "we read this as…" echo without judging the answer.
   - An optional `form:` setting (factorised, expanded, exact).
   - In the workbench, **assisted** checking: evaluate the student's expression and the key at about 10 random points, Numbas-style (a few hundred lines of JavaScript, or reuse Numbas JME under Apache-2.0), and sort answers into "matches key", "differs" and "could not read". The marker confirms each one.
   - `numeric-answer` gains structured `accept: {tolerance | sf | dp | range, units}` in place of prose.
3. **Tier 2 — defer.** MathLive as an **opt-in editor per exam**, configured to store `getValue('ascii-math')` so the stored answer is still text. Only after a rehearsal shows students are faster with it.
4. **Handwritten working — use paper, not phones.** Photographing work with phones conflicts with phone bans, GDPR and file handling. Instead:
   - An `answer-on-paper` answer space: the page shows "Answer on sheet A4". The builder prints labelled working sheets, and the marker enters marks in the workbench, so the spreadsheet stays complete.
   - Later: sheets with a QR code for student number, exam code and question, scanned after the sitting and split automatically by the workbench (the InsperaScan model; jsQR is Apache-2.0).
   - A canvas drawing type waits until the college has stylus devices.

## 7. Recommendations

**First, for maths:**
- The Tier 0 preview and palette.
- Structured numeric `accept:`.
- `answer-on-paper`.
- Matrix and vector entry as a complete-the-table variant (6N3395).
- Truth tables through the existing table type.
- `math-expression` with assisted checking.

**First, for biology:**
- Matching.
- Ordering.
- Label-bank drop-downs on `label-the-diagram`.
- A **stimulus panel**, so a data table or experiment description stays visible beside its sub-questions.
- Numeric answers with significant figures and units (magnification, Lincoln index, percentage change).
- Punnett squares through complete-the-table.
- `answer-on-paper` for drawings.

**First, for programming:** port `fields` as `labelled-boxes`, add a `pseudocode` answer, show a diff from the starter code in the workbench, and let the workbench run hidden tests.

**Defer:** hotspots and shade-regions (M), Parsons problems (M), JSXGraph "place points" and plot-from-data (L), MathLive, canvas drawing, file upload, QTI 3.0 export.

**Leave to paper, or to Moodle:** freehand biological drawings, full graph plotting at Level 5, long handwritten proofs, lab skills demonstrations, and learner records.

## What this means for dewmark

1. **The catalogue is a good core.** The new types worth adding first are small (matching, ordering, labelled boxes, pseudocode, answer-on-paper, a stimulus panel). Each must meet the four-part rule in §4 of the catalogue.
2. **A typed-maths layer should cut across the text types** (preview, palette, "we read this as"), keeping stored answers as plain text. It is the biggest change for Josh's maths papers and costs little.
3. **Reopen Q15 as "assisted, never automatic".** Structured answer keys (tolerance, forms, hidden tests) produce suggestions in the workbench, and the marker confirms every one. The same structured keys make GIFT and Moodle XML exports mechanical.
4. **Add QQI fields to the exam file:** `technique`, `weighting` and per-question `outcomes`. The export gains percentage, band, weighted mark, learning-outcome coverage and a receipt log. The submission carries a hash and any accommodations applied.
5. **Treat the exam room as a design input:**
   - A settings-first start screen with accommodations and a preload progress bar.
   - The hand-built pages' `settrace` time limit.
   - A tested SEB profile.
   - An optional encrypted live paper.
   - One rule: every heavy library is inlined only when its question type is used, and computer algebra stays out of the student page.
6. **Before it goes into any repository, the 2027 live paper should only be described structurally, never copied.** It uses `answer` ×17, `python` ×10, `text` ×8, `fields` ×1 and `pseudo` ×1.

**Sources:**
- Numbas: [parts reference](https://docs.numbas.org.uk/en/latest/question/parts/reference.html), [mathematical expression](https://docs.numbas.org.uk/en/latest/question/parts/mathematical-expression.html), [number entry](https://docs.numbas.org.uk/en/latest/question/parts/numberentry.html), [adaptive marking](https://www.numbas.org.uk/blog/2015/07/adaptive-marking-based-on-answers-to-other-question-parts/), [delivery](https://docs.numbas.org.uk/en/latest/tutorials/deliver-to-students.html), [v9.0](https://www.numbas.org.uk/blog/2025/08/numbas-v9-0/), [licensing](https://docs.numbas.org.uk/en/latest/licensing.html)
- STACK: [inputs](https://docs.stack-assessment.org/en/Authoring/Inputs/), [equivalence reasoning](https://docs.stack-assessment.org/en/Specialist_tools/Equivalence_reasoning/)
- Möbius: [question types](https://www.digitaled.com/support/help/instructor/Content/INST-AUTHORING/Available-question-types.htm)
- MathLive: [overview](https://mathlive.io/mathfield/), [speech](https://mathlive.io/mathfield/guides/speech/)
- Kobel-Keller and Sangwin 2026: [arXiv 2605.25276](https://arxiv.org/html/2605.25276)
- Abitti: [rich-text-editor](https://github.com/digabi/rich-text-editor)
- JSXGraph: [repository](https://github.com/jsxgraph/jsxgraph)
- GeoGebra: [embedding](https://geogebra.github.io/docs/reference/en/GeoGebra_Apps_Embedding/)
- QTI 3.0: [implementation guide](https://www.imsglobal.org/spec/qti/v3p0/impl), [accessibility](https://www.1edtech.org/standards/qti/accessibility)
- Moodle: [GIFT](https://docs.moodle.org/en/GIFT_format), [Moodle XML](https://docs.moodle.org/en/Moodle_XML_format), [ordering in 4.4](https://moodledev.io/general/releases/4.4), [CodeRunner](https://docs.moodle.org/502/en/CodeRunner_question_type)
- Parsons problems: [Denny et al. 2008](https://dblp.org/rec/conf/icer/DennyLS08.html)
- Inspera: [InsperaScan](https://support.inspera.com/hc/en-us/articles/360031110972-InsperaScan-Handwritten-digital-exams)
- Safe Exam Browser: [release notes](https://safeexambrowser.org/windows/win_release_notes_en.html), [user manual](https://safeexambrowser.org/windows/win_usermanual_en.html)
- QQI: [assessment guidelines (interim 2025)](https://www.qqi.ie/sites/default/files/2021-10/quality-assuring-assessment-guidelines-for-providers-revised-2013.pdf); component specifications [5N18396](https://qsdocs.qqi.ie/sites/docs/AwardsLibraryPdf/5N18396_AwardSpecifications_English.pdf), [5N2927](https://qsdocs.qqi.ie/sites/docs/AwardsLibraryPdf/5N2927_AwardSpecifications_English.pdf), [5N2746](https://qsdocs.qqi.ie/sites/docs/AwardsLibraryPdf/5N2746_AwardSpecifications_English.pdf), [5N1833](https://qsdocs.qqi.ie/sites/docs/AwardsLibraryPdf/5N1833_AwardSpecifications_English.pdf), [6N3395](https://qsdocs.qqi.ie/sites/docs/AwardsLibraryPdf/6N3395_AwardSpecifications_English.pdf)

Scratch files (downloaded specifications and size measurements) are in `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/qtypes/`. Both repositories were left untouched.