# The exam file as typed blocks

*Design round 2, 2026-09-27, revised the same evening to follow Josh's twenty decisions (`planning/DECISIONS_2026-09-27.md`; where this document and a decision differ, the decision wins). One of three rival proposals for the file a teacher writes (the others are `format-paper-first.md` and `format-one-fence-family.md`). The angle: keep dewmark's typed settings blocks, make them strict, and let the machine check everything it can. Every fragment below comes from a file that passes a working prototype checker, re-run after the revision, and section 7's figures come from running two prototype converters on the real papers. The prototype is in scratch space, listed at the end.*

## The case in brief

dewmark's current grammar got the central idea right: the facts a machine must check (names, marks, types, keys) live in labelled **settings blocks**, and the words students read live around them as ordinary text. What went wrong was looseness at the edges, each piece found by a probe (`code.md` §1, `design-docs.md` §9): headings landed in the previous question, one answer's marks could be written in four places, the marking method was guessed, `No` became `False`, a misspelt setting built silently, and a missing marking block went unnoticed. Six changes keep the idea and remove the looseness:

1. **Every value is read as text**, and the setting's declared type decides what it means. `No` stays "No".
2. **Every block kind and question type has a closed list of settings.** Anything else stops the build, with a suggestion ("Did you mean `tolerance`?").
3. **Marks are written once**, on whatever the marker gives marks for. Every other total is added up by the builder; the paper total and optional `total:` lines are checksums.
4. **Everything secret lives in marking blocks, and nowhere else.** The student page is built from the other blocks, so a key cannot leak through a forgotten entry in a strip list.
5. **Headings are made from `title:` settings**, so no heading can land in the wrong question and no "(3 marks)" can drift from the data.
6. **Names are written; numbers are made.** The permanent name is typed once. "Question 3", "(b)" and "(ii)" come from order and may change freely.

With two small converters, all four PDP papers and all five dewmark samples convert and pass the prototype checker: nine papers, 190 answer boxes. On the way the checker caught two bugs in my own converters and one rule the grammar lacked, which is the argument in miniature: a strict file turns mistakes into messages.

---

## 1. The grammar

### 1.1 The carrier

An exam file is Markdown (plain text in which `**bold**` is bold and a blank line separates paragraphs) holding settings blocks. A block opens with three backticks and a kind (```` ```question ````), holds one setting per line (`marks: 3`), and closes with three backticks. Settings use the block style of YAML, a common plain-text settings format: `key: value` lines, two-space indentation for things that belong together, `- ` for list items, `[a, b]` for a short list, and `|` for several lines of text or code, indented beneath.

What changes is how a block is read. Today `build_exam.py:175` uses `yaml.safe_load`, which guesses what each value is. The proposal uses PyYAML's `BaseLoader`, which guesses nothing: every value arrives as text, and the setting's type (§1.4) decides what it means. PyYAML is already a dependency and already runs in the studio's in-browser Python (`architecture.md` §0). The same lines through both readers:

| Written in the file | Today (`safe_load`) | Proposed (text, then typed) |
|---|---|---|
| `options: [Yes, No]` | `True`, `False`, shown to students as "True"/"False" (`code.md` §1) | "Yes", "No" |
| `expected: 12:30` | 750 | "12:30", refused where a number is required |
| `value: 0.0750` with `sf: 3` | 0.075: the significant figures are lost | "0.0750", 3 significant figures |
| `session: 2025-10-20` | a date object | "2025-10-20" |
| `planning_box: no` | `False` | no, because `planning_box` is a yes-or-no setting |

Five things YAML allows are refused, each with a message saying what to do: tabs; `{ }` maps on one line; `&`, `*` and `!` at the start of a value; a setting written twice in a block (PyYAML keeps the second silently); and `#` comments, because YAML ends a value at ` #` without a word, cutting `label: Line 4 # of the code` short. A teacher's own notes go in `note:`, which every block accepts and students never see.

### 1.2 The ten block kinds

| Kind | How many, and where | Required settings | Optional settings |
|---|---|---|---|
| `exam` | exactly one, first in the file | `format`, `exam_code`, `version`, `kind`, `title`, `total_marks`, `time_allowed`, `student_details`; when `kind: exam`, also `module`, `module_code`, `hand_in` | branding and tools (§5) |
| `python-setup` | at most one, before the first section; required when any answer is `python-code` | `packages` | `delivery`, `files`, `setup_code`, `time_limit`, `suggestions`, `error_hints` |
| `reference` | any number, before the first section | `title` and `text`, or `standard` | — |
| `section` | one or more | `name` | `title`, `label`, `choose`, `total` |
| `question` | inside a section | `name` | `title`, `label`, `marks`, `total`, `choose`, `topic`, `outcomes`, `provided_code` |
| `stimulus` | inside a question, before its first part | `name`, `title` | — |
| `part` | inside a question | `name` | `title`, `label`, `marks`, `total`, `choose`, `topic`, `outcomes` |
| `subpart` | inside a part | `name` | `title`, `label`, `marks`, `total`, `outcomes` |
| `answer` | inside a question, part or sub-part | `name`, `type` | `marks`, `label`, `marked`, `hint`, `lines`, `maths_input`, `paper_allowed`, `outcomes`, and the type's own settings (§1.5) |
| `marking` | directly under the last answer box it marks | `method` | `guidance`, `points` or `criteria` (by method), `model_answer`, `model_code`, `key`, `any_order`, `form`, `checks`, `draft` |

Every block also accepts `note`. Today's six kinds (`build_exam.py:38`) gain four: `python-setup` takes the Python settings out of the exam block, and `stimulus`, `part` and `subpart` add the levels real papers have (the PDP Sample's 4B(i), a biology table shared by four parts). A question has parts or answer boxes, never both, and so does a part with sub-parts; the builder checks it.

### 1.3 Text around the blocks

