# Kinds of exam and question in dewmark, and a registry that makes a new type cheap

*Design round, 2026-09-27. Topic: which exams and question types dewmark supports for programming, maths and biology, and the architecture that keeps each new type a small, contained piece of work. The exam file's grammar belongs to `format.md`, so keys are named here but their final syntax is not; fragments below use today's settings-block style only so they can be read. The student's screens are `student-flow.md`'s, the teacher's journey and the names lock are `architecture.md`'s, and anything involving a language model is `assistant.md`'s. Probe files are listed at the end.*

---

## 0. The recommendation on one page

1. **One folder per question type, holding every part of it.** Today a type is spread over eight functions in three files and two languages (`code.md` §8). Each type becomes a folder: a Python half (keys, checks, markup, exports), two small JavaScript halves (page: save and restore; workbench: show and suggest), its catalogue entry, an example and test fixtures. Generic tests run against every folder, so a new type arrives with its tests.
2. **The first wave adds six types and a handful of options.** New types: `labelled-boxes` (PDP's `fields`), `matching`, `ordering`, `predict-the-output`, `pseudocode`, `answer-on-paper`. The main new options: drop-down gaps, a label bank, structured `accept` rules, a maths preview and palette on any typed answer, and unmarked rough work. A stimulus panel shared by several parts is a display block, not a type.
3. **Typed maths stays plain text,** with a typeset "Reads as" line under the box and a symbol palette. Working that needs a page goes on labelled paper sheets, marked in the workbench. MathLive waits; photographs are ruled out.
4. **Hidden tests live in the marking scheme and run only in the workbench,** in the three shapes the PDP papers need: call a named function, run a program with typed input, check values after a run. Results are evidence beside the model answer's, never a mark.
5. **"Assisted, never automatic."** Rules the teacher wrote (a key, a tolerance, a test) group answers and state facts; for closed types they also propose a mark the marker confirms. The record says how each mark was made. No language model sits inside a type. Q15 is reopened on these terms.
6. **Practice papers may show the paper's answer on request, beside the student's, with no verdict** (dewlab's decision 7.235). Keys go only into practice and sample papers, never into any build of an exam paper.
7. **QQI fields are exam data** (`technique`, `weighting`, `outcomes` per question), and the marks export gains percentage, weighted mark, band, an outcomes sheet, a received log and accommodations.

The build order (§10) starts by moving the ten existing types into the registry with byte-identical output. Section 11 lists the decisions for Josh.

---

## 1. What the papers ask

Before choosing types, I counted what the nine papers in hand use.

| Paper | Answer spaces as written | What they are once typed properly |
|---|---|---|
| PDP Sample, Practice 1, Practice 2 (one skeleton, `pdp-pages.md` §3.5) | 5 `answer`, 11 `python` (1 optional), 1 `fields` (6 rows), 1 `text` display | 4 short written; 1 written answer with a pre-filled scaffold ("Permitted: / Not permitted: / My fixed versions:"); 10 code, 7 of which could carry hidden checks as worded; 1 rough-work cell; 1 labelled-boxes. The Sample's 1A(iii), "Put the following in order, from the oldest to the newest", is an ordering question in a text box. |
| PDP Exam 2027 | 17 `answer`, 10 `python`, 1 `fields` (7 rows), 8 `text`, 1 `pseudo` | 12 written; **5 `answer` spaces are scaffolds of labelled lines** ("Line 1: … Line 12:" in 1(a), 1(c), 1(e), 3(d); "(i) county:" in 3(b)); 8 code; 2 rough-work cells; 1 labelled-boxes. 1(a) and 1(e) are predict-the-output questions. |
| dewmark maths sample (5N18396) | 50 short, 15 long, 2 table, 3 sketch | By my reading, about 30 of the 50 short answers end in a number or exact value (`3/13`, `2*sqrt(13)`, `95.9°`), about 9 in an expression (`(x-4)(x+2)`), about 10 in words. Almost all want working in the same box. |
| dewmark biology, mixed, essay and hvit samples | the ten existing types | Fit the catalogue. The biology paper has no matching, ordering or label bank because dewmark has none. |

Two lessons follow. The PDP scaffolds show an unmet need: many short answers keyed by a label. In one text box the student can delete "Line 7:", and nothing can hold a per-line key. And in maths the gain comes from how the box behaves, not from new types: final values deserve their own box, and every box should show its maths.

### 1.1 Kinds of exam

| Kind | QQI technique (`exam-types.md` §4) | In dewmark? |
|---|---|---|
| Theory examination, mixed types (PDP written paper, biology) | Examination-Theory: 5N2927 30%, 5N2746 50%, 6N3395 60%, 5N1833 40% | Yes: the main case |
| Timed programming practical (hvit) | Skills Demonstration, when timed and supervised | Yes, with the Python engine |
| Timed assignment under exam conditions (maths sample) | Assignment: 5N18396 is 100% | Yes; the export says Assignment |
| Practice and sample papers | formative | Yes, with self-check (§7) |
| Typed paper with some parts on paper sheets | any of the above | Yes, through `answer-on-paper` |
| Learner record, project, collection of work, lab skills, take-home work | the rest | No: Moodle and the lab (§9) |

---

## 2. The type registry

### 2.1 Where a type lives today

Adding a type now touches eight places (`code.md` §8):

| Where | Function | Lines |
|---|---|---|
| `build_exam.py` | `check_answer` (one `elif` per type) | 433–557 |
| | `render_answer_space` | 734–879 |
| | `render_model_block` (answer key) | 882–952 |
| | `leak_fragments` | 1187–1222 |
| `assets/exam-page.js` | `collectAnswer`, `applyAnswer` | 33–115, 117–170 |
| `workbench/index.html` | `renderStudentAnswer`, `renderModel` | 436–520, 522–570 |

The model-answer display is written twice, in Python and JavaScript. Nothing records what a stored answer looks like, so page and workbench agree by coincidence. And the leak check strips every `<script>` before searching (`code.md` §1, stage 5), so the embedded data block, which `build_exam.py:1000` says is covered, is not.

### 2.2 The shape

A **registry** is a list the tools look types up in. Each entry is one folder:

```
dewmark/types/numeric-answer/
  type.py            builder half: keys, checks, student/print/key markup, exports
  page.js, page.css  exam-page half, inlined only when a paper uses this type
  marker.js          workbench half: view, one-line summary, suggestions
  README.md          the catalogue entry (purpose, student sees, teacher writes, marking)
  example.exam.md    the studio's Insert snippet, and the tests' input
  fixtures/*.json    sample stored answers: typical, blank, odd input
```

The builder half, in outline (it runs unchanged on the command line and inside the studio's Python, `architecture.md` §4):

```python
class NumericAnswer(QuestionType):
    name = "numeric-answer"                # what teachers write; never renamed
    since_format = 1
    features = ("working-box", "maths-preview", "accept-number")   # shared parts, below
    keys = {                               # everything the exam file may give; any other key is refused
        "boxes":       Key(list, required=True, each={"label": str, "unit_box": bool}),
        "working_box": Key(bool, default=True),
        "units":       Key(list, of=str),
    }
    secret = ("boxes[].expected", "boxes[].accept", "model_answer")   # stripped and leak-checked
    stored = {"boxes": {"<box>": str}, "units": {"<box>": str}, "working": str}
    suggestion = "evidence"                # "propose" | "evidence" | "none", see §2.5

    def inner_names(self, a): ...          # "1", "2": recorded by the names lock
    def check(self, a, problems): ...      # builder messages, in the builder's voice
    def student_html(self, a, ctx): ...    # exam and practice page
    def print_html(self, a, value, ctx): ...   # answer file, graded paper, printout
    def key_html(self, a, ctx): ...        # answer key and marking scheme
    def practice_key(self, a): ...         # what a practice page may carry, or None
    def export(self, a, fmt): ...          # "gift", "moodle-xml", "qti3"; or NotExportable(reason)
```

The two JavaScript halves:

```js
// page.js
export default {
  type: "numeric-answer",
  collect(root)        {},  // -> {boxes: {"1": "75"}, units: {"1": "µm"}, working: "…"} or null
  restore(root, value) {},  // puts a saved value back without scheduling a save
  answered(value)      {},  // drives the side panel's progress and the finish checks
  reveal(root, key)    {},  // practice only: the paper's answer beside the student's
};
// marker.js
export default {
  type: "numeric-answer",
  view(value, spec)    {},  // the answer as the marker reads it
  summary(value)       {},  // one line for by-question lists and the spreadsheet: "75 µm"
  suggest(value, spec) {},  // -> {group, facts: [...], proposal: null | marks}
};
```

The builder writes a small **type manifest** (a list, in JSON, a plain-text data format, of each type's name, format version and stored shape) into every page, scheme and workbench, which refuse a type or shape they do not know (`QUESTION_TYPES_AND_MARKING.md` §4).

**Features** are parts several types share, written once: a working box; the maths preview and palette (§4); `accept` rules (accepted spellings; tolerance, significant figures, units); starter text; "on paper instead" (§4.4); rough work (`marks: 0`, labelled "Rough work · not marked", `student-flow.md` §7.3). Giving `labelled-boxes` the maths preview is one word in its `features`.

**Stored answers are plain data,** never HTML (the PDP pages re-inject `output_html`, `pdp-pages.md` §8.8), and each records `touched`, so "not attempted" and "left blank" finally differ (`QUESTION_TYPES_AND_MARKING.md` §2.4).

**Inner names are part of the names contract.** A matching row, a label number, a table cell and a multiple-choice option each hold part of an answer, so each type declares them through `inner_names`, and the names lock (`architecture.md` §6) records them. Options are shown lettered A–D and stored by letter, and the lock records each letter's text; that ends the "correct by position" hazard (`design-docs.md` §9), since reordering after a sitting is refused with a message naming the answers it would misplace. Table cells stay positional, so the lock records the table's shape. Matching rows and ordering items are keyed by their text, and a teacher who fixes a typo in one after a sitting is told which stored answers it would orphan.

### 2.3 What a type gets for free

Every folder runs through the same tests (Python tests and one browser test file): the example builds; no `secret` value appears anywhere in a student or practice page, **the embedded data block included**, closing the gap above; every fixture matches `stored`; a **round trip** types each fixture into the rendered controls, collects, reloads, restores and collects again, and must get the same value; `print_html` shows every stored string; the fixture can be entered by keyboard alone and passes an automated accessibility scan; and each export is valid, or the type says why it cannot export.

The README is the type's catalogue entry and the example is the studio's Insert snippet (`architecture.md` §3.2), so documentation, snippet and test input cannot drift apart. The assistant's conversion task reads the same manifest (`assistant.md`).

**Cost.** Moving the ten types in is about a week, as a pure refactor checked by byte-identical sample builds. After that a small type (matching, ordering) is two or three days; one with new machinery (predict-the-output) about a week.

### 2.4 One type, all the way through: `numeric-answer`

A biology part: *"A drawing of a cell is 30 mm across at a magnification of ×400. Calculate the real width of the cell in micrometres, to 2 significant figures."*

**The teacher writes** (syntax per `format.md`):

```
name: a5.size
type: numeric-answer
marks: 4
boxes:
  - label: "real width ="
    expected: 75
    accept: {sf: 2, tolerance: 0}
    unit_box: yes
units: [µm, um, micrometre, micrometres]
working_box: yes
```

with a marking block: "2 marks for dividing the drawing size by the magnification, shown in the working; 1 for converting to micrometres; 1 for 75 µm to 2 significant figures".

**The builder checks**, in its usual voice (sf is significant figures): "`a5.size`: `sf: 2`, but the expected value 75.0 has 3 significant figures. Write 75, or change `sf`." "The expected value `75 µm` is not a number. Put the number in `expected` and the unit in `units`." "`a5.size` has a key `tolerence`. Did you mean `tolerance`, inside `accept`?" (today unknown keys pass silently, `code.md` §1).

**The student sees** the label, a value box, a unit box, and a working box with the maths preview (§4). The page carries no expected value, sf or units list.

**Stored:**
```json
{"boxes": {"1": "75"}, "units": {"1": "µm"},
 "working": "30 / 400 = 0.075 mm\n0.075 × 1000 = 75", "touched": true}
```

**Practice** (only on a practice or sample paper): after the student has typed something, **Show the paper's answer** gives "The paper's answer: 75 µm, to 2 significant figures. Your answer: 75 µm." No tick, no cross, no score (§7).

**The workbench** shows value, unit and working, typeset as the student saw it. `suggest` reads the value with the shared maths reader (§4.3) and states facts: "75 matches the key", "2 significant figures, as asked", "µm is an accepted unit". The scheme gives marks for method, so no mark is proposed. The by-question view groups the class ("matches the key: 18", "differs: 4, of which 0.075 three times", "could not read: 1"), so the three students who forgot to convert are marked side by side and alike.

**Print** (answer file, graded paper): "real width = 75 µm", then the working as typed, each line followed by its typeset form.

**Exports.** GIFT and Moodle XML are the formats Moodle imports questions from; QTI is the international standard for exchanging them.

| Format | Mapping | Lost |
|---|---|---|
| GIFT | `{#75:0}` | units, sf, working |
| Moodle XML | `numerical`: answer 75, tolerance 0, units µm and um | the sf rule (stated in the question); the working (a separate `essay`) |
| QTI 3.0 (later) | text entry, float, `qti-equal tolerance-mode="exact"` | the sf rule, unless `qti-equal-rounded` is used |

### 2.5 Assisted, never automatic

Q15 in `OPEN_QUESTIONS.md` assumed "no automatic checking of any kind", while the catalogue promises a multiple-choice mark confirmed "with one keypress", with nothing proposed to confirm (`design-docs.md` §9, item 1). Three levels, declared per type, settle it:

| Level | Types | What the marker sees | What the marker does |
|---|---|---|---|
| **propose** | multiple-choice, matching, ordering, label bank, drop-down gaps, and predict-the-output when the scheme gives marks per line | A proposed mark from the key, with the facts ("chose C; the key is C") | Confirms (Enter), or types another mark. In the by-question view, confirms a group ("2 marks for the 21 answers that chose C"), with every answer in the group listed. |
| **evidence** | numeric-answer, typed gaps and labels with accept lists, labelled-boxes with expected values, complete-the-table, describe-a-sketch, python-code with checks, math-expression (later) | Facts and a group ("matches the key", "differs from the key", "could not read"); no mark filled in | Enters the mark, reading the working or code |
| **none** | short and long written, essay, pseudocode, answer-on-paper, rough work | Identical answers collapsed with a count, otherwise nothing | Marks as today |

Rules that keep this safe:

- **Every suggestion comes from a rule the teacher wrote**: a key, a tolerance, an accepted spelling, a test. Such rules are not "AI" under the AI Act (Recital 12, `local-llm.md` §5), so they carry none of the high-risk duties mark-suggesting models would from December 2027. No type calls a language model; the optional assistant (`assistant.md`) never fills or proposes a mark.
- **Words, not verdicts:** "matches the key", "differs from the key", "could not read"; never "correct" or "wrong", because an equivalent answer the rule missed must not look like a mistake. "Could not read" always goes to a person.
- **The record says how each mark was made:** `{mark, marker, at, how: "typed" | "confirmed" | "group-confirmed", proposal}`, so internal verification can sample group-confirmed marks first and an appeal can see what was proposed.
- **Suggestions are computed in the workbench from the scheme** each time; never stored in the submission, never computed on the exam page.

---

## 3. The first wave

The full list, existing and new. "Stored" is the answer's value in the answer file.

| Type | Subjects | The student… | Stored | Marked | Status |
|---|---|---|---|---|---|
| `multiple-choice` | all | picks one lettered option (radio) or several (checkboxes) | `{chosen: ["C"]}` | propose; for several, a partial-credit rule in the scheme | Exists; add letters and the scoring rule |
| `fill-in-the-blank` | all | types into gaps, or picks from a drop-down gap written `{mitochondrion\|nucleus\|ribosome}` | `{blanks: {"1": "nucleus"}}` | typed: evidence with accepted spellings; drop-down: propose | Exists; add drop-downs (dewlab's shared `{a\|b\|c}` convention, first item the answer; the page lists choices alphabetically so position gives nothing away) and accept lists |
| `short-written-answer`, `long-written-answer` | all | writes in a growing box, with optional starter text and maths preview | `{text}` | none; points list typical | Exists; add `starter_text`, maths preview, "on paper instead" |
| `essay` | all | writes with a word count and a planning box | `{text, planning}` | none; criteria grid | Exists |
| `numeric-answer` | maths, bio | enters final values (with optional unit box) and working | `{boxes, units, working}` | evidence | Exists; add `accept` (§2.4) |
| `complete-the-table` | all | fills cells; may add rows where the table allows | `{cells: {"r2c1": "…"}, rows_added}` | evidence per cell | Exists; add per-column `accept`, `add_rows`, `grid` (a matrix with no headers) |
| `describe-a-sketch` | maths, bio | chooses a shape, types feature values | `{shape, features}` | evidence | Exists |
| `label-the-diagram` | bio | types a label per numbered pointer, or picks it from a bank | `{labels: {"3": "nucleus"}}` | typed: evidence; bank: propose | Exists; add `bank` |
| `python-code` | prog | writes and runs code, answers `input()` in the output, can Stop | `{code, outputs, last_run, run_matches_code}` | evidence when the scheme has checks, otherwise none | Exists; add checks, diff from starter, rough work, per-answer time limit (§5) |
| **`labelled-boxes`** | prog, all | fills one short box per label ("Function name", "Line 4") | `{boxes: {"Function name": "shout_first_word"}}` | none, or evidence where a box has `expected` | New: PDP `fields` |
| **`matching`** | bio, prog | picks from a drop-down beside each row | `{rows: {"nucleus": "controls the cell's activities"}}` | propose | New |
| **`ordering`** | bio, prog | reorders a list with Move up and Move down | `{order: ["machine code", "assembly language", "FORTRAN", "Python"]}` | propose: exact order, or one mark per correct neighbouring pair | New |
| **`predict-the-output`** | prog | reads a numbered listing and writes what chosen lines print or evaluate to | `{lines: {"10": "3", "11": "0"}}` | propose or evidence | New |
| **`pseudocode`** | prog | writes in a monospace editor with indenting and line numbers, and no Run | `{text}` | none | New |
| **`answer-on-paper`** | all | sees "Answer on a paper sheet, labelled 3(c)", ticks "I used paper for this", gives the number of sheets | `{on_paper: true, sheets: 2}` | none; mark entered in the workbench | New |

**Display blocks** come in the same wave, from `format.md`: code listings with line numbers and an optional first number (PDP's `text` and `py` with `start=`), pseudocode listings (PDP's `pseudo`), and the stimulus panel (§6.1).

**PDP parity** also needs marks shared by several spaces in one part (4B's function and tests cells, `pdp-pages.md` §9.3 gap 3). The syntax is `format.md`'s; the registry's part is a workbench that shows several spaces under one mark. With that, the four PDP papers convert without losing structure. The 2027 paper becomes 12 written answers, 3 labelled-boxes (2(a), 3(b), 3(d)), 2 predict-the-output (1(a), 1(e)), 1(c) split into a labelled-boxes pair and a predict-the-output listing sharing 3 marks, 8 code answers and 2 rough-work cells. The Sample's 1A(iii) becomes `ordering`; its 1B can stay written with starter text or become `matching` plus a box, which is the teacher's choice, not the converter's.

**By subject:**
- **Programming:** python-code with checks, labelled-boxes, predict-the-output, pseudocode, listings, rough work; multiple-choice, matching and ordering for theory.
- **Maths:** typed answers with preview and palette, numeric-answer with exact values, complete-the-table (value and truth tables, matrices for 6N3395), describe-a-sketch, answer-on-paper.
- **Biology:** stimulus panel, matching, ordering, label bank, drop-down gaps, numeric with significant figures and units, results tables and Punnett squares, answer-on-paper for drawings.

---

## 4. Typed maths

### 4.1 The four options

| | A. Plain text, preview, palette | B. MathLive editor | C. Answer on paper | D. Photograph the working |
|---|---|---|---|---|
| The student | types `x^2 - 2x - 8` and sees x² − 2x − 8 typeset under the box | types into a typeset field or taps a virtual keyboard | writes on a labelled sheet | photographs pages with a phone and uploads them |
| Stored | the text as typed | LaTeX or ASCII from the editor, not always what the student saw | "on paper: 2 sheets" | images in the answer file |
| Speed | keyboard speed; palette optional | mouse and keyboard mixed, which "interrupts the train of thought" (Kobel-Keller and Sangwin 2026, `exam-types.md` §2) | fastest for 2-D working | slow |
| Accessibility | screen readers read the text; the preview is MathML (maths markup screen readers read), in the student's font | speech output unverified with our students; new interface under pressure | excludes students who need a keyboard | poor |
| Offline weight | tens of KB | about 1.1 MB with fonts | none | phones need a network |
| Exam room | nothing new | a new library | printing and collecting sheets | phones banned; personal data on personal devices; uploads off in Safe Exam Browser |
| Reversible | yes (Q17's assumption holds) | partly | yes | no |

**Recommendation: A for everything typed, C for working that needs a page.** B waits until a rehearsal shows students are faster with it, and would then be an opt-in per paper that still stores text. D is ruled out; if sheets are ever scanned, the college scans them (§4.4).

### 4.2 What the student sees and types

```
(b) Find the inverse of f. Show your working.                          (2)

 √   x²   xⁿ   a/b   π   ≤  ≥  ≠   ±   °   θ   ∞          Typing maths ▸
┌──────────────────────────────────────────────────────────────────────┐
│ y = 2x + 3                                                           │
│ y - 3 = 2x, so x = (y-3)/2                                           │
│ inverse: (x-3)/2                                                     │
└──────────────────────────────────────────────────────────────────────┘
 Reads as   y = 2x + 3
            y − 3 = 2x, so x = (y − 3)⁄2        (the fraction typeset)
            inverse: (x − 3)⁄2
```

- **The box is an ordinary text box.** Nothing typed is changed or corrected.
- **"Reads as"** typesets each line after a short pause. Known functions (`sqrt`, `sin`, `log`) become functions, single letters variables, and other words ("so", "inverse") stay plain words, so working in sentences reads naturally. It is a mirror, never a judge: `1/2x` shows ½x, and a student who meant 1/(2x) sees it and adds brackets. This is STACK's "student must verify" (`exam-types.md` §2) without blocking anything.
- **The palette** inserts single symbols as themselves (`π`, `≤`, `±`, `°`, `θ`, `∞`, `∪`, `∈`) and structures as text with the cursor inside (`sqrt(|)`, `^(|)`, `(|)/()`). Each has a typed equivalent on the "Typing maths" card the maths sample already carries (`maths-for-it-5n18396.exam.md:18-37`). It is reachable by Tab and never required.
- **Screen readers:** the preview is not a live region (every keystroke announced would be unbearable); the student can move to it and hear it.
- **Where:** any control with the `maths-preview` feature (written answers, working boxes, labelled boxes, table cells), switched on per paper with a per-answer override.

### 4.3 One maths reader, used in four places

The preview must read text exactly as the workbench's checks will, or the student sees one meaning while the marker's evidence uses another. So dewmark writes **one small maths reader** in JavaScript, used by the calculator, the preview, the workbench's reading of final values and, later, the expression checker. It starts from the calculator's parser (`assets/exam-page.js:926-996`), which already reads `sqrt`, `pi`, powers and degree trigonometry without ever running the typed text as code.

I ran that parser over 26 final answers written the way the maths sample's model answers are (probe `calc.js`). It read 18, including `2*sqrt(13)`, `3/13`, `(1/2)^8` and `5.0 × 10^2`. It failed on 8: `2sqrt(13)` and `2√13` (implied multiplication), `10,000`, `95.9°`, `22.5 cm²`, `5e2`, and `x = 4` (a leading label). Each is a small, testable addition: units and degree signs become their own fact, and a comma counts as a thousands separator only between groups of three digits.

**Cost:** about two weeks for reader, preview and palette, with one table of test strings shared by the page and workbench tests. An existing AsciiMath converter (a plain-text maths notation with a ready-made renderer) would give a preview faster, but two readers that can disagree.

### 4.4 Answer on paper, and "on paper instead"

`answer-on-paper` is for parts the teacher puts on paper: long proofs, constructions, a biological drawing, a graph plotted from data. The page shows "Answer on a paper sheet. Write your name, student number and 3(c) at the top"; the student ticks **I used paper for this part** and gives the number of sheets. Issue prints **labelled sheets** (paper code, fingerprint, part label, name and number boxes). The workbench shows "on paper: 2 sheets" and takes the mark there, so the spreadsheet stays complete and the received log records the sheets (QQI §4.2.7).

**"On paper instead"** (`paper_allowed: yes`) adds the same tick box to a typed part, for students who find typing maths slower or have that accommodation. Small cost; real fairness.

**Later:** sheets with a QR code (a printed square code) for paper, part and student, scanned by the college and split by the workbench, as Inspera does (`exam-types.md` §6).

### 4.5 Next: final answers as expressions

`math-expression` follows the first wave: a one-line box for a final algebraic answer, with "Reads as". The workbench evaluates the student's expression and the key at about ten random values of the variables, as Numbas does, skipping points where either is undefined, and groups answers as "equivalent to the key", "not equivalent" or "could not read". An optional `form: factorised | expanded | exact` adds a fact ("equivalent, but not factorised"). The maths sample's `a3.factors`, `a2.inverse` and `b3.power` are first users. Level: evidence, since the form often carries marks.

---

## 5. Programming

**Running code.** The engine is `student-flow.md` §7.4's: the CodeMirror 6 code editor, `input()` as a line in the output, Stop, and a two-layer time limit that `except Exception` cannot swallow. The type adds a per-answer `time_limit_seconds` (a pandas question may need 30, not the default 10) and an `input` record in the outputs, so the marker sees what the student typed in the run that produced the output:

```json
{"code": "age_text = input('Age? ')\n…",
 "outputs": [{"kind": "stdout", "text": "Age? "}, {"kind": "input", "text": "17"},
             {"kind": "stdout", "text": "You need a junior ticket, which costs €6.\n"}],
 "last_run": "2026-10-20T10:14:03Z", "run_matches_code": true}
```

Output is capped (`student-flow.md` §7.2), so a runaway `print` loop cannot stop the saving.

**Hidden checks** are written in the marking block, so they are secret like any key and never reach the exam page. Three shapes cover the PDP papers:

```
checks:
  - call: longer_word("cat", "horse")          # a named function (Sample 4B(i))
  - call: longer_word("dog", "cat")            # equal lengths: the first string
  - run: {input: ["abc"]}                      # a whole program with typed input (2A)
    contains: ["whole number"]
  - run: {input: ["17"]}
    contains: ["junior", "6"]
  - after: [a == 17, whole_share == 3, leftover == 2]   # values after the run (1C)
```

A `call` or `after` check is compared with the same check run on `model_answer_code`, in the shape of dewlab's `compare()` (`dewlab-runtime.md` §3), unless it gives its own `expect`. A `run` check looks for words in the output, because students' prompts differ. The workbench shows a table (check, student's result, model's result, same or different) and a summary ("4 of 5 checks give the same result as the model answer"). The by-question view groups students by *which* checks differ, so the six who all fail the equal-length case are judged together.

Why this is safe: checks run in the workbench's Python Worker (a background process with its own copy of Python), on the same version of Pyodide (Python compiled to run in a browser) the paper was issued with. Each check starts from a fresh copy of the student's program state, with its own time limit ("asked for more input than the check provides" when input runs out). Student code never runs on the teacher's page itself, the Worker has no network access under the workbench's content policy, and nothing runs until the marker presses **Run the checks**.

Checks need names the question fixes. Every function in the Sample and both practice papers is named (`longer_word`, `count_letter`, `both_even`, `fill_with_dots`), so 7 of their 10 marked code spaces can carry checks; 1D ("comment each line") and the two "your tests" cells are for a person. The 2027 paper's 2(c) lets the student choose the name, so the builder warns: "`q2.c` has a `call` check on `circumference`, but the question never says `circumference`."

**Diff from the starter.** Where the starter code is the task (2027's 2(b) rewrite, the Sample's 1D), the workbench highlights what the student changed.

**`predict-the-output`.** The numbered, read-only listing is part of the answer space; `ask` names the lines that get a box (`each-print`, listed lines, or `evaluate` for 1(a)'s "what does each expression give, where x = 4 and y = 9"). Expected values are written in the file; the studio's **Fill in the answers by running this code** writes them there for the teacher to check, so the command-line builder needs no Python engine. Comparison trims line-end spaces only, since `True` and `true` differ. **A nuance:** in a paper with code cells, a student can type the listing into a rough-work cell and run it, as the 2027 paper allows today. Accept it and say so in the instructions, or later put reading questions in a section without Run.

**Trace tables** use `complete-the-table` with `add_rows: yes` (columns such as `n`, `n % 5 == 0`, `output`), since how often the loop runs is part of the answer. Keep the loops short.

**`pseudocode`** is CodeMirror with no language mode, Run or suggestions: line numbers, Tab to indent, Escape-then-Tab to leave. It serves 5N2927's outcome 6 ("pseudo-code, storage and control structures") and is marked by a person.

**Later:** `parsons-problem` (put given lines in order, with decoys and indent buttons), built on `ordering`'s keyboard controls, once ordering has been used in a sitting (`exam-types.md` §7).

---

## 6. Biology

### 6.1 The stimulus panel

Biology parts share material: a results table, a method, a graph, a food web. A **stimulus** is a display block its parts refer to (syntax from `format.md`). On a wide screen it stays pinned beside its parts while the student scrolls; on a narrow screen or at large text sizes, each part gets a **Show Table 1** button that opens it above the part and moves focus there. Tables have real headers and figures need descriptions. It prints once, before its parts, and the workbench shows it once per question. It stores nothing, so it is not a type. Cost: small, mostly layout and print styles.

### 6.2 Label the diagram, with a bank

`bank: [cell wall, cell membrane, nucleus, chloroplast, vacuole, mitochondrion, ribosome]` turns each pointer's box into a drop-down. The bank may hold more labels than pointers; the builder refuses one that lacks an expected label. The label's text is stored, so the bank's order does not matter. Level: propose. The typed version stays, with `accept` lists ("cell membrane", "plasma membrane") and the evidence level.

Drop-downs, not dragging, because a native drop-down works with a keyboard, a screen reader and a touchscreen, and prints as a list. Dragging can come later as a second route, never the only one; hotspots wait (§9).

### 6.3 Matching

Rows, each with a drop-down of shared choices: term to definition, organelle to function. `reuse: yes` lets a choice serve several rows, which gives "classify these" questions: "legal" or "not legal" for each of PDP 3(b)'s six names, "true" or "false" for each statement. More choices than rows stops the last row being answered by elimination. Stored by row text; propose, one mark per row by default; exports cleanly to Moodle and GIFT matching.

### 6.4 Ordering

The teacher writes the items in the correct order. The builder shows them in a fixed starting order derived from the answer's name, the same for every student (so print and appeals refer to one layout), with no item in its place and no neighbouring pair correct. Untouched means "not attempted", and the side panel says "not moved yet". **Move up** and **Move down** buttons announce "Prophase, now 2nd of 4". Scoring: `exact`, or `pairs` (one mark per correct neighbouring pair). Uses: stages of mitosis, the route of food through the gut, the steps of a method, PDP's "oldest to newest".

### 6.5 Numbers, significant figures and units

Magnification, the Lincoln index (estimating a population from two catches), percentage change and rates all use `numeric-answer`'s `accept` (§2.4). Significant figures are counted from the text typed, not the number: "0.0750" has 3, and for "500" the fact says "1 to 3" rather than guessing. Units are matched against the teacher's spellings, without conversion ("mm is not one of the accepted units"); the marker decides what that costs.

### 6.6 Data tables

`complete-the-table` covers results tables (per-column `accept` such as `{tolerance: 0.1}`), Punnett squares (alternatives per cell, `Tt` and `tT`) and "complete the key" tables. The biology sample's `a4.table` fits as written.

### 6.7 What stays on paper

A drawing from a specimen and plotting a graph from data at Level 5 (axes, scale, points, line of best fit) use `answer-on-paper`; `describe-a-sketch` stays the typed way to ask about a graph's shape. Bench work and the learner record (5N2746's two 25% parts) belong to the lab and Moodle (§9).

---

## 7. Practice and exam

`student-flow.md` §10 leaves self-checking in practice papers to this design.

**What self-check looks like.** Where the type allows it, a **Show the paper's answer** button appears once the student has answered. It shows the paper's answer beside the student's, and "You gave the same as the paper" when they match. Nothing is red or green or scored, and the student can change the answer and look again. This is dewlab's rule since 7.235 ("a question shows the page's answer only when the reader asks, beside their own"), so tutorials and practice papers share one manner.

| Type | In a practice paper |
|---|---|
| multiple-choice, matching, ordering, label bank, drop-down gaps | The paper's choice beside the student's |
| typed gaps and labels, labelled-boxes with `expected`, predict-the-output | The paper's words beside the student's |
| numeric-answer, complete-the-table, describe-a-sketch | The paper's values, units and sf beside the student's; working is untouched |
| short and long written, essay | The model answer and the scheme's points, if the teacher sets `practice_reveal: all` (default: closed types only) |
| python-code | **Try the paper's checks** runs the practice copy of the checks on the page and shows the student's results beside the model answer's, dewlab's `compare()` in exam form. The model code appears on request, if the teacher allows it |
| pseudocode, answer-on-paper, rough work | Nothing |

**Why it is safe.**
1. **Keys go only into papers that are themselves practice or sample papers.** The practice variant of an exam paper keeps its hints but gets no keys, since it would otherwise be the answer key in the page's source. To reuse a sat exam for revision, the studio's **Make a practice copy** gives it a new exam code and `kind: practice`.
2. Each type's `practice_key` names what a practice page may carry; the leak check applies the rest of `secret` to every build.
3. A practice answer file cannot pass as an exam's: variant and fingerprint differ (`architecture.md` §6).
4. A student reading the page's source can find the keys. With no marks at stake that is acceptable, the same trade dewlab's 7.179 names.
5. The answer file records `revealed: ["a5.size", …]`, so a teacher looking at practice work knows what was checked.

---

## 8. QQI fields and the marks export

**In the exam file** (keys named, syntax per `format.md`; `weighting` is also in `student-flow.md` §11.1):

| Key | Level | Example | Used for |
|---|---|---|---|
| `technique` | paper | `Examination-Theory` (or Skills Demonstration, Assignment) | export header; records |
| `weighting` | paper | `30%` | weighted mark column; cover page |
| `module`, `module_code` | paper | Programming and Design Principles, 5N2927 | every export; file names |
| `outcomes` | paper | `{1: "Demonstrate an understanding of the historical development…", 6: "…pseudo-code…", 7: …}` | outcomes sheet; the list the PDP Sample already prints |
| `outcomes` | question or part | `[6, 7]` | which outcomes each mark counts towards |

The builder refuses an outcome tag the paper does not list, and warns when a listed outcome is never assessed ("Outcome 3 is listed, but no question is tagged with it").

**The marks export** (`marks.xlsx`, `architecture.md` §3.6):

| Sheet | Columns |
|---|---|
| Results | learner number, name, one column per question (and per part when asked), section totals, raw total out of the paper's marks, percentage, weighted mark (raw × weighting ÷ total: 60 marks at 30% gives raw ÷ 2, as the PDP Sample states), band, accommodations, status (marked, not handed in, on-paper sheets awaited) |
| Learning outcomes | per learner and outcome: marks gained and available. With "answer any N", available marks differ by student, so both are shown |
| Columns explained | each column's name, marks, outcome tags and question wording, generated from the registry's `summary` and the paper |
| Received | file, receipt code, time, fingerprint match, paper sheets received |
| Marking log | each mark: marker, time, how (typed, confirmed, group-confirmed), and any internal verifier's change with its reason |

Two cautions. The **band** (Pass 50–64%, Merit 65–79%, Distinction 80–100%) belongs to the whole component, which may combine techniques (5N2927 is 30% exam, 70% skills demonstration), so the column is headed "band for this paper alone" and the component grade stays in the college's records. The wording below 50% and the rounding rule should come from the college's results template, which `architecture.md` §8 already asks Josh for.

---

## 9. What waits, and what stays on paper or in Moodle

| Item | Decision | Why | What would change it |
|---|---|---|---|
| `math-expression` | Next (T7) | Needs the maths reader first | — |
| MathLive editor | Wait | 1.1 MB; mixes mouse and keyboard; untested with our students | A rehearsal where students are faster with it |
| `parsons-problem` | Wait | Needs ordering's controls proved | Ordering used in a sitting |
| Hotspots; shading Venn regions | Wait | Needs a keyboard route and region authoring | A paper that needs them |
| Placing points, plotting (JSXGraph) | Wait | About 1 MB; coordinate boxes already give the keyboard route | A Level 6 paper where plotting is the skill |
| Freehand drawing on screen | Paper | Unfair without stylus devices (Q9) | College stylus devices |
| File upload; photographs of working | No | Off in Safe Exam Browser; phones, personal data, unequal cameras | — |
| Scanned QR-labelled sheets | Later | Worth it once paper parts are common | Paper parts in several papers |
| Per-student shuffled options or numbers | No, for exams | One layout for print, moderation and appeals | — |
| Marks carried forward from an earlier wrong answer, by machine | Wait | The guidance already tells the marker | math-expression in use |
| `sql-query` answers | Wait | hvit uses Python with sqlite | A database paper |
| GIFT and Moodle XML export | T7 | Structured keys make it mechanical; useful for Moodle practice quizzes | — |
| QTI 3.0 export | Later | Large; no consumer yet | A request |
| A language model inside a type | No | Marks come from teachers' rules; models are `assistant.md`'s | — |
| Learner records, projects, collections of work, take-home work, lab skills | Moodle and the lab | Not timed and supervised; Moodle already handles them | — |

---

## 10. The order to build

Each step ships on its own and ends with a check. Steps T0–T1 fit `architecture.md` §7's steps 2–3; T2 goes with its step 5.

| Step | Delivers | Done when |
|---|---|---|
| **T0. Registry, no change in behaviour** | The ten types in folders; manifest; stored shapes; `touched`; secret keys drive the leak check, data block included; unknown keys refused; inner names in the lock; generic tests | Five samples build byte-identically; a toy type in one folder passes every generic test |
| **T1. PDP parity** | `labelled-boxes`, `pseudocode`, rough work, starter text, listings, shared part marks (`format.md`); QQI keys | All four PDP papers convert, build and are sat as practice |
| **T2. Assisted marking** | The three levels; group confirm; "how" in the record; lettered options; hidden checks in the Worker; diff from starter; §8's export sheets | A mock marking of the PDP Sample (ten test submissions), timed against hand marking, every proposal visible in the log |
| **T3. Maths** | Maths reader, preview, palette; numeric `accept`; `answer-on-paper` with sheets; "on paper instead"; `grid` | The maths sample, re-typed, is sat in rehearsal and markers can read every typed answer |
| **T4. Biology** | Stimulus panel, `matching`, `ordering`, label bank, drop-down gaps | The biology sample, rewritten, is sat and marked; keyboard-only and screen-reader passes |
| **T5. Practice self-check** | `reveal` for closed types; practice checks for code; Make a practice copy | A practice paper self-checks; the exam build of the same file passes the leak check |
| **T6. Programming extras** | `predict-the-output` with fill-by-running; trace-table rows | 2027's 1(a) and 1(e) rebuilt, keys filled by running |
| **T7. Next** | `math-expression`; GIFT and Moodle XML export | Then §9's table, as papers ask |

T4 and T5 can swap if the next papers are practice papers. T6 comes late because labelled-boxes carries those questions from T1, less conveniently.

---

## 11. Decisions for Josh

| # | Question | Recommendation | If not |
|---|---|---|---|
| 1 | Reopen Q15 as "assisted, never automatic" (§2.5) | Yes | Markers retype every multiple-choice mark; hidden checks have nowhere to show |
| 2 | Practice self-check as "show the paper's answer", no verdict, keys only in practice and sample papers (§7) | Yes | No self-check, or a page that says right and wrong, which dewlab has given up |
| 3 | Typed maths: plain text, preview, palette; paper for 2-D working; MathLive waits; no photographs (§4) | Yes | MathLive now: 1.1 MB per page and an unrun rehearsal |
| 4 | One maths reader for calculator, preview and checks (§4.3) | Yes | A quicker preview, but two readings of one answer |
| 5 | Hidden checks in the scheme, run only in the workbench (§5) | Yes | Checks on the page put the tests, in effect the key, before students |
| 6 | Options lettered and stored by letter, the lock recording each letter's text (§2.2) | Yes (grammar is `format.md`'s) | Reordering after a sitting silently misplaces answers |
| 7 | Predict-the-output where students can run the listing (§5) | Accept it and say so in the instructions for now | — |
| 8 | Band wording below 50% and rounding (§8) | From the college's results template | — |

---

## Evidence used

Research: `exam-types.md` §0, §2–7; `pdp-pages.md` §3, §8, §9; `code.md` §1, §2, §8; `design-docs.md` §3, §7, §9; `dewlab-runtime.md` §3, §7; `local-llm.md` §4, §5. Designs this round: `architecture.md` §3.2, §3.6, §4, §6, §7, §8; `student-flow.md` §7.2–7.4, §10, §11.1. Primary sources: `dewlab/dewmark/build_exam.py` (lines cited in §2.1), `assets/exam-page.js` (collect 33–115, restore 117–170, calculator 926–996), `workbench/index.html` (436–570), `planning/QUESTION_TYPES_AND_MARKING.md` §2–4, `planning/OPEN_QUESTIONS.md` Q9, Q15, Q17, `planning/THE_MARKING_WORKBENCH.md` §7, the five samples, and the four PDP papers' sources (fence counts and part structure). dewlab: `DECISIONS_LOG.md` 7.179 and 7.235; `build.py` `parse_question` (line 1515); `assets/tutorial_tools.py` `compare()` (line 1037).

New this round, in `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/design-round/question-types/` (scratch space; copy into `dev/probes/` if worth keeping): the four PDP sources extracted from their pages (`PDP_5N2927_*.md`), confirming the fence counts in §1; and `calc.js`, which runs dewmark's calculator parser over 26 typical final answers. It read 18; the 8 it could not read are listed in §4.3.
