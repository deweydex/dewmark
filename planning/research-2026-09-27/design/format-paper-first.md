# The exam file, paper-first

*Design round 2, 2026-09-27. One of three rival proposals for the one file a teacher writes. It argues that the file should read like the printed paper followed by the printed marking scheme. It starts from the source format inside the four PDP 5N2927 pages (the `exam-src` block, read by `parseExam` at `experiments/pdp-5n2927/PDP_5N2927_Exam_2027.html:1187-1219`) and adds only what marking and robustness need. I tested the claims with a prototype reader (about 460 lines of Python) and a PDP converter (about 120 lines). Both are scratch work in `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/design-round/paper-first/`, not part of either repository.*

## The proposal in brief

1. **One file, two halves.** The top half is the paper, written as it would be printed. Below a line reading `# Marking scheme` is the marker's half, written the way schemes already are: under each question number. The student page is built from the top half only, so it is built from text that holds no answers.
2. **Headings carry the numbers and the marks**, as on paper: `## Question 1: Functions (15 marks)`, `### 1(a): Parts of a function (6 marks)`. A heading counts only when it gives marks. The builder checks every sum.
3. **An answer box is a fence under its part.** A fence is a block that opens with three backticks and a word and closes with three backticks. The word names what the student gets: `answer`, `python`, `boxes`, `choice` and so on.
4. **An answer's permanent name is the number printed beside it**, tidied: `1(b)(i): your tests` is stored as `q1b.i.your-tests`. After a sitting, the names lock refuses a renumbering unless the paper's `version` changes.
5. **The three marking methods are recognised by how their lines look.** Tick-box points are written `- 2 marks: …`. A criteria grid is written `- **Argument** (15 marks)` with its bands indented below. Anything else is guidance for a mark out of a total.
6. **The four PDP papers convert by script, with 32 to 36 changed lines each, and pass the prototype's checks.** The marking schemes, which none of them has, arrive as `(draft)` entries, and a draft cannot be issued as an exam.

---

## 1. The grammar

### 1.1 The carrier

An exam file is a UTF-8 text file, `<code>.exam.md`, with `pictures/` and `data/` folders beside it. It is read as **CommonMark**, the fully specified dialect of Markdown, by one reader written in pure Python (`markdown-it-py`), so it can run in the studio's in-browser Python as today's Markdown library does (`architecture.md` §4). CommonMark fixes two PDP bugs on its own (`pdp-pages.md` §3.4). First, `2 * 3 * 4` stays as written instead of becoming italics. Second, a four-backtick fence can contain a three-backtick one. On top of Markdown the format adds four things:

- **settings** between two `---` lines at the very top;
- **`$…$` maths**, typeset at build time;
- **fences**, for answer boxes and for things students read;
- **one reserved line**, `# Marking scheme`, and **one optional line**, `# Reference`.

Before reading anything, the builder tidies Windows line endings, tabs, non-breaking spaces, and curly quotes and dashes in settings, headings and fence lines. At present a PDP file with Windows line endings loses all its settings (`pdp-pages.md` §3.1).

```
---
settings, one per line (§5)
---
the front page: everything before the first section or question
# Section A: …                  optional sections
## Question 1: … (15 marks)     questions, parts, boxes, material
# Reference                     optional: cards for the side panel
# Marking scheme                the marker's half (§4)
```

### 1.2 Headings

| Written | Means | Rule |
|---|---|---|
| `# Section B: Answer any two questions (40 marks)` | A section | Optional. Marks are checked when given. "any N" (digits or one to ten) sets a choice rule. |
| `## Question 3: Loops (20 marks)` | A question | Counts only when it ends in marks; it must carry a number |
| `### 3(a): Tracing a loop (5 marks)` | A part | Also written `(a)`; it belongs to the question above it |
| `#### (i) First pass (2 marks)` | A sub-part with its own marks | Only when a sub-part has its own marks |
| a heading with no marks | Ordinary text, such as `## Instructions to candidates` | Warned if it looks numbered |

**Marks** are written `(N marks)`, `(1 mark)`, `[N marks]` or `[N]`, and halves are allowed. **Numbers** may take any of the usual printed styles: `Question 3`, `Q3`, `3(b)`, `3B`, `3b`, `3 (b)`, `3.b`; `(b)` under Question 3 and `(ii)` under 3(b); and `A1` or `B2(c)(ii)` in papers numbered by section. The prototype reads all eighteen spellings I tried; every spelling of 1(a), including `(a)` under Question 1, becomes the same name, `q1a`.