- **Text belongs to the nearest block above it.** After the exam block it is the instructions to candidates; after a section, question, stimulus, part or sub-part it is that block's text; after an answer box it stays in its part, below the box. The `instructions:` and `prompt:` settings go: what students read is prose, where it sits.
- **`#`, `##` and `###` headings are refused.** Sections, questions and parts get their headings from `title:`, with numbers and marks added. `####` and smaller may be used inside text.
- **Code shown to students is a Markdown fence with a language word** (`python`, `text`, `pseudo`, `sql`, `output`), optionally `numbered` and `start=N`. Any other word must be a block kind, so ```` ```anwser ```` is refused ("Did you mean answer?") instead of being shown as code. This removes today's "a fenced code block in prose is a build error" (`code.md` §1).
- **`$...$` is mathematics in every student-visible setting**: options, labels, table cells, hints. Today those skip typesetting and pass with raw dollars (`code.md` §1). A `$` inside backticks is never mathematics; an unpaired `$` is refused.
- **Pictures** are `![description](pictures/file.svg)`, description required, as today.

### 1.4 Types of value

| Type | Written like | Checked |
|---|---|---|
| name | `q2.a.boxes` | lower-case letters, digits, hyphens, pieces joined by dots; starts with a letter; at most 40 characters; unique |
| text | `title: Reading a function` | one line; Markdown and `$maths$` |
| long text, code | `starter: \|` then indented lines | kept exactly |
| marks, whole number | `3`, `0.5`; `choose: 2` | whole or half; 1 or more |
| yes or no | `planning_box: yes` | exactly `yes` or `no`; `true` and `on` are refused |
| choice | `timer: shown` | one of a published list, with did-you-mean |
| time | `2 hours`, `10 seconds` | words, never a bare number |
| file | `pictures/cell.svg` | exists beside the exam file |
| lettered list, named list | `A: …`, `B: …`; `root-1: $x =$` | letters in order; short inner names (§3) |

### 1.5 Question types

Each type has a closed list of **public** settings in its answer block (what students see) and a **key** shape in its marking block (what students must not see).

| Type | In the answer block | `key:` in the marking block | Today |
|---|---|---|---|
| `multiple-choice` | `options:` A, B, C…; `several: yes` | `B`, or `[A, C]` | exists |
| `fill-in-the-blank` | `text:` with gaps `{1}`, `{2}`, or a drop-down gap `{3: nucleus \| ribosome \| vacuole}` | `1: mitochondrion`, one line per gap; a list for accepted alternatives | exists |
| `short-written-answer`, `long-written-answer` | `starter_text`, `lines` | none; `model_answer` | exists |
| `essay` | `guide_words`, `planning_box` | none; usually `method: criteria` | exists |
| `numeric-answer` | `boxes:` name → label; `unit_box`, `working_box` | per box: a number, or `value`, `tolerance`, `range`, `sf`, `dp`, `units` | exists |
| `complete-the-table` | `columns`, `rows` with `"?"` cells; `add_rows` | the whole table again, filled in | exists |
| `describe-a-sketch` | `shape_prompt`, `shapes:` A, B…; `features:` name → label with one `_` per box | `shape:` letter; each feature's values | exists |
| `label-the-diagram` | `image`, `image_description`, `pointers`, optional `bank` | `1: cell wall`, one line per pointer | exists |
| `python-code` | `starter`, `time_limit` | none; `model_code`, `checks` | exists |
| `labelled-boxes` | `boxes:` name → label | optional, per box | first wave |
| `matching` | `rows:` name → text; `choices:` A, B…; `reuse` | row → letter | first wave |
| `ordering` | `items:` A, B… in the order shown | the right order, `[C, A, D, B]` | first wave |
| `pseudocode` | `starter` | none | first wave |
| `answer-on-paper` | — | none | first wave |
| `math-expression` | `box_label`, `working_box` | one expression; `form:` in the marking block | later (`question-types.md` §4.5) |

The type list is the registry's (`question-types.md` §2.2), so a new type is one more row: its public settings, its key shape, its checks.

---

## 2. Structure and marks

**The hierarchy** is section, question, stimulus, part, sub-part, answer box; stimulus, part and sub-part are optional.

**Marks are written once, on the marking unit**: whatever block carries `marks`, either an answer box marked alone or a part (or question, or sub-part) whose boxes are marked together. Along the path from a section down to any answer box, exactly one block carries `marks`; two is refused ("Marks are written in two places for this answer box… Write them once, where the marker gives them"), and so is none. Today one answer's marks can appear on its question, its answer block, its marking block and as a `limit`, with three checks whose only job is keeping the copies equal (`build_exam.py:329`, `586`, `638`). Shared marks matter: the PDP Sample's 1A(i)–(iii) share 3 marks, 4B(i)'s function and tests cells share 4, and the 2027 paper has four such parts (`pdp-pages.md` §9.3, gap 3). The current grammar forces the teacher to invent a split, which `TRANSLATING_AN_EXISTING_EXAM.md` §2 forbids.

**Rough work** is an answer box with `marked: no`: no marks, no marking block, allowed anywhere.

**Every other total is computed**, upwards from the units to the paper, and the "(3 marks)" students read is generated from it.

**Checksums.** `total_marks` is required; `total:` may be written on any section, question, part or sub-part. A checksum feeds no calculation; it only has to agree, and a disagreement names every piece (the first message in §8). Converters write `total:` wherever the source paper states a total, which catches transcription slips.

**"Answer any N"** is `choose: N` on a section (among its questions) or on a question or part (among its parts). The choices must carry their own marks and be worth the same, as today (`build_exam.py:338`). The total is N times one choice, and the sentence "Answer any two of the three questions in this section. Each is worth 6 marks." is generated, which retires today's check that the instructions mention the rule, a check that passed whenever any "2" appeared in them (`build_exam.py:343-350`). The workbench's "best N" counting is unchanged.

---

## 3. Answer spaces and their names

**An answer box is one `answer` block**: a `name`, a `type` and the type's public settings. What the block says is exactly what the student sees, in that order; nothing is reordered or derived behind the teacher's back.

**The name is the permanent key** for the saved answer, the mark, the spreadsheet column and the graded paper. The teacher writes it, or the studio or a converter proposes it once from the printed number (`q2.a.boxes`); the builder never derives it from position. Names need not start with their question's name, so a box moved to another question keeps its name.

**Inner names.** One answer often stores several pieces, and each has a written name: letters for options (`A:`), numbers for gaps (`{1}`) and pointers, short names for boxes and rows (`root-1:`, `amylase:`), row and column for table cells. A saved answer has a key for every piece:

```json
"q2.a.boxes": {"boxes": {"i": "singGoodMorning", "ii": "name", "iii": "Saoirse"}, "touched": true}
```

**Numbers are made.** "Question 2", "2(a)" and "(ii)" come from order and the exam's `numbering` style (`1(a)(i)`, `1A(i)` or `A1(a)(i)`); `label:` overrides one. When a teacher moves the tank question above the quadratic, the printed numbers change and every name stays. When she inserts a part between (a) and (b), the old (b) prints as (c) and is still stored under `q1.b`; the workbench and spreadsheet show "1(c) · q1.b".

**The names lock** (`architecture.md` §6) holds the contract after a sitting: at first issue it records every name and inner name with its type, marks and printed label, and a later build that renames, removes, retypes or re-marks one stops unless `version` changes. Because inner names are written in the file, the lock is complete: it records each option letter's text, so swapping options A and B after a sitting is refused instead of silently misplacing every stored "A". Before the first issue, anything may change.

---

## 4. Marking and model answers

**Where.** A marking block goes directly under the last answer box of its marking unit, with no text between: one per unit, required. Today a missing one silently becomes marks-out-of-a-total (`build_exam.py:564`). A marking block giving the marker nothing (no guidance, points, criteria, key, model answer or code) is refused unless it says `draft: yes`.

**The method is named**, never inferred (today `build_exam.py:570` and `594` guess it from which keys are present), and a setting belonging to another method is refused:

- `method: marks`: one number, with optional `guidance:` lines.
- `method: points`: `- 2 marks: explains denaturation`. The limit is the unit's marks, so no `limit:` needs keeping equal. No point may exceed the marks available, and together they must reach them.
- `method: criteria`: each criterion has a `name`, `marks` and `bands:` written `- 7 to 8: a sustained line of argument`. The criteria add up to the unit's marks, and each criterion's bands must cover 0 to its marks with no gap or overlap, which is new (today a band only has to fit inside, `build_exam.py:594-628`). The range is the band's setting name, read as data, not a pattern searched for inside a string (`BAND_RE`, `build_exam.py:63`, takes whole numbers only).

**Model answers** are `model_answer:` (Markdown with maths) and, for code, `model_code:`. **Keys** take the shape their type defines (§1.5); wherever a key accepts words, a list gives accepted alternatives: `3: [membrane, cell membrane, plasma membrane]`.

**Numbers, tolerance and units.** A numeric key is a number, or a `value` kept exactly as written with any of `tolerance` (`0.05`, or `1%`), `range` (`3.14 to 3.142`), `sf`, `dp` and `units` (accepted spellings; requires `unit_box: yes`). `any_order: yes` lets a two-root answer come either way round. The builder checks the key against itself:

```
Line 66, the marking block for the answer box "q1.b.value" in 1(b):
  `sf: 2`, but the value 0.0750 is written with 3 significant figures. Write the value to the same number of figures you ask for.
