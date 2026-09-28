# The exam file, paper-first

*Design round 2, 2026-09-27, revised after `planning/DECISIONS_2026-09-27.md`. One of three rival proposals for the one file a teacher writes. The argument: the file should read like the printed paper, followed by the printed marking scheme. It starts from the source format inside the four PDP 5N2927 pages (the `exam-src` block, read by `parseFrontmatter` and `parseExam` at `experiments/pdp-5n2927/PDP_5N2927_Exam_2027.html:1187` and `:1193`, and `questionList` at `:1364`) and adds only what marking and robustness need. The claims below were tested with a prototype reader (`paperfirst.py`, about 480 lines of Python) and a PDP converter (`pdp2paperfirst.py`, about 120 lines), both scratch work in `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/design-round/paper-first/`, not part of either repository.*

## The proposal in brief

1. **One file, two halves.** The top half is the paper as it would be printed. Below a line reading `# Marking scheme` is the marker's half, laid out the way schemes already are: under each question number. The student page is built from the top half only.
2. **Headings carry the numbers and the marks**, as on paper: `## Question 1: Functions (15 marks)`, `### 1(a): Parts of a function (6 marks)`. A heading counts only when it gives marks. The builder checks every sum.
3. **An answer box is a fence under its part.** A fence is a block that opens with three backticks and a word, and closes with three backticks. The word says what the student gets: `answer`, `python`, `boxes`, `choice` and so on.
4. **An answer's permanent name is the number printed beside it**, tidied: `1(b)(i): your tests` is stored as `q1b.i.your-tests`. Once a paper has been sat, the builder refuses a renumbering unless the paper's `version` changes.
5. **The three marking methods are recognised by how their lines look**: `- 2 marks: …` is a tick-box point; `- **Argument** (15 marks)` with bands indented below is a criteria grid; anything else is guidance for a mark out of a total.
6. **The four PDP papers convert by script** (a diff of 37 to 41 lines each) and pass every check. Their marking schemes, which none of them has, arrive as `(draft)` entries, and a draft cannot be issued as an exam.

---

## 1. The grammar

### 1.1 The carrier

An exam file is a plain text file, `<code>.exam.md`, with `pictures/` and `data/` folders beside it. It is read as **CommonMark**, the precisely specified dialect of Markdown, by one reader in pure Python (`markdown-it-py`), so the same code runs on the command line and inside the browser studio (decision 5). CommonMark fixes two PDP defects on its own (`pdp-pages.md` §3.4): `2 * 3 * 4` stays as written instead of turning into italics, and a four-backtick fence can hold a three-backtick one. Before reading, the builder tidies Windows line endings, tabs, non-breaking spaces and curly quotes in settings, headings and fence lines; today a PDP file saved with Windows line endings loses all its settings (`pdp-pages.md` §3.1).

On top of Markdown the format adds four things: settings between two `---` lines; `$…$` maths, typeset at build time; fences; and two reserved lines, `# Marking scheme` (required once) and `# Reference` (optional).

```
---
settings, one per line (§5)
---
the front page: everything before the first section or question
# Section A: …                  optional sections
## Question 1: … (15 marks)     questions, parts, boxes, material
# Reference                     optional cards for the side panel
# Marking scheme                the marker's half (§4)
```

### 1.2 Headings

| Written | Means |
|---|---|
| `# Section B: Answer any two questions (40 marks)` | A section (optional). "any N" sets a choice rule. |
| `## Question 3: Loops (20 marks)` | A question. It counts only if it ends in marks and carries a number. |
| `### 3(a): Tracing a loop (5 marks)` | A part; `### (a) …` also works. |
| `#### (i) First pass (2 marks)` | A sub-part, only when it has its own marks. |
| a heading with no marks | Ordinary text, such as `## Instructions to candidates`. Warned if it looks numbered. |

**Marks** are written `(N marks)`, `(1 mark)`, `[N marks]` or `[N]`; halves are allowed. **Numbers** take the usual printed styles: `Question 3`, `Q3`, `3(b)`, `3B`, `3b`, `3 (b)`, `3.b`, a bare `(b)` under Question 3, and `A1` or `B2(c)(ii)` for papers numbered by section. The prototype reads all eighteen spellings tried; every spelling of 1(a) becomes the name `q1a`.

### 1.3 Fences