### 1.3 Fences

````
```KIND  LABEL  (NOTE)
````

**KIND** is one word from the two tables below. An unknown word is refused. It is never quietly shown as code, which is what the PDP runtime does (`pdp-pages.md` §3.2). **LABEL** is a number, optionally followed by `: caption`. It is needed only when a part has two or more boxes. **NOTES** are `(not marked)`, `(choose 2)` and `(about 800 words)`. Everything on the line except the kind is shown to the student as written.

**Answer boxes**

| Kind | The student gets | The body is | Registry type (`question-types.md` §2) |
|---|---|---|---|
| `answer` | A growing written box, sized from the marks, with a word count | Starter text (PDP's "Line 1: … Line 12:" scaffolds) | written answer |
| `maths` | A written box with a "Reads as" preview and a symbol palette, stored as plain text | Starter text | written answer + maths feature |
| `python` | An editor with Run, sharing one Python session | Starter code | python-code |
| `essay` | A writing view with a word count against the note | Empty | essay |
| `boxes` | One labelled box per line. `____` places the box inside the line; a last line `Choose from: a / b / c` makes every box a drop-down | The labels | labelled boxes |
| `blanks` | Text with gaps: `____` to type, `[a / b / c]` to choose | The text | fill in the blank |
| `table` | A table with `____` in the cells to fill | A pipe table | complete the table |
| `choice` | Options; `(choose N)` allows several | `A.`, `B.` … each may hold Markdown, including code | multiple choice |
| `match` | A drop-down of letters beside each numbered item | `1.`, `2.` …, then `A.`, `B.` … | matching |
| `order` | A list to reorder with keyboard buttons | `A.`, `B.` … as shown | ordering |
| `on-paper` | "Answer 3(c) on the paper provided"; the mark is typed in the workbench | The instruction | answer on paper |

Any box marked `(not marked)` becomes rough work: it is saved, printed and shown to the marker, but it carries no marks and never counts as unanswered. PDP's `fields` becomes `boxes`, because a non-programmer knows what a box is; the converter renames it. Three of today's types become combinations, which leaves the registry fewer types to build and test:

- `numeric-answer` becomes a `maths` working box plus a `boxes` answer line;
- `label-the-diagram` becomes a picture plus `boxes` labelled 1, 2, 3;
- `describe-a-sketch` becomes a `choice` plus `boxes`.

**Things students read**

| Written | Shown as |
|---|---|
| ` ```text ` | A code listing with line numbers and Python colouring (PDP's meaning); `text sql` and `start=4` also work |
| ` ```pseudo ` | Pseudocode: monospaced, not coloured |
| ` ```python setup ` | Code that runs before Begin, shown collapsed as "Set-up code (runs automatically)" |
| `![what it shows](pictures/cell.svg)` | An embedded picture; the description is required |
| `[hvit_registry.db](data/hvit_registry.db)` | An embedded data file, listed in the side panel and placed in Python's folder |
| `$\frac{k^2}{4}$` | Maths, typeset everywhere: prose, options, box labels, table cells, keys |
| raw HTML | Shown as text and never run (PDP passes it through, so `If a<b` loses its text) |

**Shared material needs no syntax.** Text between a question heading and its first part belongs to the whole question, as it does on paper. When that text holds a table, picture or listing, the page keeps it available beside every part. Text between a section heading and its first question works the same way for the section.

### 1.4 The marker's half

| Line | Meaning |
|---|---|
| A heading that starts with a number: `### 2(a)`, `### 2(a): answer`, `## Question 2` | The entry for that part, box or question. The heading level does not matter; `(draft)` at the end marks it unchecked |
| `Answer: …`, or `Answers:` and a numbered list; `Answers (any order):` | The key (§4.3) |
| `Model answer: …`, or a ` ```python ` block | The model answer or model code |
| ` ```tests ` | Hidden tests, run only in the workbench |
| `- 2 marks: …` | A tick-box point |
| `- **Name** (15 marks)` with indented `- 13 to 15: …` lines | A criterion and its bands |
| `Hint:` / `Topic:` / `Outcomes: 3, 7` | Practice-only hint; export and QQI fields |
| anything else | Guidance for the marker |

Besides the sums and names in §2 and §3, the builder refuses unknown settings and fence words (suggesting the nearest match), `Answer:` or `Model answer:` above the scheme line, any scheme text repeated in the paper half (a model answer pasted in as starter text), and dewlab-style `{word}` gaps, which would print the answer.

---

## 2. Structure and marks

**Marks come only from headings.** A box shares the marks of the heading it sits under, which is how the PDP papers are marked. In the Sample, 1A (i), (ii) and (iii) share 3 marks, and 4B's function and tests cells share 4. dewmark's current format forces the teacher to split marks like these (`pdp-pages.md` §9.3, gap 3). In the workbench, the unit a marker marks is the lowest heading that has marks, shown with all its boxes.

**The builder checks that:**

- every heading's marks equal the sum of its children's;
- any section that states marks adds up;
- the paper's sum equals `total marks`, a setting the PDP runtime never reads;
- no box in a question with parts sits outside every part, unless it is rough work;
- every marked part has a box or is `on-paper`.

**Printed marks are written twice on purpose.** A paper shows "(15 marks)" and each part's marks, and the builder checks that they agree, which catches the commonest slip in a hand-written paper. This is not the hidden duplication `design-docs.md` §9 criticised (marks in both an answer block and a marking block): both copies are on the page students read.

**"Answer any N" is read from the heading that says it**, which on paper is where it is said: `# Section B: Answer any two of Questions 2 to 4 (20 marks)`. A question heading can say it about its parts. The alternatives must be worth the same, and there must be more of them than N. Parts nested inside alternatives are summed first. There is no `choose:` key to fall out of step with the instructions, because the rule is the instruction. The page never blocks an extra attempt. The workbench counts the best N and allows an override, as `THE_MARKING_WORKBENCH.md` already plans.

**Hostile cases run through the prototype:**

| Case | Result |
|---|---|
| 2(b) changed to 5 marks | "2's parts add up to 11 marks, but its heading says 10." |
| A 12-mark question in an "any two" section of 10-mark questions | "…says 'any 2', but its questions are not all worth the same", then the section and paper sums |
| `(4 marks)` deleted from `### 5(c)` | A warning that the heading "looks like a part but gives no marks", then three knock-on problems. The builder must list the cause first (§10) |
| PDP's `**(ii) Counting a letter (5 marks).**` left in bold | "This line gives marks but is not a heading… start the line with ####." |
| Two boxes labelled `2(a): working` | "Two answer boxes would both be stored as q2a.working (lines 99 and 102)." |
| `boxes 2(c): answer` placed under 2(b) | "The box labelled '2(c): answer' sits under 2(b)." |
| `version: 1.10`, `code: 0123`, `calculator: no` | Read as `1.10`, `0123` and off; values stay text until a known key converts them |

---

## 3. Answer spaces and their names

**Declaring a box.** Put a fence under its part. A lone box needs no label: an empty ` ```answer ` under `### 5(c)` is stored as `q5c`. When a part has more than one box, label each one.

**The name rule.** The name is built from these pieces, in order:

1. `q`;
2. the question number and the part letter (whether the number is written in full or relative to its heading);
3. `.` and the roman numeral of the sub-part;
4. `.` and the caption, in lower case with dashes.

This matches the form `assistant.md` §3.4 already uses when it names answers from printed numbers (`1A (ii)` becomes `q1a.ii`).

| As printed | Stored as |
|---|---|
| no label, under `### 1(a)` | `q1a` |
| `1A (i)`, `1(a)(i)`, `1a (i)` | `q1a.i` |
| `4(e): main limitation` | `q4e.main-limitation` |
| `Question 1: rough work (not marked)` | `q1.rough-work` |
| `B2(c)(ii)` | `qb2c.ii` |

**Why the printed number.** The student saw "2(b)". The scheme, the graded paper, an appeal and the internal verifier's sample all say "2(b)". A hidden identifier would be a second name that can drift from the first. The teacher could not see it, and a model converting a Word paper would have to invent it. dewlab learnt that cell ids are a contract. Here the contract is the number students were shown, and nobody renumbers a paper after it has been sat.

**How names stay stable.** The names lock (`architecture.md` §6) records each name at first issue, with its label, kind, part and marks.

- **Before the first issue,** renumbering is free.
- **After a sitting,** changing a locked number stops the build unless `version` changes (§8 shows the message). A new version gets its own names; the old sitting keeps its scheme and record. So "renumber 2(b) to 2(c) after a sitting" ends in one of two clear outcomes: put the number back, or make the paper version 2.
- **A caption-only fix** (same number, same kind, same position, caption edited) keeps the stored name, and the builder says so.
- **Reordering questions without renumbering** keeps every name, with a warning that the paper now reads 1, 3, 2.
- **Later,** a "2(c) was 2(b)" map in the lock carries item statistics across versions.

**Inner names.** A choice option is stored by its printed letter, so a key never depends on position. `boxes` lines and `table` cells are stored by position, and the lock records their count or shape. `match` items are stored by number. After a sitting, changing any of these is refused in the same way (`question-types.md` §2.2).

---

## 4. Marking and model answers

### 4.1 Where the scheme lives

| | Inline after each box | `# Marking scheme` at the end (recommended) | A companion file |
|---|---|---|---|
| Reads like | Neither a paper nor a scheme | The paper, then its scheme: the pair QQI asks a provider to keep | Two documents |
| Keeping keys off the student page | Every renderer must skip every marking block, with a leak check per type (`code.md` §1) | One split at one line, before anything is rendered | As at the end |
| Sharing the paper with a moderator | Not without the answers | Send the top half | Send one file |
| Scheme beside its question | Yes | In the studio's split view | No |
| Drift | None | Numbers in two places, cross-checked both ways | The same, plus a file that can go missing |

The end of the file keeps one file, makes secrecy a matter of structure rather than of a list of fragments to strip, and matches what teachers already have: a Word paper and a Word scheme, numbered alike. The half can later move into `<code>.marking.md` unchanged. It is `#`, not `## Marking`, because `##` is question level.

### 4.2 The three methods

Each part uses one method. The builder recognises it from the lines, refuses a part that mixes points with criteria, and names the method it found in the answer-key preview ("Marked by points: 5 listed, up to 4 marks").

| Method | Written as | The marker gets | Checked |
|---|---|---|---|
| Marks out of a total | Guidance in any form | One number, in half-mark steps | none |
| Points with a limit | `- 2 marks: the enzyme is denatured` | Tick boxes; the total stops at the part's marks | none; points may add up to more than the part ("any of") |
| Criteria grid | `- **Evidence** (15 marks)` with indented `- 13 to 15: …` bands | A band, then an exact mark, per criterion | the criteria add up to the part; the bands run from 0 to the top with no gaps or overlaps |

The limit is always the part's marks, so there is no `limit:` to keep in step. Error carried forward stays as guidance, because the marker applies it.

### 4.3 Keys, alternatives, numbers

| Box | Key |
|---|---|
| `choice` | `Answer: B`, or `Answer: A, C` with `(choose 2)` |
| `match` / `order` | `Answer: 1 B, 2 A, 3 C` / `Answer: B, D, C, A` |
| `boxes`, `blanks` | `Answer:` for one box; otherwise `Answers:` and a numbered list in order; `Answers (any order):` when the boxes are interchangeable |
| `table` | The completed table, the same shape as in the paper |
| two keyed boxes in one part | One entry per box: `### 2(c): shape` |

- **Accepted alternatives** are separated by a slash with spaces around it: `vacuole / large vacuole`. `3/8` is one answer.
- **A key that starts with a number is compared as a number:**
  - `4.88 m ± 0.01` gives a value, a unit and a tolerance;
  - `± 2%` gives a relative tolerance;
  - `12.4 to 12.6 cm` gives a range;
  - `(2 d.p.)` and `(3 s.f.)` give the precision;
  - `4/13` is a fraction;
  - `500`, `500.0` and `5e2` all agree.
- **A quoted key**, such as `"0123"`, is compared exactly as written.

The workbench uses keys only to suggest, for example "matches key", "right value, no unit" or "same value, not in lowest terms". The marker confirms every mark (`question-types.md` §2.5).

### 4.4 Model answers, tests and drafts

- **Model answers.** A `Model answer:` paragraph or a ` ```python ` block. It appears in the answer key and the workbench, and in practice papers when `show answers` allows it.
- **Hidden tests.** A ` ```tests ` fence has one test per line, in one of two forms:
  - a Python expression that should be true, such as `longer_word("cat", "horse") == "horse"`;
  - `with input 17: output includes "junior"`, which feeds typed input to the student's program.

  Tests run only in the workbench. A fresh Python session runs the paper's set-up code, then the part's own cells in order, then each line. The marker sees the results beside the model answer's results, as evidence and never as a mark.
- **Drafts.** An entry ending `(draft)` is labelled "draft" everywhere, and an exam cannot be issued while one remains.

### 4.5 Keeping it off the student page

Student and practice pages are built from the paper half only. The builder then searches the whole built page, **including the embedded data block that today's check skips** (`code.md` §1, stage 5), for every key, model answer and test line of eight characters or more. Short keys such as `B` or `500` are protected by structure, because they exist only below the line. A practice or sample paper receives keys and hints on purpose, through `show answers` and `Hint:`. The builder refuses `show answers` on `kind: exam`.

---

## 5. Exam settings and presentation

Settings are `key: value` lines. Capitals, spaces, underscores and hyphens in a key are ignored, so `time_allowed` and `Time allowed` are the same key. Every value is text until the builder converts a key it knows: to a number, to a list separated by commas, or to a switch (`on`/`off`, `yes`/`no`, `true`/`false`, in any capitals). This removes YAML's traps, where `no` becomes false and `1.10` becomes `1.1` (`code.md` §1), and PDP's rule that only a lower-case `false` counts.

| Setting | Example | Needed |
|---|---|---|
| `dewmark` (format version) | `1` | written by templates |
| `code` (permanent; file names, save keys, lock) | `pdp-5n2927-exam-2027` | yes |
| `version` | `1` | default 1 |
| `kind` (sets the cover band and what practice may show) | `exam`, `practice`, `sample` | yes |
| `title` | Written Examination 2026–2027 | yes |
| `module`, `module code` | Programming and Design Principles; 5N2927 | yes; code recommended |
| `institution`, `college`, `session` | Dublin and Dún Laoghaire ETB; Dublin College Dundrum; 2026–2027 | recommended |
| `logo`, `logo dark` | `pictures/dcd-logo.svg` | optional |
| `total marks`, `time allowed` | 60; 2 hours | yes |
| `weighting`, `technique` (QQI, `exam-types.md` §4) | 30%; Examination-Theory | optional |
| `student details`, `number example` | full name, student number; D00123456 | default as shown |
| `hand in` (replaces the hard-coded Moodle text) | Upload your file to "PDP exam" on Moodle, then raise your hand. | yes for an exam |
| `timer` | `shown`, `hidden`, `off` | default `shown`, never enforced |
| `calculator` | `none`, `basic`, `scientific` | default `none` |
| `python packages` | sqlite3, pandas, matplotlib | checked against pinned Pyodide; anything needing PyPI during the sitting is refused |
| `python time limit` | 10 seconds, or `off` | default 10 seconds |
| `code completion` / `error hints` | `on`, `off` | off / on in practice and off in an exam, as the PDP papers chose |
| `python reference` | `yes` | default `no` |
| `show answers` | `never`, `on request`, `after finishing` | practice only |

**Branding** is these text settings plus an optional logo. It appears on the cover, the masthead, print headers and the answer file as `student-flow.md` §11.2 lays out. There is no college colour in the first release, so the exam and practice bands mean the same thing in every college. **Reference sheets** are `python reference: yes` for dewmark's standard Python sheet, and anything under `# Reference`, where each `##` becomes one side-panel card; a formula sheet goes there. **How Python reaches the room** is chosen at Issue rather than written in the paper, since one paper may be sat in several rooms (`architecture.md` §3.4).

---

## 6. Worked examples

Together, examples (a) to (e) make one specimen paper. The settings in (a) head the file, the `# Reference` card closes the paper half after the essay in (e), and the scheme entries follow `# Marking scheme` in question order. Assembled that way, the prototype reads the file with no problems: 7 questions, 23 boxes, 92 marks. The specimen crosses subjects, as no real paper would.

### (a) A PDP-style question: a code listing, Python cells and labelled boxes

````markdown
---
dewmark: 1
code: dewmark-specimen
kind: practice
title: Specimen Paper
module: Specimen paper for the exam format
institution: Dublin and Dún Laoghaire ETB
college: Dublin College Dundrum
session: 2026–2027
total marks: 92
time allowed: 2 hours 30 minutes
calculator: scientific
python time limit: 10 seconds
code completion: on
python reference: yes
show answers: after finishing
hand in: Keep your answer file. In the real exam you will upload it to Moodle and raise your hand.
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

Write the following functions with clear comments, and write tests to show that each function works.

#### (i) Longer word (4 marks)

Write a function named `longer_word` that takes two strings and returns whichever is longer. If both have the same length, it returns the first.

```python 1(b)(i): your function
# Write your function here
```

```python 1(b)(i): your tests
# Call your function and write your tests here
```

#### (ii) Counting a letter (5 marks)

Write a function named `count_letter` with two arguments, `text` and `letter`. It must use a loop to count how many times `letter` appears in `text`, and return the count. Do not use `.count()`.

```python 1(b)(ii): your function
# Write your function here
```

```python 1(b)(ii): your tests
# Call your function and write your tests here
```

You can use this cell for rough work.

```python Question 1: rough work (not marked)
```
````

The marking scheme entries:

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

Each question in this section is worth 10 marks. Show your working in the working boxes.

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

A card is drawn at random from a standard deck of 52 cards. Find the probability that it is a heart or a king. Give your answer as a fraction in its lowest terms.

```maths 4: working
```

```boxes 4: answer
P(heart or king) = ____
```
````

The marking scheme entries:

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
- Follow through from the student's own answer to 2(a) when they use sine or tangent.

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

### (c) Biology: a data table shared by several parts, a label bank and matching

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

![A plant cell with three numbered pointers. Pointer 1 points to the thick outer boundary of the cell. Pointer 2 points to one of several small oval bodies near the edge. Pointer 3 points to the large pale space that fills the middle of the cell.](pictures/plant-cell-3.svg)

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

The table sits between the question heading and 5(a), so it is Question 5's shared material, and the page keeps it available beside 5(a) to 5(e). The marking scheme entries:

```markdown
## Question 5

Topic: enzymes; cell structure
Outcomes: 2, 4

### 5(a)

Answer: 40

- 2 marks for 40 °C; no marks for 30 or 50.

### 5(b)

Answer: 0.25 per minute ± 0.005

Hint: Rate = 1 ÷ time. Use the time for 30 °C from the table.

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

1 mark each. Do not accept "cell membrane" for 1.

### 5(e)

Answer: 1 B, 2 A, 3 C

1 mark each.
```

Note that 5(a)'s "2 marks for 40 °C" has no colon after "marks", so it is guidance, not a tick-box point. The preview says "Marked by: marks out of 2".

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

Option C holds its own code block, so the choice fence uses four backticks. CommonMark closes a fence only with at least as many backticks as opened it. The answer is stored as the letter, so reordering the options before issue is safe, and after issue the lock refuses it. The marking scheme entry:

```markdown
### 6

Answer: B
```

### (e) An essay with a criteria grid

````markdown
# Section D: Essay (40 marks)

## Question 7: Recording lectures (40 marks)

"Every lecture should be recorded." Discuss.

Use the planning box first if it helps. It is handed in with your essay but carries no marks.

```answer 7: plan (not marked)
```

```essay (about 800 words)
```

# Reference

## Rate of reaction

Rate = 1 ÷ time taken. Its unit is "per minute" when time is in minutes.
````

The `# Reference` card serves Question 5, but reference cards come after the last question, so it closes the paper half here. The marking scheme entry:

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

The planning box is ordinary rough work, not a separate `planning_box` key. Changing Clarity to `(8 marks)` gives "The criteria for 7 add up to 38, but it is worth 40" and "The bands for 'Clarity…' should run from 0 to 8".

---

## 7. Conversion

**PDP pages, by script.** The converter reads the `exam-src` block and makes these changes:

- **Settings:** `exam_id` becomes `code`, `duration_minutes: 120` becomes `time allowed: 2 hours`, `module` is split into module and code, the unused `reference_theory` is dropped, switches become `on` and `off`, and a `hand in` line is added.
- **Title:** the `#` line that repeats the title is dropped.
- **Box words:** `(optional)` becomes `(not marked)`, and `fields` becomes `boxes`.
- **Sub-parts:** a bold lead that carries marks, such as `**(i) Longer word (4 marks).**`, becomes a `####` heading.
- **The 2027 paper only:** four lines of HTML maths become `$…$`, and the inline SVG flowchart becomes `pictures/…-figure-1.svg`, with a placeholder description for the teacher to write.
- **Marking scheme:** a skeleton is appended, with one `(draft)` entry per part and `Topic:` and `Outcomes:` lines per question.

Every question, part, label, listing and piece of starter text is kept as written.

| Paper | Source lines | Lines changed | Prototype result |
|---|---|---|---|
| Sample, Practice 1, Practice 2 | 266–270 | 32 each | 60 marks, 17 boxes (1 rough work), 13 draft entries, no problems |
| Exam 2027 | 456 | 36 | 60 marks, 28 boxes (2 rough work), 21 draft entries, no problems |

The parts the prototype finds with shared marks are the ones `pdp-pages.md` §3.5 counted by hand: 1A and 4B(i)/(ii) in the Sample, and 2(d), 3(a), 4(e) and 4(f) in 2027. **Effort:** the converter exists. For each paper, allow 15 minutes to compare the preview with the original and one to two hours to write the scheme. Add 10 minutes for 2027's figure description. The four papers take six to nine hours in all, and nearly all of that is scheme writing, which no format avoids. The assistant can draft those entries as `(draft)` (`assistant.md` §3.5). The importer for old `pdp-exam/1` submissions (`pdp-pages.md` §9.3) becomes small, because a PDP label is now the name: `"label": "1A (i)"` maps to `q1a.i`.

**dewmark's five samples, by script.** They are YAML blocks, so a converter can read them with `build_exam.py`'s own `parse_exam_file` and write paper-first text:

- `question` blocks become headings with marks;
- `prompt` becomes prose;
- each `type` maps to a fence or a pair of fences (§1.3);
- `{word}` gaps become `____`, with each answer moved to `Answers:`;
- `marking` blocks go below the line;
- `choose: 2` becomes "Answer any two" in the section heading;
- `reference` blocks become `# Reference` cards;
- `data_files` become links, and `setup_code` becomes a `python setup` fence.

The converter must place headings by position, because today's parser attaches each heading to the previous question (`code.md` §1). **Effort:** about 250 lines and a day to write, then a day of review, mostly on the maths sample and its 70 boxes. Splitting its final values into `boxes`, so the workbench can suggest marks, is optional teacher work of about half a day. No sample has been sat, so their names can change freely.

---

## 8. Translation by a language model

**Why a model gets this format right.**

- **The output looks like the input.** A Word exam is already numbered headings with "(15 marks)", and a Word scheme already reads "1(a) … 2 marks …". The model mostly copies text and adds a fence where a box goes, instead of re-encoding the paper into a structure. Its one real judgement, what kind of box a part needs, is the judgement a teacher would make.
- **There are few ways to fail.** Markdown is what models write most reliably. Nothing depends on indentation except criteria bands, and there any indent is accepted. There are no quoting rules and no YAML typing, and the vocabulary is eleven box words, three material words and `tests`.
- **The model invents no names.** Names come from the printed numbers by rule.
- **Coverage is checked by plain text matching.** The paper half keeps the teacher's sentences verbatim, so `assistant.md` §3.4's check ("every source paragraph appears once, or is listed as left out") works without unfolding YAML strings. That design's JSON quote objects still work: a serialiser writing this format from them is a few dozen lines. On the paste route, a large hosted model can write the file directly.
- **Repair messages point to a line the teacher recognises**, not to a path in a schema.

**What goes wrong.** Markdown forgives, so a plausible file can mean something else. A model may write `**Question 1** (15 marks)` in bold instead of as a heading, write "(3m)", nest a part at the wrong level, or kindly write the solution into the starter text. The first three are caught by the warning about marks on a line that is not a heading, the warning about numbered headings without marks, and the sums. The last is caught by the check that no scheme text appears above the line.

**Three builder messages, as a teacher reads them:**

> **Line 91 · Question 2 · marks don't add up**
> Question 2's parts add up to 11 marks, but its heading says (10 marks).
> 2(a) is 6 marks and 2(b) is 5 marks.
> Change one part's marks, or change the heading. The paper's total is checked once this is fixed.

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
   hand in: Upload your file to "Biology exam" on Moodle, then raise your hand.
   ---

2  THE FRONT PAGE is anything you write before the first question: the instructions.

3  NUMBERS AND MARKS GO IN HEADINGS. A heading with marks is a question or a part.
   # Section B: Answer any two questions (40 marks)       optional; "any two" is understood
   ## Question 3: Enzymes (20 marks)
   ### 3(a): Reading the graph (5 marks)                   or just ### (a) …
   #### (i) The optimum (2 marks)                          only if a sub-part has its own marks
   Parts must add up to their question, and questions to the total. dewmark checks.

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
   ```on-paper  the student answers on paper; you type the mark in later
   End every box with three backticks on a line of their own.
   Two boxes in one part? Label them:  ```python 4(b): your function   ```python 4(b): your tests
   A box with no marks (rough work, a plan): add (not marked).

5  THINGS STUDENTS READ BUT CANNOT CHANGE
   ```text      code with line numbers      ```pseudo    pseudocode
   ![say what the picture shows](pictures/cell.svg)       $x^2 - 4$ for maths
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
   Hint: ...                         practice papers only
   Anything else is guidance for the marker.
   Put (draft) after a heading you have not checked; an exam cannot be issued until you remove it.

AFTER STUDENTS HAVE SAT A PAPER, DO NOT RENUMBER IT. For next year, change version: 1 to version: 2.
````

---

## 10. Self-critique

**1. Meaning depends on small written conventions.** Each of these is quick to learn:

- "(3 marks)" and not "(3m)";
- "any two" in a heading;
- `2 marks:` with a colon, and not "2 marks for";
- " / " with spaces for alternatives;
- `____` for a gap;
- "(not marked)".

The prototype catches every slip I tried. But all of these errors are the same kind: something written slightly differently that means something else. A single slip also sets off several messages. Deleting one heading's marks produced four, so the builder must list the cause first, and the preview must say what it read, including the outline with marks and "Marked by …" labels. **What breaks first** is real schemes pasted from Word or written by a model. Lines such as "Award 2 marks for …", "(2)" or "2m" will be read as guidance rather than tick-box points. That is safe, because the marker still types a number, but the tick boxes disappear without comment. The builder should warn when a guidance line starts with a number of marks.

**2. Two halves joined by numbers, and names that are numbers.** Four costs follow:

- The scheme sits away from its question, although the studio's split view helps.
- Renumbering before issue means editing two places, although both are cross-checked.
- After a sitting, renumbering is refused outright unless the version changes. That is right for the sitting, but comparing a question across years needs the "was" map, which is not built yet.
- Captions are part of names, so fixing a caption after a sitting depends on the caption-only rule. That rule is one more piece of logic that has to be right.

**3. Light syntax grows into a set of small languages.** Numeric keys already have their own phrasing (±, to, %, d.p., s.f., units). Tests have a second and bands a third. Each new need would add another phrase: stricter significant figures, a separate unit box, per-cell table marks, mechanical error carried forward, randomised versions. The typed-blocks design would add a key for each, which is easier to check and harder to write. Without discipline, by the tenth question type this format would be harder to learn than YAML. The rule must be that each phrase belongs to one registry type, with its own tests and one line on the cheat sheet, and that a need which cannot be said in one short line waits. The format also parts company with dewlab's `question` fence, which writes `{word}` gaps with the answer inline: right for a tutorial, wrong for an exam. Moving a tutorial self-check into a paper therefore takes a mechanical rewrite.

---

## What ships first, and what waits

**First,** alongside the move and the data-loss fixes. The format freezes before the first sitting (`ROADMAP.md`), so this step includes:

- the whole grammar, written down, including kinds whose renderers come later (an unknown kind is refused, so adding a renderer never changes the format);
- the reader, with settings, headings, sums, names and the lock;
- the kinds the PDP papers and the samples use: `answer`, `python`, `boxes`, `essay`, `choice`, `blanks`, `table`, `text`, `pseudo` and `python setup`, with `maths` shown as `answer` until its preview exists;
- the marker's half: `Answer:`, `Model answer:`, points, criteria, guidance and `(draft)`;
- the PDP converter.

**Second:**

- `match`, `order`, `on-paper` and `Choose from:` banks;
- the maths preview and palette;
- numeric suggestions and `tests` in the workbench;
- `Hint:` and `show answers` in practice papers;
- the samples converter.

**Later:**

- the companion scheme file;
- the "was" map across versions;
- rubric tables pasted from Word;
- checks on the form of an expression;
- paper variants.

## Decisions for Josh

1. **Where the scheme lives:** at the end of the same file, under `# Marking scheme` (recommended), in a companion file, or inline after each box.
2. **Names are the printed numbers** (recommended). This means a paper that has been sat cannot be renumbered without a new version.
3. **Gaps are written `____`, with the answers in the scheme** (recommended). This departs from dewlab's `{word}`.
4. **`fields` becomes `boxes`** (recommended), and PDP's `text` keeps its meaning of a numbered code listing.
5. **Set-up code is shown to students, collapsed, by default** (recommended). The hvit paper's instructions already describe it to students.