```

**Hidden tests for code** are `checks:` in the three shapes the PDP papers need (`question-types.md` §5): `- call: longer_word("cat", "horse")`; `- run: [17]` with `contains: [junior]` (run the program, typing 17 when asked); `- after: [a == 17, leftover == 2]`. Without `expect:`, a result is compared with the same check on `model_code`. Checks run in the workbench's Python worker, and also in a practice or sample page that says `practice_checks: yes`, so students see which pass (decision 16). They never run in an exam page, and `practice_checks` on a `kind: exam` file is refused.

**A key never awards a mark.** Following decision 13, the rules the teacher wrote (a key, a tolerance, a check) propose marks on closed types and give evidence on the rest; the marker confirms every mark. The language-model assistant never proposes marks (decision 17); nothing in the marking block is addressed to it. `draft: yes` marks what a converter or the assistant wrote rather than transcribed (`TRANSLATING_AN_EXISTING_EXAM.md` §2); drafts build for preview and practice, and Issue refuses an exam that still has one.

**Keeping it out of the student page** takes three layers, the first new:

1. **Structure.** The parser splits the file into a public tree (every block except `marking`, minus every `note`) and a marking tree. The student and practice renderers receive only the public tree, and a test asserts that handing them the marking tree fails. There is no per-type strip list to forget (today `leak_fragments`, `build_exam.py:1187`).
2. **Schema.** Answer blocks have no secret settings; `expected:` in an answer box is refused, pointing to the marking block.
3. **Search.** The self-check searches the whole built page for every marking string of four or more characters, including the embedded data and scripts that today's check strips out first (`build_exam.py:1228`, `code.md` §1).

The declared exceptions are both practice-only and both named in the exam block, so the leak search knows what to allow. `practice_reveal: closed` (keys of closed types) or `all` (also model answers) carries the answers into a practice or sample page, shown only once the student has finished the whole paper, never question by question (decision 14). `practice_checks: yes` carries `checks` and `model_code`. A `kind: exam` file refuses both settings, so an examination page is always built from the public tree alone.

---

## 5. Exam settings and presentation

The exam block holds what the cover, the top bar, the print header, the finish screen and every exported file need, as data. This is the 2027 paper's block (it passes the checker in front of the converted paper):

```exam
format: 1
exam_code: pdp-5n2927-exam-2027
version: 2026.10.01.1
kind: exam
title: Written Examination 2026–2027
module: Programming and Design Principles
module_code: 5N2927
session: 2026–2027
institution: Dublin and Dún Laoghaire ETB
college: Dublin College Dundrum
logo: pictures/dcd-logo.svg
technique: Examination-Theory
weighting: 30%
total_marks: 60
time_allowed: 2 hours
timer: enforced
breaks: no
calculator: none
student_details: [name, number]
number_example: D00123456
numbering: 1(a)(i)
hand_in: |
  Save your answer file, then upload it to "5N2927 Written Examination"
  on Moodle. Raise your hand so that your invigilator can see the
  confirmation card before you leave.