````
```KIND  LABEL  (NOTE)
````

**KIND** is one word from the tables below; an unknown word is refused with the nearest match suggested, never shown quietly as code, which is what the PDP runtime does (`pdp-pages.md` §3.2). **LABEL** is a number, optionally followed by `: caption`, and is needed only when a part has two or more boxes. **NOTES** are `(not marked)`, `(choose 2)` and `(about 800 words)`. Everything after the kind is shown to the student as written.

**Answer boxes**

| Kind | The student gets | The body is |
|---|---|---|
| `answer` | A growing written box with a word count | Starter text (PDP's "Permitted: … Not permitted: …" scaffolds) |
| `maths` | A maths box in the routes the paper allows: plain text with a "reads as" line and symbol palette, a visual editor (MathLive), a photograph (decision 15) | Starter text |
| `python` | A code editor with Run, all cells sharing one Python session | Starter code |
| `essay` | A writing view with a word count against the note | Empty |
| `boxes` | One labelled box per line; `____` puts the box inside the line; a last line `Choose from: a / b / c` makes every box a drop-down | The labels |
| `blanks` | Text with gaps: `____` to type, `[a / b / c]` to choose | The text |
| `table` | A table with `____` in the cells to fill | A pipe table |
| `choice` | Options; `(choose N)` allows several | `A.`, `B.` …, each may hold Markdown and code |
| `match` | A drop-down of letters beside each numbered item | `1.`, `2.` …, then `A.`, `B.` … |
| `order` | A list to reorder, with keyboard buttons | `A.`, `B.` … |
| `photo` | A photograph of handwritten work, such as a drawn graph | The instruction |
| `on-paper` | "Answer 3(c) on the paper provided"; the mark is typed in the workbench | The instruction |

A box marked `(not marked)` is rough work: saved, printed, shown to the marker, never counted as unanswered. PDP's `fields` becomes `boxes`, because a non-programmer knows what a box is. A number answer is a `maths` working box plus a `boxes` answer line; label-the-diagram is a picture plus `boxes`. Neither needs a type of its own.

**Things students read**

| Written | Shown as |
|---|---|
| ` ```text ` | A code listing with line numbers and colouring (PDP's meaning); `text sql` and `start=4` also work |
| ` ```pseudo ` | Pseudocode, monospaced, not coloured |
| ` ```python setup ` | Code that runs before Begin, shown collapsed as "Set-up code (runs automatically)" |
| `![what it shows](pictures/cell.svg)` | A picture; the description is required |
| `[registry.db](data/registry.db)` | A data file, listed in the side panel and placed in Python's folder |
| `$\frac{k^2}{4}$` | Maths, typeset in prose, options, labels, table cells and keys |
| raw HTML | Shown as text, never run (PDP passes it through, so `If a<b` loses its text) |

**Shared material needs no syntax.** Text between a question heading and its first part belongs to the whole question, as on paper. When it holds a table, picture or listing, the page keeps it available beside every part.

### 1.4 The marker's half

| Line | Meaning |
|---|---|
| A heading that starts with a number: `### 2(a)`, `### 2(a): answer`, `## Question 2` | The entry for that part, box or question. Level does not matter. `(draft)` at the end marks it unchecked. |
| `Answer: …`, or `Answers:` and a numbered list; `Answers (any order):` | The key (§4.3) |
| `Model answer: …`, or a ` ```python ` block | The model answer |
| ` ```tests ` | Hidden tests for code (§4.4) |
| `- 2 marks: …` | A tick-box point |
| `- **Name** (15 marks)` with indented `- 13 to 15: …` | A criterion and its bands |
| `Topic:` / `Outcomes: 3, 7` | Fields for the marks spreadsheet and QQI records |
| anything else | Guidance for the marker |

---

## 2. Structure and marks

**Marks come only from headings.** A box shares the marks of the heading it sits under, which is how the PDP papers are marked: in the Sample, 1A (i), (ii) and (iii) share 3 marks and 4B's function and tests cells share 4. dewmark's current format forces a teacher to split marks like these (`pdp-pages.md` §9.3). In the workbench, the unit a marker marks is the lowest heading with marks, shown with all its boxes.

**The builder checks** that every heading's marks equal the sum of its children's; that a section which states marks adds up; that the paper equals `total marks` (a setting the PDP runtime never reads, `pdp-pages.md` §3.1); that no box in a question with parts sits outside every part, unless it is rough work; and that every marked part has a box.

**Marks are written twice on purpose.** A paper shows "(15 marks)" and each part's marks, and the builder checks that they agree, catching the commonest slip in a hand-written paper. This is not the hidden duplication `design-docs.md` §9 criticised (marks in an answer block and again in a marking block): both copies are on the page students read.

**"Answer any N" is read from the heading that says it**, which on paper is where it is said: `# Section B: Answer any two of Questions 2 to 4 (20 marks)`. A question heading can say it about its parts. The alternatives must be worth the same and outnumber N. There is no separate `choose:` key to fall out of step with the instructions, because the rule is the instruction. The page never blocks an extra attempt; the workbench counts the best N and lets the marker override.

**Faults run through the prototype:**

| Fault | Message (abridged) |
|---|---|
| 2(b) changed to 5 marks | "Question 2's parts add up to 11 marks, but its heading says 10." |
| A 12-mark question in an "any two" section of 10-mark questions | "Section B says 'any 2', but its questions are not all worth the same." |
| PDP's `**(ii) Counting a letter (5 marks).**` left in bold | "This line gives marks but is not a heading. Start the line with ####." |
| Two boxes labelled `2(a): working` | "Two answer boxes would both be stored as q2a.working (lines 99 and 102)." |
| `timer: hidden` | "'timer' can be enforced, none, shown, not 'hidden'." |

---

## 3. Answer spaces and their names

**Declaring a box.** Put a fence under its part. A lone box needs no label: an empty ` ```answer ` under `### 5(c)` is stored as `q5c`. When a part has more than one box, label each.

**The name rule**: `q`, the question number and part letter, then `.` and the sub-part numeral, then `.` and the caption in lower case with dashes. This is the form `assistant.md` §3.4 already uses when it names answers from printed numbers.

| As printed | Stored as |
|---|---|
| no label, under `### 1(a)` | `q1a` |
| `1A (i)`, `1(a)(i)`, `1a (i)` | `q1a.i` |
| `4(e): main limitation` | `q4e.main-limitation` |
| `Question 1: rough work (not marked)` | `q1.rough-work` |
| `B2(c)(ii)` | `qb2c.ii` |

**Why the printed number.** The student saw "2(b)". The scheme, the graded paper, an appeal and the external authenticator's sample all say "2(b)". A hidden identifier would be a second name that can drift from the first; the teacher could not see it, and a model converting a Word paper would have to invent it. dewlab learnt that a cell id is a contract. Here the contract is the number students were shown, and nobody renumbers a paper that has been sat.

**How names stay stable.** A names lock (a small file beside the paper, `architecture.md` §6) records each name at first issue, with its label, kind, part and marks.

- **Before first issue,** renumbering and reordering are free.
- **After a sitting,** changing a locked number stops the build unless `version` changes (§8 shows the message). A new version gets its own names; the old sitting keeps its scheme and record.
- **A caption-only fix** (same number, kind and position) keeps the stored name, and the builder says so.
- **Moving questions without renumbering** keeps every name, with a warning that the paper now reads 1, 3, 2.

Inside a box, a choice option is stored by its printed letter, `match` items by number, and `boxes` lines and `table` cells by position; the lock records their count and shape, and changes after a sitting are refused the same way.

---

## 4. Marking and model answers

### 4.1 Where the scheme lives

| | Inline after each box | `# Marking scheme` at the end (recommended) | A companion file |
|---|---|---|---|
| Reads like | Neither paper nor scheme | The paper, then its scheme, the pair QQI asks a provider to keep | Two documents |
| Keeping answers off the student page | Every renderer must skip every marking block (the gap `code.md` §1 found) | One split at one line, before anything is rendered | As at the end |
| Sending the paper to a moderator | Not without the answers | Send the top half | Send one file |
| Scheme beside its question | Yes | In the studio's split view | No |

The end of the file keeps one file, makes secrecy a matter of structure rather than of a list of fragments to strip, and matches what teachers already have: a Word paper and a Word scheme, numbered alike. The half can later move into `<code>.marking.md` unchanged. It is `#`, not `## Marking`, because `##` is the question level.

### 4.2 The three methods

Each part uses one method. The builder recognises it from the lines, refuses a part that mixes points with criteria, and says what it found in the preview ("Marked by points: 5 listed, up to 4 marks").

| Method | Written as | The marker gets | Checked |
|---|---|---|---|
| Marks out of a total | Guidance in any form | One number, in half-mark steps | none |
| Points with a limit | `- 2 marks: the enzyme is denatured` | Tick boxes; the total stops at the part's marks | points may add to more than the part ("any of") |
| Criteria grid | `- **Evidence** (15 marks)`, bands indented below | A band, then an exact mark, per criterion | criteria add to the part; bands run from 0 to the top with no gaps |

The limit is always the part's marks, so there is no `limit:` key to keep in step.

### 4.3 Keys, alternatives, numbers

| Box | Key |
|---|---|
| `choice` | `Answer: B`, or `Answer: A, C` with `(choose 2)` |
| `match` / `order` | `Answer: 1 B, 2 A, 3 C` / `Answer: B, D, C, A` |
| `boxes`, `blanks` | `Answer:` for one box; `Answers:` and a numbered list otherwise; `Answers (any order):` when boxes are interchangeable |
| `table` | The completed table |
| two keyed boxes in one part | One entry per box: `### 2(c): shape` |

- **Alternatives** are separated by a slash with spaces: `vacuole / large vacuole`. `3/8` is one answer.
- **A key that starts with a number is compared as a number:** `4.88 m ± 0.01` (value, unit, tolerance); `± 2%` (relative); `12.4 to 12.6 cm` (range); `(2 d.p.)`, `(3 s.f.)` (precision); `4/13` (fraction). `500`, `500.0` and `5e2` agree.
- **A quoted key**, such as `"0123"`, is compared exactly.

In line with decision 13, a key proposes a mark on a closed box ("matches key", "right value, no unit") and the marker confirms every mark.

### 4.4 Model answers, tests and drafts

- **Model answers**: a `Model answer:` paragraph or a ` ```python ` block. Shown in the answer key and the workbench, and on a practice paper after the student finishes (decision 14).
- **Hidden tests**: a ` ```tests ` fence, one test per line, either a Python expression that should be true (`longer_word("cat", "horse") == "horse"`) or `with input 17: output includes "junior"`. In the workbench a fresh Python session runs the set-up code, then the part's cells, then each line; the marker sees which pass, as evidence. On a practice paper with `practice tests` on, the same lines run in the student's page (decision 16). They are never placed in an exam page.
- **Drafts**: an entry ending `(draft)` is labelled "draft" everywhere, and an exam cannot be issued while one remains.

### 4.5 Keeping it off the student page

Exam pages are built from the paper half only. The builder then searches the whole built page, **including the embedded data block that today's check skips** (`code.md` §1, stage 5), for every key, model answer and test line of eight characters or more; short keys such as `B` exist only below the line, so structure protects them. A practice page receives keys, model answers and tests on purpose, locked until the student finishes, and the builder refuses `show answers` or `practice tests` on `kind: exam` (tested in the prototype).

---

## 5. Exam settings and presentation

Settings are `key: value` lines. Capitals, spaces, underscores and hyphens in a key are ignored, so `time_allowed` and `Time allowed` are the same key. Every value is text until the builder converts a key it knows, which removes YAML's traps (`no` becomes false, `1.10` becomes `1.1`, `code.md` §1) and PDP's rule that only lower-case `false` counts.

| Setting | Example | Needed |
|---|---|---|
| `dewmark` (format version) | `1` | written by templates |
| `code` (permanent: file names, save keys, lock) | `pdp-5n2927-exam-2027` | yes |
| `version` | `1` | default 1 |
| `kind` (sets the EXAMINATION or PRACTICE band, decision 12) | `exam`, `practice`, `sample` | yes |
| `title`, `module`, `module code` | Written Examination 2026–2027; Programming and Design Principles; 5N2927 | yes |
| `institution`, `college`, `session`, `logo` | Dublin and Dún Laoghaire ETB; Dublin College Dundrum; 2026–2027; `pictures/dcd-logo.svg` | recommended; logo optional |
| `total marks`, `time allowed` | 60; 2 hours | yes |
| `timer` (decision 11) | `none`, `shown`, `enforced` | default `shown`; the student can always hide it |
| `breaks` | `on`, `off` | default `off` |
| `student details` | full name, student number | default as shown |
| `hand in` (replaces the hard-coded Moodle text) | Upload your PDF and answer file to "PDP exam" on Moodle. | yes for an exam; the PDF is always produced (decision 10) |
| `calculator` | `none`, `basic`, `scientific` | default `none` |
| `maths input` (decision 15) | `text, visual, photo` | default `text` |
| `python from` (decision 7) | `this file`, `internet` | default `this file` |
| `python packages` | sqlite3, pandas | checked against the pinned Pyodide |
| `python time limit` | 10 seconds, or `off` | default 10 seconds |
| `code completion`, `error hints` | `on`, `off` | off, on |
| `python reference` | `yes`, `no` | default `no` |
| `show answers`, `practice tests` | `never`, `after finishing` (tests also `while working`) | practice and sample only |
| `weighting`, `technique` | 30%; Examination-Theory | optional, for QQI records |

**Branding** is these text settings plus the optional logo, shown on the combined start screen, the masthead, print headers and the PDF. There is no college colour yet, so the two bands mean the same in every college. **Reference sheets**: `python reference: yes` adds dewmark's standard Python sheet, and each `##` under `# Reference` becomes one side-panel card, which is where a formula sheet goes.

---

## 6. Worked examples

Examples (a) to (e) make one specimen paper, `specimen.exam.md` in the scratch folder. The prototype reads it with no problems: 7 questions, 23 boxes, 92 marks.

### (a) A PDP-style question: a code listing, Python cells and labelled boxes

````markdown
---
dewmark: 1
code: dewmark-specimen
version: 1
kind: practice
title: Specimen Paper
module: Specimen paper for the exam format
institution: Dublin and Dún Laoghaire ETB
college: Dublin College Dundrum
session: 2026–2027
total marks: 92
time allowed: 2 hours 30 minutes
timer: shown
calculator: scientific
maths input: text, visual, photo
python from: this file
python time limit: 10 seconds
code completion: on
python reference: yes
show answers: after finishing
practice tests: after finishing
hand in: Keep your PDF and answer file. In the real exam you will upload both to Moodle.
---

## Instructions to candidates

1. Answer Section A, **two** questions from Section B, Section C and Section D.
2. Your work saves as you go.

# Section A: Programming (15 marks)

## Question 1: Functions (15 marks)

### 1(a): Parts of a function (6 marks)

Study the following function. For each term below, give its name or value in this function, and explain what the term means.

```text
def shout_first_word(sentence: str) -> str:
    words = sentence.split()
    first = words[0]
    return first.upper() + "!"

print(shout_first_word("hello there friend"))
```

```boxes
Function name
Parameter(s)
Variable declaration(s)
Return statement
Function call
What would happen if the last line (the function call) were removed?
```

### 1(b): Writing functions (9 marks)

Write the following functions with clear comments, and write tests to show that each works.

#### (i) Longer word (4 marks)

Write a function named `longer_word` that takes two strings and returns whichever is longer. If both have the same length, it returns the first.

```python 1(b)(i): your function
# Write your function here
```

```python 1(b)(i): your tests
# Call your function and write your tests here
```

#### (ii) Counting a letter (5 marks)

Write a function named `count_letter` with two arguments, `text` and `letter`. It must use a loop to count how many times `letter` appears in `text`. Do not use `.count()`.

```python 1(b)(ii): your function
# Write your function here
```

```python 1(b)(ii): your tests
# Call your function and write your tests here
```

```python Question 1: rough work (not marked)
```
````

Scheme entries, below `# Marking scheme`:

````markdown
# Marking scheme

## Question 1

Topic: functions
Outcomes: 7, 8

### 1(a)

Answers:
1. shout_first_word
2. sentence
3. words, first
4. return first.upper() + "!"
5. shout_first_word("hello there friend")
6. Nothing is printed: the function is defined but never run.

- 1 mark: function name, with what a function name is
- 1 mark: parameter, with what a parameter is
- 1 mark: both variables, with what a declaration is
- 1 mark: the return statement, with what it does
- 1 mark: the call, with what a call does
- 1 mark: nothing is printed, because the function never runs

### 1(b)(i)

```python
def longer_word(first, second):
    # Return the longer string; on a tie, return the first one
    if len(second) > len(first):
        return second
    return first
```

```tests
longer_word("cat", "horse") == "horse"
longer_word("horse", "cat") == "horse"
longer_word("dog", "cat") == "dog"
```

- 2 marks: a working function with the right name and two parameters
- 1 mark: a tie returns the first string
- 1 mark: at least two tests that call the function

### 1(b)(ii)

```tests
count_letter("banana", "a") == 3
count_letter("", "a") == 0
```

- 2 marks: a loop that visits every character
- 1 mark: the count is returned, not printed
- 1 mark: `.count()` is not used
- 1 mark: at least two tests, including one where the letter is absent
````

### (b) Maths: "answer any 2 of 3", a number with tolerance and units, and typed maths

````markdown
# Section B: Answer any two of Questions 2 to 4 (20 marks)

Each question in this section is worth 10 marks. Show your working.

## Question 2: A ladder (10 marks)

A ladder 5.2 m long leans against a vertical wall. Its foot is 1.8 m from the wall, on level ground.

### 2(a): Height (6 marks)

How far up the wall does the ladder reach? Give your answer in metres, correct to two decimal places.

```maths 2(a): working
```

```boxes 2(a): answer
Height = ____ m
```

### 2(b): Angle (4 marks)

Find the angle between the ladder and the ground, correct to the nearest degree.

```maths 2(b): working
```

```boxes 2(b): answer
Angle = ____ °
```

## Question 3: A quadratic (10 marks)

### 3(a): Factorising (4 marks)

Factorise $x^2 - 2x - 8$.

```maths
```

### 3(b): Solving (6 marks)

Hence solve $x^2 - 2x - 8 = 0$.

```maths 3(b): working
```

```boxes 3(b): answer
x = ____
x = ____
```

## Question 4: Cards (10 marks)

A card is drawn at random from a standard deck of 52. Find the probability that it is a heart or a king, as a fraction in its lowest terms.

```maths 4: working
```

```boxes 4: answer
P(heart or king) = ____
```
````

Scheme entries:

```markdown
### 2(a)

Answer: 4.88 m ± 0.01

Model answer: $h = \sqrt{5.2^2 - 1.8^2} = \sqrt{23.8} = 4.878\ldots \approx 4.88$ m

- 3 marks: Pythagoras with the ladder as the hypotenuse
- 2 marks: correct working to 4.878
- 1 mark: 4.88 with the unit

### 2(b)

Answer: 70° ± 1

- 2 marks: $\cos\theta = 1.8 / 5.2$, or an equivalent ratio using 2(a)'s answer
- 1 mark: 69.7° before rounding
- 1 mark: 70°

Follow through from the student's own answer to 2(a).

### 3(a)

Answer: (x - 4)(x + 2)

Accept the factors in either order. An expanded answer earns no marks.

### 3(b)

Answers (any order):
1. 4
2. -2

- 2 marks: each factor set equal to zero
- 2 marks: x = 4
- 2 marks: x = -2

### 4

Answer: 4/13

- 2 marks: 13 hearts and 4 kings
- 3 marks: the king of hearts counted once, giving 16 cards
- 3 marks: 16/52
- 2 marks: 4/13 in lowest terms
```

### (c) Biology: a shared data table, a label bank and matching

````markdown
# Section C: Biology (17 marks)

## Question 5: Enzymes and cells (15 marks)

A student timed how long amylase took to break down starch at different temperatures.

| Temperature (°C) | 10 | 20 | 30 | 40 | 50 | 60 |
| --- | --- | --- | --- | --- | --- | --- |
| Time taken (minutes) | 14 | 8 | 4 | 2 | 5 | did not finish |

### 5(a): Reading the table (2 marks)

At which temperature did the amylase work fastest?

```boxes
Temperature = ____ °C
```

### 5(b): Rate (3 marks)

The rate of the reaction is 1 ÷ time taken. Work out the rate at 30 °C, to two decimal places, and give its unit.

```boxes
Rate = ____
```

### 5(c): The result at 60 °C (4 marks)

Explain why no result was recorded at 60 °C.

```answer
```

### 5(d): Parts of a cell (3 marks)

![A plant cell with three numbered pointers. Pointer 1 points to the thick outer boundary. Pointer 2 points to one of several small oval bodies near the edge. Pointer 3 points to the large pale space in the middle of the cell.](pictures/plant-cell-3.svg)

Name the parts labelled 1 to 3.

```boxes
1 ____
2 ____
3 ____
Choose from: cell wall / cell membrane / nucleus / chloroplast / vacuole / mitochondrion
```

### 5(e): What each part does (3 marks)

Match each part of a cell to its job. One job is not used.

```match
1. Mitochondrion
2. Ribosome
3. Chloroplast

A. Makes proteins
B. Releases energy in respiration
C. Absorbs light for photosynthesis
D. Controls what enters and leaves the cell
```
````

The table sits between the question heading and 5(a), so it is Question 5's shared material and stays available beside 5(a) to 5(e). Scheme entries:

```markdown
## Question 5

Topic: enzymes; cell structure
Outcomes: 2, 4

### 5(a)

Answer: 40

### 5(b)

Answer: 0.25 per minute ± 0.005

- 2 marks: 1 ÷ 4 = 0.25
- 1 mark: the unit, per minute or /min

### 5(c)

- 2 marks: the enzyme is denatured at 60 °C
- 1 mark: its active site has changed shape
- 1 mark: so starch no longer fits the active site
- 1 mark: a correct link to the fastest result at 40 °C

### 5(d)

Answers:
1. cell wall
2. chloroplast
3. vacuole / large vacuole / permanent vacuole

Do not accept "cell membrane" for 1.

### 5(e)

Answer: 1 B, 2 A, 3 C
```

### (d) Multiple choice, with an option that is code

`````markdown
## Question 6: Reading a loop (2 marks)

Which of these prints the numbers 1 to 5, one on each line?

````choice
A. `for n in range(5): print(n)`
B. `for n in range(1, 6): print(n)`
C.
   ```python
   n = 1
   while n < 5:
       print(n)
       n = n + 1
   ```
D. `print(range(1, 6))`
````
`````

Option C holds its own code block, so this fence uses four backticks. The answer is stored as the letter, so reordering options before issue is safe. Scheme entry: `### 6` then `Answer: B`.

### (e) An essay with a criteria grid

````markdown
# Section D: Essay (40 marks)

## Question 7: Recording lectures (40 marks)

"Every lecture should be recorded." Discuss.

Use the planning box first if it helps. It is handed in but carries no marks.

```answer 7: plan (not marked)
```

```essay (about 800 words)
```
````

Scheme entry:

```markdown
### 7

- **Argument and structure** (15 marks)
  - 13 to 15: one position, sustained; each paragraph advances it
  - 8 to 12: a clear position, developed unevenly
  - 4 to 7: drifts between positions or retells the title
  - 0 to 3: no discernible argument
- **Evidence and examples** (15 marks)
  - 13 to 15: specific named cases, examined rather than cited
  - 8 to 12: real examples, summarised rather than used
  - 4 to 7: generalities standing in for examples
  - 0 to 3: little or no evidence
- **Clarity and control of language** (10 marks)
  - 8 to 10: precise, controlled prose throughout
  - 4 to 7: clear overall, with lapses
  - 0 to 3: meaning is often unclear
```

Changing Clarity to `(8 marks)` gives "The criteria for 7 add up to 38, but it is worth 40" and "The bands for 'Clarity…' should run from 0 to 8".

---

## 7. Conversion

**PDP pages, by script.** The converter reads each page's `exam-src` block and changes only this: `exam_id` becomes `code`; `duration_minutes: 120` becomes `time allowed: 2 hours` with `timer: shown` (PDP's behaviour); `module` is split into module and code; the dead `reference_theory` key is dropped; switches become `on`/`off`; `python from` and `hand in` lines are added; the `#` line repeating the title goes; `(optional)` becomes `(not marked)` and `fields` becomes `boxes`; bold sub-part leads carrying marks become `####` headings; in 2027 only, four lines of HTML maths become `$…$` and the inline SVG flowchart becomes `pictures/…-figure-1.svg` with a placeholder description. A scheme skeleton follows, one `(draft)` entry per part. Every question, label, listing and starter text is kept as written.

| Paper | Source lines | Diff lines | Prototype result |
|---|---|---|---|
| Sample, Practice 1, Practice 2 | 266–270 | 37 each | 60 marks, 17 boxes (1 rough work), 13 draft entries, no problems |
| Exam 2027 | 456 | 41 | 60 marks, 28 boxes (2 rough work), 21 draft entries, no problems |

The parts found with shared marks are the ones `pdp-pages.md` §3.5 counted by hand (1A and 4B(i)/(ii) in the Sample; 2(d), 3(a), 4(e), 4(f) in 2027). **Effort:** the converter exists; per paper, 15 minutes comparing the preview with the original and one to two hours writing the scheme, which no format avoids; six to nine hours for all four. Old `pdp-exam/1` submissions import easily, because a PDP label is now the name: `"label": "1A (i)"` maps to `q1a.i`. One PDP instruction line ("a small box appears at the top of the screen") describes the old `input()` prompt and must be reworded by hand.

**dewmark's five samples, by script.** They are YAML blocks, so a converter can read them with `build_exam.py`'s own parser and write paper-first text: `question` blocks become headings with marks, `prompt` becomes prose, each `type` maps to a fence, `{word}` gaps become `____` with the answer moved to `Answers:`, `marking` blocks move below the line, `choose: 2` becomes "Answer any two" in the section heading, `reference` blocks become `# Reference` cards, and `setup_code` becomes a `python setup` fence. It must place headings by position, because today's parser attaches each heading to the previous question (`code.md` §1). **Effort:** about 250 lines and a day to write, a day to review, mostly on the maths 5N18396 sample and its 70 boxes. No sample has been sat, so their names can change freely.