```

| Setting | Used for |
|---|---|
| `format`, `exam_code`, `version` | which grammar (a file without `format` is refused with an offer to convert, §7); file names, save keys, the names lock |
| `kind`: `exam`, `practice`, `sample` | the band ("EXAMINATION" or "PRACTICE PAPER"), hints, reveal, storage (`student-flow.md` §10) |
| `title`, `module`, `module_code`, `session`, `institution`, `college` | cover, masthead, print header, answer file, exports (`student-flow.md` §11.2) |
| `logo`, `logo_dark` | cover and masthead; SVG, PNG, JPEG or WebP, scripts stripped, refused above 150 KB (`student-flow.md` §11.3) |
| `technique`, `weighting`, `outcomes` | QQI export columns; blocks tag `outcomes: [6, 7]`, and an unlisted number is refused (`question-types.md` §8) |
| `time_allowed`, `timer`: `none`, `shown`, `enforced` | decision 11: no timer, a timer shown, or a timer that ends the sitting; in every case the student can hide it with one click |
| `breaks`: yes or no | decision 11: off unless set; when on, the page offers a clean way to start and end a break |
| `calculator`: `none`, `scientific` | the side-panel calculator |
| `student_details`, `number_example` | the fields on the one combined start screen (decision 9), from the fixed vocabulary `name`, `number`, `seat` |
| `hand_in` | the finish screen's upload instructions, replacing the PDP pages' hard-coded Moodle wording. There is no setting for the PDF: every hand-in includes one (decision 10), and the data file's form is dewmark's choice, not the paper's |
| `numbering`: `1(a)(i)`, `1A(i)`, `A1(a)(i)` | printed numbers |
| `maths_input`: a list from `typed`, `editor`, `photo` | decision 15: which maths routes the paper offers (plain text with a "reads as" line and symbol palette; the MathLive visual editor; photographs of handwritten working). An answer box may narrow it |
| `practice_reveal`: `none`, `closed`, `all`; `practice_checks`: yes or no | practice and sample papers only (§4) |

**Python** has its own block, present only when the paper has code, so the decision to carry Python is visible at the top:

```python-setup
packages: [sqlite3, pandas, matplotlib]
delivery: inside
files:
  - path: data/hvit_registry.db
    as: hvit_registry.db
    description: The main student registry database, for Tasks 1 to 4.
setup_code: |
  import sqlite3
  conn = sqlite3.connect("hvit_registry.db")
time_limit: 10 seconds
suggestions: yes
error_hints: no
```

`packages` is checked against the pinned list of what dewmark's Python kit carries, so a package that would need the internet in the room is refused at build time (today `openpyxl` comes from PyPI mid-sitting, `code.md` §4). `time_limit` is the per-run limit, overridable on one answer box; `suggestions` is code completion. A **reference sheet** is a `reference` block with a `title` and `text`, or `standard: python-basics` for the Python sheet the PDP pages carry.

**The start screens are generated from these blocks.** The cover takes its branding from the exam block, and the Get ready checklist (`student-flow.md` §5.2) has one row per thing `python-setup` declares: Python, each package with its pinned size, each file, the set-up code. A teacher never configures the loading screen; the file already says what must load.

**Branding** follows decision 12: text settings plus an optional logo, and the EXAMINATION or PRACTICE band is fixed by `kind`, not written. There is deliberately no colour setting yet; a strict grammar adds one later as one more row, without disturbing existing files.

**Python delivery** (decision 7) is `delivery: inside` (Python carried in the file, with a folder beside it for heavy packages) or `delivery: internet` (loaded from the web when the page opens). The builder should warn, not refuse, when a `kind: exam` paper says `internet`, since an exam room may have no connection but the teacher knows the room; with `inside` it refuses any package missing from the pinned kit.

Defaults: `timer: shown`; `breaks: no`; `calculator: none`; `maths_input: [typed]`; `delivery: inside`; `time_limit: 10 seconds`; `suggestions: yes`; `error_hints: yes`.

---

## 6. Worked examples

All five are sections of one file, `examples.exam.md`, which passes the prototype checker; its exam block is like §5's with `kind: practice`, `practice_reveal: closed`, `practice_checks: yes` and `maths_input: [typed, editor, photo]`.

### (a) A PDP-style question: listing, labelled boxes, code, rough work

From the 2027 paper, Question 2. The question is named `q2` because that is its number in the source; in the examples file it prints as "Question 1", which shows the point of section 3: names do not follow numbers.

````markdown
```question
name: q2
title: Functions
total: 6
outcomes: [8]
```

```part
name: q2.a
title: Reading a function
marks: 3
```

Study the program below and answer the questions that follow.

```python numbered
def singGoodMorning(name):
    print("Good morning to you.")
    print("Good morning to you.")
    print("Good morning dear", name)
    print("Good morning to you.")
    return

singGoodMorning("Saoirse")
```

```answer
name: q2.a.boxes
type: labelled-boxes
boxes:
  i: (i) What is the name of the function?
  ii: (ii) What is the name of the parameter?
  iii: (iii) What is the value of the argument?
  iv: (iv) What output does the program display?
  v: (v) Explain the main benefit of using a parameter in this function.
  vi: (vi) What is the purpose of line 8?
  vii: (vii) What would happen if you called the function without an argument?
```

```marking
method: points
points:
  - 0.5 marks: (i) singGoodMorning
  - 0.5 marks: (ii) name
  - 0.5 marks: (iii) "Saoirse"
  - 0.5 marks: (iv) the four lines, with "Good morning dear Saoirse" third
  - 0.5 marks: (v) one function greets anyone, with no copied code
  - 0.5 marks: (vi) line 8 calls the function, so its code runs
  - 0.5 marks: (vii) a TypeError, because the required argument is missing
key:
  i: singGoodMorning
  ii: name
  iii: [Saoirse, '"Saoirse"']
```

```part
name: q2.b
title: Removing duplication
marks: 3
```

Rewrite the code below so that the duplicated line,
`print("Thanks for playing.")`, appears only once. Both versions must be
logically equivalent. The first two lines set up test values so that you
can run your answer.

```answer
name: q2.b.code
type: python-code
starter: |
  guess = 7
  secret = 7

  if (guess == secret):
      print("Correct!")
      print("Thanks for playing.")
  else:
      print("Wrong guess.")
      print("Thanks for playing.")