---

## 8. Translation by a language model

**Why a model gets this format right.**

- **The output looks like the input.** A Word exam is already numbered headings with "(15 marks)", and a Word scheme already reads "1(a) … 2 marks …". The model mostly copies and adds a fence where a box goes. Its one judgement, what kind of box a part needs, is the one a teacher would make.
- **Few ways to fail.** Markdown is what models write most reliably. No indentation matters except criteria bands; there are no quoting rules and no YAML typing; the vocabulary is twelve box words, three material words and `tests`.
- **The model invents no names**; they come from the printed numbers.
- **Coverage is checked by plain text matching.** The paper half keeps the teacher's sentences, so a check that every source paragraph appears once, or is listed as left out, is a text comparison. That makes decision 19's modes easy to show: "copy without composing" should produce a paper half almost identical to the Word text, and every change made by "tidy the wording" or "rephrase commands as invitations" appears as a plain diff the teacher reads line by line.
- **The paste route (decision 20) needs only this document's cheat sheet** and the specimen paper; both are short Markdown, the natural thing to paste into any assistant, and the reply is checked by the same builder.

**What goes wrong.** Markdown forgives, so a plausible file can mean something else. A model may write `**Question 1** (15 marks)` in bold, write "(3m)", nest a part at the wrong level, or helpfully put the solution in the starter text. The first three are caught by the warning about marks on a line that is not a heading, the warning about numbered headings without marks, and the sums. The last is caught by the check that no scheme text appears above the line.