```

```marking
method: marks
guidance:
  - 1 mark for moving the shared print below the if/else, not indented
  - 1 mark for keeping each branch's own message
  - 1 mark for code that runs and prints the same as the original
model_code: |
  guess = 7
  secret = 7

  if guess == secret:
      print("Correct!")
  else:
      print("Wrong guess.")
  print("Thanks for playing.")
checks:
  - run: []
  - after: [guess == 7, secret == 7]
```

```answer
name: q2.rough
type: python-code
marked: no
label: Question 2 rough work
```
````

Seven boxes share 3 marks through a points list at half a mark each; the key covers only the three boxes with one right answer, and the workbench shows it beside those three.

### (b) Maths: "answer any 2 of 3", a numeric answer with tolerance and units, a typed-maths answer

````markdown
```section
name: calculation
title: Calculation
choose: 2
```

```question
name: tank
title: A water tank
```

A cylindrical water tank has an inside radius of 40 cm and an inside
height of 1.2 m. Find how much water the tank holds, in litres, correct to
one decimal place. Show your working. (1 litre = 1000 cm³)

```answer
name: tank.volume
type: numeric-answer
marks: 6
boxes:
  volume: "The tank holds"
unit_box: yes
working_box: yes
hint: Put both lengths in centimetres before you use $V = \pi r^2 h$.
```

```marking
method: marks
guidance:
  - 2 marks for $V = \pi r^2 h$ with both lengths in centimetres
  - 1 mark for about 603 186 cm³
  - 1 mark for dividing by 1000
  - 2 marks for 603.2 litres, with the unit
key:
  volume:
    value: 603.2
    tolerance: 0.05
    dp: 1
    units: [litres, litre, l, L]
model_answer: |
  $V = \pi \times 40^2 \times 120 = 603185.8$ cm³, which is 603.2 litres.
```

```question
name: quadratic
title: A quadratic function
```

Consider the function $f(x) = x^2 - 2x - 8$.

```part
name: quadratic.factors
```

Factorise $f(x)$.

```answer
name: quadratic.factors.expression
type: math-expression
marks: 2
box_label: $f(x) =$
```

```marking
method: marks
guidance:
  - 1 mark for a pair of brackets that multiply out to $x^2 - 2x - 8$
  - 1 mark for the signs, as in the key
key: (x - 4)(x + 2)
form: factorised
```

```part
name: quadratic.roots
```

Hence solve $f(x) = 0$.

```answer
name: quadratic.roots.values
type: numeric-answer
marks: 4
boxes:
  root-1: $x =$
  root-2: $x =$
working_box: yes
```

```marking
method: marks
guidance:
  - 2 marks for setting each bracket equal to zero, shown in the working
  - 1 mark for each correct root
key:
  root-1: 4
  root-2: -2
any_order: yes
```

```question
name: savings
title: Compound interest
```

Aoife puts €2,500 into a savings account that pays 3.5% interest a year,
compounded yearly. She takes nothing out.

```answer
name: savings.amount
type: numeric-answer
marks: 6
boxes:
  amount: "After 4 years the account holds €"
working_box: yes
```

```marking
method: marks
guidance:
  - 2 marks for the multiplier 1.035
  - 2 marks for raising it to the power 4
  - 2 marks for €2,868.81
key:
  amount:
    value: 2868.81
    tolerance: 0.01
    dp: 2
```
````

The builder computes the section as 2 × 6 = 12 marks and writes "Answer any two of the three questions in this section. Each is worth 6 marks." The hint appears only in the practice build. `math-expression` is a later type (§1.5); until it ships, the same part is a `short-written-answer` (whose box offers the paper's `maths_input` routes: here typed, the MathLive editor, or a photograph) with the expression as `model_answer`.

### (c) Biology: a shared data table, a label bank, a matching part

````markdown
```question
name: amylase
title: Starch digestion
```

```stimulus
name: amylase.table-1
title: Table 1
```

A student mixed starch solution with the enzyme amylase at five
temperatures, and timed how long the starch took to disappear.

| Temperature (°C) | 10 | 20 | 30 | 40 | 50 |
| --- | --- | --- | --- | --- | --- |
| Time for the starch to disappear (s) | 300 | 180 | 90 | 60 | 240 |

```part
name: amylase.change
```

Using Table 1, calculate the percentage decrease in the time taken when
the temperature rises from 30 °C to 40 °C. Give your answer to 3
significant figures.

```answer
name: amylase.change.percent
type: numeric-answer
marks: 3
boxes:
  decrease: "Percentage decrease ="
unit_box: yes
working_box: yes
```

```marking
method: marks
guidance:
  - 1 mark for the change, 90 - 60 = 30 s
  - 1 mark for dividing by the starting time, 90 s
  - 1 mark for 33.3%
key:
  decrease:
    value: 33.3
    sf: 3
    units: ["%", per cent, percent]
```

```part
name: amylase.fifty
```

Using Table 1, explain why the starch took longer to disappear at 50 °C
than at 40 °C.

```answer
name: amylase.fifty.explain
type: short-written-answer
marks: 4
lines: 5
```

```marking
method: points
points:
  - 1 mark: the optimum temperature is about 40 °C
  - 1 mark: above the optimum the enzyme is denatured
  - 1 mark: the active site changes shape
  - 1 mark: starch no longer fits the active site, so fewer reactions happen
  - 1 mark: uses the figures, 60 s at 40 °C against 240 s at 50 °C
model_answer: |
  About 40 °C is the optimum. At 50 °C some amylase is denatured: its
  active site changes shape, so starch no longer fits and fewer
  molecules are broken down each second. The time rises from 60 s to
  240 s.
```

```part
name: amylase.organs
```

The diagram shows the human digestive system. Label each numbered part
using the words in the list.

```answer
name: amylase.organs.labels
type: label-the-diagram
marks: 4
image: pictures/digestive-system.svg
image_description: |
  An outline of the human body from the mouth to the hips, showing the
  digestive system. Pointer 1 indicates a gland beside the mouth.
  Pointer 2 indicates a J-shaped bag on the left below the ribs. Pointer
  3 indicates a flat organ lying under that bag. Pointer 4 indicates the
  long coiled tube in the centre of the abdomen.