**Three builder messages, as a teacher reads them:**

> **Line 91 · Question 2 · marks don't add up**
> Question 2's parts add up to 11 marks, but its heading says (10 marks).
> 2(a) is 6 marks and 2(b) is 5 marks.
> Change one part's marks, or change the heading.

> **Line 123 · Question 3 · students would see this**
> This line starts "Model answer:", but it is above the # Marking scheme line, so every student would read it.
> Move it below # Marking scheme, under a heading ### 3(a).

> **Line 113 · 2(b) · already sat**
> Students sat this paper on 20 October 2026 (Group A), and their answers to 2(b) are stored under that number. This file no longer has a 2(b): the part on line 113 is now numbered 2(c).
> If this is next year's paper, change `version: 1` to `version: 2` at the top. The October sitting keeps its own copy and its marks.
> If the change was a slip, put the number back to 2(b).

---

## 9. What a teacher has to learn: the cheat sheet

````
THE DEWMARK EXAM FILE ON ONE PAGE
Write the paper as it would be printed. Write the marking scheme underneath it.

1  SETTINGS go at the very top, between two lines of three dashes.
   ---
   code: bio-5n2746-jan-2027          (never change this once students have sat it)
   kind: exam                         (or practice, or sample)
   title: January Examination
   module: Biology
   module code: 5N2746
   total marks: 100
   time allowed: 2 hours
   timer: shown                       (or none, or enforced)
   hand in: Upload your PDF and answer file to "Biology exam" on Moodle.
   ---