pointers: 4
bank: [salivary gland, stomach, pancreas, small intestine, large intestine,
  liver, oesophagus]
```

```marking
method: marks
guidance:
  - 1 mark per label
key:
  1: salivary gland
  2: stomach
  3: pancreas
  4: small intestine
```

```part
name: amylase.enzymes
```

Match each enzyme to what it does.

```answer
name: amylase.enzymes.match
type: matching
marks: 3
rows:
  amylase: Amylase
  protease: Protease
  lipase: Lipase
choices:
  A: breaks down fats into fatty acids and glycerol
  B: breaks down starch into sugars
  C: breaks down proteins into amino acids
  D: builds glucose into starch
```

```marking
method: marks
guidance:
  - 1 mark per row
key:
  amylase: B
  protease: C
  lipase: A
```
````

The stimulus holds the text after it until the first part, and is shown beside all four parts (`question-types.md` §6.1). The builder refuses a bank that lacks a keyed label ("no student could choose it") and a key that uses one choice twice unless the answer says `reuse: yes`.

### (d) Multiple choice

````markdown
```question
name: photosynthesis
title: The equation for photosynthesis
```

Which equation describes photosynthesis?

```answer
name: photosynthesis.choice
type: multiple-choice
marks: 2
options:
  A: 6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂
  B: C₆H₁₂O₆ + 6O₂ → 6CO₂ + 6H₂O
  C: 6O₂ + 6H₂O → C₆H₁₂O₆ + 6CO₂
  D: C₆H₁₂O₆ → 2C₂H₅OH + 2CO₂
```

```marking
method: marks
key: A
guidance:
  - B is respiration and D is fermentation; neither earns a mark
```
````

The student sees the letters, the answer file stores the letter, and the lock records each letter's text.

### (e) An essay with a criteria grid

````markdown
```question
name: screens
title: Screens and paper
```

"Studying from a screen is worse than studying from paper." Discuss,
drawing on your own experience and on the research summaries covered this
term.

```answer
name: screens.essay
type: essay
marks: 20
guide_words: 600
planning_box: yes
```

```marking
method: criteria
criteria:
  - name: Argument and structure
    marks: 8
    bands:
      - 7 to 8: a sustained line of argument; each paragraph builds on
          the one before
      - 4 to 6: a clear position, developed unevenly
      - 0 to 3: description without an argument
  - name: Use of evidence
    marks: 8
    bands:
      - 7 to 8: research and experience are woven into the argument
      - 4 to 6: evidence is present but summarised rather than used
      - 0 to 3: little or no evidence
  - name: Clarity of writing
    marks: 4
    bands:
      - 3 to 4: precise, controlled prose
      - 0 to 2: meaning is sometimes unclear
```
````

---

## 7. Conversion

Both kinds of source convert **by script**, because both are already machine-readable. The prototypes share one 95-line writer (`emit.py`) that turns plain data into blocks, quoting only where the syntax needs it.

**PDP pages** (`pdp2tb.py`, 281 lines) read the `exam-src` string out of the page. Front matter becomes the exam and `python-setup` blocks; `## Question N: Title (M marks)` a question with `total: M`; `### 1(a): Title (3 marks)` a part with `marks: 3`; the Sample's `**(i) Longer word (4 marks).**` a sub-part. `answer` fences become written answers, `python` fences code answers (`(optional)` ones `marked: no`), `fields` fences `labelled-boxes`, and `text`, `py` and `pseudo` fences numbered listings. The 2027 paper's HTML fractions become `$\frac{4}{3}\pi r^3$` and its flowchart SVG a picture file described by its `aria-label`. Each part gets `method: marks` with `draft: yes`.

| Paper | Answer boxes | Marking units | Drafts to write | Source → typed file |
|---|---|---|---|---|
| Sample | 17 | 12 (11 parts, of which 4B has 2 sub-parts) | 12 | 8.4 KB → 10.1 KB |
| Practice 1 | 17 | 12 | 12 | 8.3 KB → 10.0 KB |
| Practice 2 | 17 | 12 | 12 | 8.5 KB → 10.2 KB |
| Exam 2027 | 28 | 21 | 21 | 11.9 KB → 13.1 KB |

All four pass, with totals of 60 computed from the parts. What remains by hand is the teacher's real work: marking schemes and model answers, which no PDP source has (`pdp-pages.md` §1). Optional retyping comes later: the 2027 paper's five "Line 1: … Line 12:" scaffolds as `labelled-boxes`, the Sample's 1A(iii) as `ordering` (`question-types.md` §1). **Effort:** about two days to turn the converter into tested production code; then minutes per paper, plus one to two hours of the teacher's time per paper for the marking.

**dewmark's five samples** (`old2tb.py`, 261 lines). It moves `expected`, `correct` and the model answers into marking blocks, names each method, drops the duplicated marks (a question's `marks` becomes a `total:` checksum), letters the options, numbers the gaps, turns `### Question A1 — Reading a graph` into `title: Reading a graph`, moves `prompt:` text above its box, and gathers the Python settings into `python-setup`. All five pass: 111 answer boxes, each paper's computed total matching its `total_marks`. By hand: check the extracted titles, rename the converter's box names (`1`, `2`, `f1`) where wanted, add `module`. **Effort:** half a day for all five.

**What the strictness found while converting.** A writer bug that turned table keys into quoted strings was refused ("Row 1 of the key has a different number of cells from the table"). My first HTML-maths conversion produced `4$\pi$r^2$`, caught by the unpaired-dollar check. The database practical had its reference blocks at the end of the file, refused until the converter moved them to the top. And Practice 2 lists `total$` in inline code, which showed the grammar needed the rule that a `$` inside backticks is never mathematics.

**Old files** have no `format:` line. The builder refuses them with an offer, never a guess: "This file is in the 2025–26 format. The studio's Upgrade this file converts it and shows you every change."

---

## 8. Translation by a language model

A model converting a teacher's Word exam gets this grammar right for five reasons. The first matters now, because the paste route ships first (decision 20); the others matter once a local or approved cloud endpoint is connected (decision 18).