2  THE FRONT PAGE is anything before the first question: the instructions.

3  NUMBERS AND MARKS GO IN HEADINGS. A heading with marks is a question or a part.
   # Section B: Answer any two questions (40 marks)    optional; "any two" is understood
   ## Question 3: Enzymes (20 marks)
   ### 3(a): Reading the graph (5 marks)                or just ### (a) ...
   #### (i) The optimum (2 marks)                       only if a sub-part has its own marks
   Parts must add up to their question, questions to the total. dewmark checks.

4  AN ANSWER BOX is a fence under its part: three backticks and one word.
   ```answer    a written answer (anything inside is what the box starts with)
   ```maths     written maths, with a preview and symbols
   ```python    code the student writes and runs (inside: the starting code)
   ```essay (about 800 words)
   ```boxes     one box per line; ____ shows where the box goes;
                a last line "Choose from: a / b / c" makes drop-downs
   ```blanks    sentences with ____ gaps, or [a / b / c] to choose from
   ```table     a table with ____ in the cells to fill
   ```choice    options A. B. C. D.   add (choose 2) for more than one
   ```match     1. 2. 3. to be matched with A. B. C. D.
   ```order     A. B. C. to put in order
   ```photo     a photograph of handwritten work
   ```on-paper  the student answers on paper; you type the mark in later
   End every box with three backticks on a line of their own.
   Two boxes in one part? Label them:  ```python 4(b): your function
   A box with no marks (rough work, a plan): add (not marked).

5  THINGS STUDENTS READ BUT CANNOT CHANGE
   ```text      code with line numbers      ```pseudo    pseudocode
   ![say what the picture shows](pictures/cell.svg)    $x^2 - 4$ for maths
   A table or picture right under a question heading stays in view for all its parts.

6  THE MARKING SCHEME comes after the paper, under one line:
   # Marking scheme
   ### 3(a)                          the part's number, as printed
   Answer: B                         a letter, a word or a number
   Answer: 4.88 m ± 0.01             a number, its unit, and how close counts
   Answers:                          one per box or gap, in order
   1. cell wall
   2. vacuole / large vacuole        " / " separates accepted answers
   Model answer: ...                 or a ```python block
   - 2 marks: a point to tick        the part's marks are the limit
   - **Argument** (15 marks)         a criteria grid, bands indented under it
     - 13 to 15: ...
   Anything else is guidance for the marker.
   Put (draft) after a heading you have not checked; an exam can't be issued until you remove it.

AFTER STUDENTS HAVE SAT A PAPER, DO NOT RENUMBER IT. For next year, change version: 1 to version: 2.
````

---

## 10. Self-critique

**1. Meaning rests on small written conventions**: "(3 marks)" and not "(3m)"; "any two" in a heading; `2 marks:` with a colon; " / " with spaces for alternatives; `____` for a gap; "(not marked)". The prototype catches every slip tried, but they are all the same kind of error, something written slightly differently that means something else, and one slip can set off several messages (deleting one heading's marks produced four). The builder must list the cause first, and the preview must say what it read, with an outline of marks and "Marked by …" labels. **What breaks first** is a scheme pasted from Word or written by a model: "Award 2 marks for …", "(2)" and "2m" are read as guidance, not tick-box points. That is safe, since the marker still types a number, but the tick boxes disappear without comment unless the builder warns when a guidance line starts with a number of marks.

**2. Two halves joined by numbers, and names that are numbers.** The scheme sits away from its question (the studio's split view helps). Renumbering before issue means editing two places, both cross-checked. After a sitting, renumbering is refused outright unless the version changes; comparing a question across years then needs a "2(c) was 2(b)" map, which is not built. Captions are part of names, so fixing a caption after a sitting depends on the caption-only rule, one more piece of logic that has to be right.

**3. Light syntax grows into small languages.** Numeric keys have their own phrasing (±, to, %, d.p., s.f., units); tests have a second, bands a third. Each new need adds a phrase: stricter significant figures, per-cell table marks, randomised versions. A typed-block format would add a key for each, easier to check and harder to write. Without discipline this format would be harder to learn than YAML by its tenth question type. The rule must be one phrase per question type, each with its own tests and one line on the cheat sheet; a need that cannot be said in one short line waits. The format also departs from dewlab's `question` fence, which writes `{word}` gaps with the answer inline (`build.py` `parse_question`, line 1515; `DECISIONS_LOG.md` 7.179): right for a tutorial, wrong for an exam, so moving a tutorial self-check into a paper takes a mechanical rewrite.

---

## What ships first, and what waits

**First**, with the move and the data-loss fixes, because the format must freeze before the first sitting: the whole grammar written down, including kinds whose renderers come later (an unknown kind is refused, so adding a renderer never changes the format); the reader, with settings, headings, sums, names and the lock; the kinds the PDP papers and samples use (`answer`, `python`, `boxes`, `essay`, `choice`, `blanks`, `table`, `text`, `pseudo`, `python setup`, with `maths` shown as plain text until its preview exists); the marker's half (`Answer:`, `Model answer:`, points, criteria, guidance, `(draft)`); `timer` and `breaks`; the PDP converter; and the cheat sheet plus specimen as the paste-route package.

**Second**: `match`, `order`, `photo`, `on-paper` and `Choose from:` banks; the maths preview, palette and MathLive; number-key proposals and `tests` in the workbench and practice pages; `show answers`; the samples converter.

**Later**: the companion scheme file; the "was" map across versions; rubric tables pasted from Word; paper variants.

## Decisions for Josh

1. **Where the scheme lives**: at the end of the same file under `# Marking scheme` (recommended), in a companion file, or inline after each box.
2. **Names are the printed numbers** (recommended). A paper that has been sat cannot be renumbered without a new version.
3. **Gaps are `____` with answers in the scheme** (recommended), departing from dewlab's `{word}`.
4. **`fields` becomes `boxes`** (recommended), and PDP's `text` keeps its meaning of a numbered code listing.
5. **When practice tests run**: after the student finishes, matching decision 14 (recommended), or while working, which decision 16 allows but which gives question-by-question feedback.
6. **Set-up code is shown to students, collapsed** (recommended); the HVIT paper's instructions already describe it.