1. **The paste route checks the reply mechanically.** With no model connected, the studio prepares a package for any assistant: an idealised exam file for the subject (section 6's examples are ready-made), the cheat sheet of section 9 as the format guide, and the teacher's exam, with no student data. The model writes `key: value` lines, the commonest settings format in its training text, and the teacher pastes the reply back. Because every setting list is closed and every value typed, the checker can tell a right reply from a plausible one: a stray `true`, an unquoted colon or `expected:` in an answer box is refused with its line and a fix, and the teacher can paste the message back to the assistant (the studio should offer a "copy these problems" button). That loop is also the small exercise in AI literacy the decision asks for: the teacher sees the model's slips named.
2. **With an endpoint, the file is the JSON the model already returns.** `assistant.md` §3.4 has the model return JSON (a plain-text data format) under a schema, and dewmark write the file. Each block is one JSON object and each setting one property, so writing is mechanical: `emit.py` does it in 95 lines.
3. **The model's schema comes from the checker's own lists.** A JSON Schema (a description of the exact shape a reply must have) generated from the block and type lists uses only closed property lists and fixed choices, the subset local model servers turn into a grammar the model cannot step outside (`assistant.md` §1.5, `local-llm.md` §1). An unknown setting, type or method becomes impossible to generate, not merely caught.
4. **Nothing depends on counting.** Options carry their letters, gaps their numbers, boxes their names. Models are unreliable at "the third option"; `correct: 3` by position was a hazard even for people (`design-docs.md` §9).
5. **Every fact has one home.** Marks go on the marking unit, the method is named, secrets go in the marking block. A model cannot produce two disagreeing copies of a number; the only repeats are checksums, exactly where a transcription slip should show.

The five conversion modes of decision 19 (copy without composing, tidy the wording, check accessible language, make it more UDL-friendly, rephrase commands as invitations) change only the prose between blocks and the `title:` and `label:` settings. Because structure, names, marks and keys live in typed settings, the studio can show every wording change as a difference in text and verify that no mark, name or key moved: a rephrasing mode whose reply alters a `marks:` line should be refused, not merely flagged.

`draft: yes` carries the rule that drafted answers are labelled, and dewmark, not the model, assigns names from printed numbers (`assistant.md` §3.4). Three messages, exactly as the prototype prints them to a teacher:

```
Line 19, Question 1 ("q1"):
  `total: 15` does not match: the parts add up to 14 (1(a) 3, 1(b) 3, 1(c) 3, 1(d) 2, 1(e) 3). Change one of them, or the total.
```

```
Line 90, answer "q1.e.text":
  "expected" is not a setting an answer box can have. Answers and keys go in the marking block under the answer box, so that they can never reach the student's page.
```

```
Line 444, a marking block:
  This marking block is meant for answer "photosynthesis.choice", but text on line 441 comes between them. A marking block goes directly under its answer box. Move the text above the answer box.
```

Each says where, what is wrong and what to do, in the calm three-part voice `APPEARANCE_AND_READABILITY.md` asks for. The real builder adds a stable code to each (`marks-dont-add-up`) linking to a help page (`architecture.md` §3.3).

---

## 9. What a teacher has to learn: the cheat sheet

````text
THE EXAM FILE ON ONE PAGE

A paper is ordinary text with settings blocks in it. A block starts with
```kind and ends with ```. Inside, one setting per line:  marks: 3
Text outside the blocks is what students read, shown where it sits.

PAPER SETTINGS WORTH KNOWING  (in the exam block)
  kind: exam | practice | sample        timer: none | shown | enforced
  breaks: yes | no                      calculator: none | scientific
  maths_input: [typed, editor, photo]   (choose one or more)
  Every hand-in includes a PDF. You do not set it.

THE ORDER OF A FILE
  ```exam           once, at the top: what the paper is (see the template)
  ```python-setup   only if there are code questions
  ```reference      any number: sheets for the side panel
  Your instructions to candidates, as ordinary text.
  ```section        then, for each section:
    ```question       its text follows it
      ```stimulus     optional: a table or passage every part uses
      ```part         optional: (a), (b)...   ```subpart for (i), (ii)...
        ```answer     one box for the student to fill
        ```marking    directly under the last box it marks, nothing between

FIVE RULES
1  Write marks once, where the marker gives them: on the answer box, or on
   the part or question if its boxes are marked together. Everything else
   is added up for you. total_marks: and total: are only checks.
2  Answers, keys, model answers and code checks go only in marking blocks.
3  Names (q3.roots) are permanent once students have sat the paper.
   Numbers (Question 3, (b), (ii)) are made from the order: move freely.
4  Do not type #, ## or ### headings. Give the block a title: instead.
5  Every value is text. yes or no only where a setting asks for it.
   Put a value in quotes if it contains ": " or " #", or starts with
   - [ { & * ! | > ' " % @ or `.
   Code and long text go after a |, every line indented two spaces.

MARKING METHODS  (method: is required)
  method: marks      guidance:  - 1 mark for the method
  method: points     points:    - 2 marks: names the optimum temperature
  method: criteria   criteria:  - name: Argument   marks: 8
                                  bands:  - 7 to 8: a sustained argument
  Add key:, model_answer: or model_code: as the type needs.
  draft: yes  = not checked by you yet; the paper will not issue.

QUESTION TYPES  (type: in the answer block;  key: in the marking block)
  multiple-choice      options: A: B: C:            key: B
  fill-in-the-blank    text: The {1} is...          key: 1: nucleus
  numeric-answer       boxes: volume: "V ="         key: volume: 603.2
                                  (or value:, tolerance:, sf:, dp:, units:)
  label-the-diagram    image:, pointers: 4, bank:   key: 1: stomach
  matching             rows:, choices: A: B:        key: row: B
  ordering             items: A: B: (shown order)   key: [C, A, B]
  labelled-boxes       boxes: i: (i) Function name  key: optional
  complete-the-table   rows: with "?" cells         key: the full table
  describe-a-sketch    shapes:, features:           key: shape: A ...
  short-written-answer, long-written-answer, essay, pseudocode,
  answer-on-paper      (model_answer: in marking)
  python-code          starter: |                   model_code:, checks:
  Rough work: any box with  marked: no

WHEN THE CHECK COMPLAINS  it names the line, the block and the fix.
````

The studio's Insert menu writes every block from the registry's snippets (`architecture.md` §3.2), so a teacher using it types the words and numbers, not the settings names.

---

## 10. Self-critique

**1. It is still YAML, and teachers will meet its rules.** The strict reader turns every silent YAML failure into a message, but it cannot remove the rules themselves: quotes around a value with ": " in it, two-space indentation, and `|` blocks whose lines must all be indented. Pasting a Python program into `starter: |` without indenting it gives "This line starts further left than the lines above it, so the block cannot be read". The message is clear and points at the line, but the teacher still has to indent forty lines. The studio's editor can indent a paste automatically; by hand, it is a chore. **This is what breaks first:** the first teacher who writes a code paper in Notepad.

**2. The key sits away from what it keys.** Keeping every secret in the marking block is what makes the leak guarantee structural, but it costs readability. `The {1} is the site of respiration` with `1: mitochondrion` below is harder to read than dewmark's current `{mitochondrion}`, and a multiple-choice key is a letter a few lines from its option. The dangerous case: a teacher swaps options B and C before the first issue and forgets the key. The file is still valid, so no check fires. The mitigations are real but indirect: the answer key view prints the keyed text beside each letter, the Before you issue list requires "I have sat this paper myself" (`architecture.md` §3.3), and the lock makes the same mistake impossible after a sitting. If Josh prefers inline answers for blanks, `{mitochondrion}` could be allowed as the one exception, at the price of a strip step for that one type.

**3. Ceremony.** Ten block kinds, a marking block for every unit (even an empty draft), and names on everything make a file longer and more formal than a PDP source: the Sample grows from 8.4 KB to 10.1 KB before any marking is written, and a four-option multiple-choice answer with its key is two blocks and fourteen lines, three blocks if it is a question of its own. A teacher writing a quick practice quiz by hand will find paper-first lighter. The bet is that teachers mostly write through the studio's snippets or through conversion, and that the formality pays for itself at marking time, when every answer has a name, a method and a key. If most teachers end up hand-writing files, that bet loses.

---

## 11. What ships first, what waits, and what Josh decides

**First, with the move and before any sitting** (`architecture.md` §7 step 2): the text-only reader and its five refusals; closed settings lists with did-you-mean; `format: 1`; named methods; marks once, with checksums; a required marking block per unit; secrets only in marking blocks, with the structural split and the full-page leak search; generated headings; names separate from printed numbers; `part`, `subpart`, `marked: no`, `labelled-boxes`; the `python-setup` block with `delivery`; the branding, `timer`, `breaks` and `maths_input` settings; both converters; and the paste package of §8, which needs nothing but the cheat sheet, the examples file and the checker. This replaces `parse_exam_file` and `check_exam`/`check_answer`/`check_marking` (`build_exam.py:111-640`). The prototype is about 1,500 lines, much of it messages; production code with a test per message is about two weeks.

**With each type as it lands** (`question-types.md` §10, T2–T4): `stimulus`, `matching`, `ordering`, label banks, drop-down gaps, numeric `tolerance`, `sf`, `dp` and `units`, and `checks`. **Later:** `math-expression` and `form`; the JSON Schema export for a connected model (§8); a colour setting, once Josh wants one (decision 12 says not yet).

| Decision | Recommendation | If not |
|---|---|---|
| Read values as text (PyYAML `BaseLoader`) rather than a new parser or StrictYAML | Yes: no new dependency, already runs in the studio | A 300-line parser of our own, only if error positions prove inadequate |
| Every secret only in marking blocks, including blank-filling answers (`{1}`) | Yes | Allow `{word}` inline for fill-in-the-blank alone, and strip it by rule |
| Headings made from `title:`; `#` to `###` refused | Yes | Headings attach to the block below them, which keeps the "(3 marks)" drift |
| Names written by people, proposed once from printed numbers | Yes | Names derived from position, which the 2025–26 maths paper showed to be fragile (`LESSONS_FROM_THE_EXPERIMENTS.md`) |
| A `subpart` level | Yes: the PDP Sample's 4B needs it | Invent a split of 4B's marks, which the conversion rules forbid |

---

## Evidence used

Research: `design-docs.md` §2, §9; `code.md` §1, §2, §4, §8; `pdp-pages.md` §1, §3, §9.3; `exam-types.md` §3, §7; `local-llm.md` §1, §7. This round's designs: `architecture.md` §0, §3.2–3.3, §6, §7; `question-types.md` §1, §2.2, §2.5, §5–§8, §10; `student-flow.md` §3.2, §5.2, §10, §11; `assistant.md` §1.5, §3.4, §4. Primary sources: `dewlab/dewmark/build_exam.py` (lines cited), `planning/THE_EXAM_FILE.md`, `QUESTION_TYPES_AND_MARKING.md`, `TRANSLATING_AN_EXISTING_EXAM.md`, `LESSONS_FROM_THE_EXPERIMENTS.md`, the five samples, and the four PDP pages' embedded sources.

Prototype, in `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/design-round/format-typed-blocks/` (Python 3.11, PyYAML 6.0.1, latex2mathml): `tb.py` (the checker; `python3 tb.py FILE --outline`), `emit.py`, `pdp2tb.py`, `old2tb.py`, `examples.exam.md` (section 6), `converted/pdp/` (the four PDP papers, plus `presentation-2027.exam.md` with §5's exam block), `converted/samples/` (the five samples), and `probe-marks.exam.md`, `broken.exam.md`, `broken-photosynthesis.exam.md` (the messages in §4 and §8), `probe-decisions.exam.md` and `probe-maths.exam.md` (the refusals added for the 27 September decisions: `timer: hidden`, `practice_reveal` on an exam, `maths_input: [typed, photos]`, which the checker answers with Did you mean "photo"?). `tb.round2-before-decisions.py` is the checker as it stood before the revision. Checking the largest file, the 1,450-line maths sample, takes about 80 ms, which fits the studio's check-as-you-type (`architecture.md` §3.3).
