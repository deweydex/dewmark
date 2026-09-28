# The exam file as one fence family with dewlab

*Design round 2, 2026-09-27. One of three rival proposals for the one file a teacher writes (the others are `format-paper-first.md` and `format-typed-blocks.md`). It follows Josh's twenty decisions in `planning/DECISIONS_2026-09-27.md`; where this document and a decision differ, the decision wins. The angle: dewlab already has a small grammar for an answer space, the `question` fence (`/home/user/dewlab/DECISIONS_LOG.md` entry 7.179; `parse_question()` at `/home/user/dewlab/build.py:1515`, dispatched from `extract_blocks()` at `build.py:1755`). This proposal makes that grammar the exam grammar, so that a tutorial's self-check and a practice paper's question are the same text. Every example below passes a prototype checker, and section 7's figures come from running two prototype converters on the nine real papers. The prototype is scratch work in `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/design-round/one-fence-family/` (`dewfence.py`, 580 lines; `pdp2fence.py`, 166; `dm2fence.py`, 194; converted papers in `out/`), not part of either repository.*

## The case in brief

1. **One shape for every answer space.** A fence (a block that opens with three backticks and a word and closes with three backticks), then a few `key: value` lines, then ordinary Markdown. This is dewlab's `question` fence and dewlab's `python exec` cell exactly as they stand. A tutorial self-check copied into a practice paper passes the checker with no edit at all (tested: `moved.exam.md` holds two fences copied verbatim from `/home/user/dewlab/tutorials/how-far-apart/how-far-apart.md:56-85`).
2. **Structure is headings; data is fences.** A `##` heading opens a question, as a `##` heading opens a part of a tutorial. Sections, which carry rules ("answer any 2"), are a small `section` fence.
3. **Marks and the marking scheme live in a `mark` fence under the answer it marks**, the way dewlab's `solution` and `hint` fences attach to the cell above them. One mark fence can mark several spaces (`for: a, b`), which is exactly what the PDP papers need for "your function" and "your tests".
4. **The permanent name is the `id:` line**, the rule dewlab already enforces for cells (`CLAUDE.md`, "Cell ids are a contract"). Headings and numbers may change freely; ids may not, once a paper has been sat.
5. **The student page is built from the shape of each fence, never from its key**, and the checker proves it: it changes every answer in the file and confirms the student half comes out identical.
6. **All nine papers convert and pass**: the four PDP papers by script, and dewmark's five samples by script. 190 answer spaces in all.

The strongest reason for this angle is not tidiness. It is that Josh maintains one set of habits, one set of documentation, one assistant package and one parser for both projects, and that practice material can flow from the tutorials, where it is written and tested with students every week, into practice papers, without being retyped.

---

## 1. The grammar

### 1.1 The carrier

An exam file is `<code>.exam.md`: a dewlab-style Markdown page with `pictures/` and `data/` folders beside it. It has four layers, the same four a dewlab tutorial has.

```
---                          settings, one per line (§5), between two --- lines
title: …
---
front page prose             everything before the first section or question
```section …```              a section and its rule (optional)
## Question 1: …             a question; everything under it belongs to it
### 1(a): …                  a part: display only
```question …```             an answer space
```mark …```                 its marks and scheme (never on the exam page)
```

Before reading anything the builder tidies Windows line endings, tabs and non-breaking spaces (a PDP file with Windows line endings loses all its settings today, `pdp-pages.md` §3.1). `$…$` is maths, typeset at build time, as in dewlab since 7.182. A fence may use four backticks to hold a three-backtick block, as CommonMark allows.

### 1.2 The one rule for every fence

Every fence reads the same way, and it is dewlab's rule:

- **The first line** names the fence: `question`, `python exec`, `mark`, and so on.
- **The header** is `key: value` lines at the top. Each value is the rest of the line, read as text. There is no indentation, no quoting and no lists-in-brackets: a list is written with commas (`bank: nucleus, vacuole`). This removes the YAML problems the current grammar has, where `options: [Yes, No]` reaches students as "True"/"False" and `12:30` becomes 750 (`code.md` §1, table row "YAML 1.1 coercion").
- **The body** is everything after the header. For prose fences the header ends at the first blank line. For code fences (`python exec`, `solution`, `checks`) it ends at the first line that is not a known key, which is how dewlab's cells work today (`how-far-apart-practice.md:158-164`: `id:` on one line, code on the next).
- **Every key belongs to a closed list.** An unknown key stops the build with a suggestion ("Did you mean `marks`?"). In a code fence, a first line that looks like a misspelt key (`mraks: 3`) is refused rather than read as code.

### 1.3 Every construct

| Fence | What it is | Required keys | Optional keys | Student sees it? |
|---|---|---|---|---|
| `question` | an answer space that is not code | `id`, `type` | `answer`, `bank`, `see`, `input`, `size`, `words`, `planning`, `working`, `marked` | the prompt and the empty spaces |
| `python exec` | a code answer; body is starter code | `id` | `tests`, `see`, `run_limit`, `marked` | yes |
| `python setup` | code run silently before the paper starts | none | none | no (runs) |
| ```` ```python ````, ```` ```text ````, ```` ```pseudocode ```` | a read-only listing; `numbered` or `numbered-from-4` after the language | none | none | yes |
| `stimulus` | material several parts refer to (a table, a passage, a figure) | `id` | `title` | yes, pinned beside its parts |
| `section` | a group of questions with a rule | `id` | `title`, `answer`, `marks` | its title and rule |
| `reference` | a card for the side panel (a formula sheet, a Python reference) | `title` | none | yes, in the panel |
| `mark` | marks and marking scheme for one or more answer spaces | `marks` | `for`, `method`, `accept`, `draft` | only the number of marks |
| `solution` | the model answer (dewlab's own fence, with `---` before the explanation) | none | `for`, `title` | practice: after finishing; exam: never |
| `checks` | hidden tests for code | none | `for` | practice: results after running; exam: never |
| `hint` | dewlab's staged hint | none | `for`, `after`, `title` | practice only; dropped from exam builds |

`for:` is optional wherever it appears: a `mark`, `solution`, `checks` or `hint` fence with no `for:` attaches to the answer space above it, which is how dewlab attaches `hint`, `solution`, `inputs` and `predict` fences to "the exec cell above" (`build.py:1790-1812`).

### 1.4 Question types

| `type:` | Body | Key lives in | Tutorial today? |
|---|---|---|---|
| `multiple-choice` | prompt, then options as `- ` lines; an indented `  - ` under an option is its note | `answer: B` (or `2`, dewlab's form); several: `answer: A, C` | yes |
| `fill-in-the-blank` | any Markdown (sentences, lists, tables, a figure) with `{…}` gaps | the gaps themselves | yes |
| `written` | prompt; optional `---` line, then text already in the box | `solution` fence | no |
| `essay` | prompt | `solution` fence, grid in `mark` | no |
| `maths` | prompt; typed maths answer (plain text, MathLive or photograph, decision 15) | optional `answer:`; `accept:` in `mark` | no |
| `ordering` | the items as `- ` lines in the correct order | the order written | no |
| `on-paper` | prompt; the student ticks "I answered this on paper" and gives the sheet count | `solution` | no |

`fill-in-the-blank` carries most of the catalogue, and this is the grammar's main economy. dewlab's two gap forms stay; two are added:

| Gap | Student gets | Key |
|---|---|---|
| `{nucleus}` | a typing box | `nucleus` |
| `{same amount\|different amounts}` | a drop-down (dewlab's form, first item the key); listed alphabetically on a paper, so position gives nothing away and every student sees the same layout | first item |
| `{}` | a typing box with no key (a free answer, like PDP's `fields`) | none; see `solution` |
| `{= 3.63 ± 0.01 m}` | a number box, and a unit box when a unit is written | 3.63, within 0.01; unit `m` |

With a `bank:` line, every `{word}` gap becomes a drop-down of the bank, and the builder refuses a gap whose word is not in the bank. So a matching question, a label-the-diagram question with a label bank, a complete-the-table question and a describe-a-sketch question are all `fill-in-the-blank` written in different Markdown: a list, a numbered list under a picture, a table with gaps in its cells, sentences with number gaps. The research proposed six new types and kept eleven old ones (`question-types.md` §3); this grammar needs seven types for the same ground. The workbench still shows each one sensibly, because it reads the shape (a table, a bank) rather than a type name.

Gaps are found by dewlab's `find_gaps()` (`build.py:1471`), which already skips braces inside `$…$`, so `$10^{-12}$` stays a power.

---

## 2. Structure and marks

**Questions.** A `##` heading opens a question, and everything under it until the next `##` or section belongs to it. This is the fix for today's worst structural bug, where every heading lands in the *previous* question because the heading comes before the `question` block that opens it (`code.md` headline finding 6 and §1 table): here the heading *is* the opener. A `##` heading with no answer space under it ("Instructions to candidates") is prose, not a question, without any marker.

**Parts.** `###` headings and bold labels like `**(ii)**` are display only. The builder does not need to know about parts, because marks attach to answer spaces, not to headings.

**Sections.** A `section` fence starts a section and holds its rule:

```section
id: maths
title: Section B: Measurement and algebra
answer: any 2
marks: 20
```

The builder draws the heading from `title:` and writes the instruction line from `answer:` ("Answer any two of these three questions"), so the words cannot drift from the rule. `answer:` is `all` (the default) or `any N`. For `any N`, every question in the section must carry the same marks; the builder refuses otherwise, because "the best 2 of 20, 15 and 4" has no single total. The workbench keeps today's behaviour for choice sections: it marks everything, counts the best N and shows which counted (`design-docs.md` §"Any N").

**Where totals come from.** Marks are written in one place only: the `marks:` line of each `mark` fence. Everything above is added up:

- a question's total is the sum of its mark fences;
- a section's total is that sum, or N × the question total for `any N`;
- the paper's total is the sum of its sections.

**How they are checked.** Three optional checksums, all compared with the sums: `(15 marks)` at the end of a `##` heading, `marks:` on a section fence, and the required `total:` in the settings. A heading without "(N marks)" gets it added by the builder, so a teacher may write it or not. Every answer space must have exactly one mark fence covering it, or say `marked: no` (rough work). A forgotten mark fence is therefore an error, not silent rough work. All of this runs in the prototype (`dewfence.py`, `check()`).

---

## 3. Answer spaces and their names

**Declaring one.** Any `question` or `python exec` fence is an answer space. There is no other way to make one.

**Its permanent name** is the `id:` line: small letters, digits and hyphens (`parts-of-count-capitals`, `q4b-i-tests`), unique across the paper. Sub-answers inside a fence are stored by position: the third gap of `ramp-length` is `ramp-length.3`, a working box is `ramp-length.working`, a planning box is `essay-remote-learning.planning`. This is dewlab's saved-work model without change (7.179: "one string per gap").

**Why renumbering is safe.** Nothing a student's work is stored under comes from a number. Moving Question 3 before Question 2, renaming "1(b)" to "2(a)", or moving a section changes headings only. The student sees new numbers; the workbench and the marks spreadsheet key on ids and show the current numbers beside them.

**Recommended ids.** The prototype converters make ids from part labels (`q4b-i-function`) because a script cannot know what a question is about. For new papers the cheat sheet asks for a few words that describe the question (`same-first-and-last`), because such an id still reads correctly after the question moves. Either works; once sat, neither may change.

**The lock.** The first time a paper is built with `kind: exam`, the builder writes `<code>.names.txt` beside it: each id, its type and its gap count. After that, a build that removes an id, changes its type or changes its gap count stops, naming the id. Adding answer spaces is always allowed. A teacher who must break the rule deletes the lock file on purpose, and the workbench then shows old answers that match nothing under "answers with no question" rather than losing them. dewlab learnt the same lesson about cells; dewlab's world suffix (`your-turn-1--planets`) is also accepted in an id, which leaves room for version A and version B of a paper later without a new rule.

---

## 4. Marking and model answers

### 4.1 Where they live

Three fences hold everything a student must not see in an exam: `mark` (marks, method, accepted alternatives), `solution` (the model answer, exactly dewlab's fence: code or prose, then `---`, then the explanation) and `checks` (hidden tests). They normally sit directly under the answer space. Because each can say `for:`, a teacher who prefers the scheme at the back of the file may gather them under a closing `# Marking scheme` heading, or in a second file `<code>.scheme.md` that the builder reads alongside. The paper-first layout is therefore available as an option inside this grammar.

### 4.2 The three methods

`method:` on a mark fence says which, with `total` the default.

| Method | Written as | Checked |
|---|---|---|
| `total` (marks out of a total) | `marks: 6`, then guidance as ordinary Markdown | marks is a whole number |
| `points` (a points list with a limit) | `marks: 6` is the limit; each point `- 2 marks: the method is shown` | points add up to at least the limit |
| `grid` (criteria grid) | each criterion `- Argument, 8 marks`, its bands indented `  - 7 to 8: one position, sustained` | criteria add up to `marks`; each criterion's bands cover 0 to its top exactly once |

The method is written, not guessed; today it is inferred from which keys are present (`design-docs.md` §"Marking blocks").

### 4.3 Accepted alternatives, tolerance and units

- **Choice keys** are the `answer:` line or the first item of a drop-down gap.
- **Typed gaps**: the word in the gap, plus `accept:` lines in the mark fence, which may repeat: `accept: 1 = premisses, premiss` (gap 1). With no gap number, `accept:` applies to a single-gap or `maths` answer: `accept: (x + 2)(x - 4)`.
- **Numbers**: `{= 7.1 ± 0.1}` (a percentage works: `± 2%`; `+-` is accepted for teachers who cannot type ±).
- **Units**: a unit written in the gap (`{= 3.63 ± 0.01 m}`) gives the student a unit box. The unit is part of the key and is never shown. Other spellings go in `accept:` (`accept: 1 = metres, metre`). Units are matched, not converted: "363 cm" is shown to the marker as "unit not accepted", and the marker decides (decision 13).

Rules like these propose a mark on closed answers and give evidence on the rest; the marker confirms every mark (decision 13).

### 4.4 Hidden tests for code

A `checks` fence holds one test per line, in the three shapes the PDP papers need (`question-types.md` §0 point 4):

```checks
same_first_and_last("Anna") is True
same_first_and_last("Dublin") is False
run with input: 50 | prints: divisible by both 2 and 5
after run: len(odd_numbers) == 10
```

A plain line is a Python expression that should be true after the student's cell has run. Checks run in the workbench as evidence, and in practice pages so students see which pass (decision 16). They never go into an exam page.

### 4.5 Keeping it out of the student page

This is the angle's hardest question, because dewlab's fence keeps its key next to the prompt: `answer: 1`, and `{word}` in the gap. In a tutorial that is right: dewlab writes the key into the page on purpose (`data-answer`, `render_question()` at `build.py:1569`), as "the right trade for a question to think with and the wrong one for an exam". So the exam build must never do what the tutorial build does, and that must be guaranteed by construction, not by a list of things to strip.

The guarantee has three parts.

1. **Split at reading time.** The reader turns each answer fence into two records: what it looks like (type, prompt, number and kind of gaps, the bank in alphabetical order, whether a unit box exists) and what it expects (keys, notes under options, accepted spellings). `mark`, `solution` and `checks` fences go only into the second. The student-page renderer is given the first record and nothing else; it has no way to reach a key.
2. **The build by kind.** Exam builds carry the first record only. Practice builds also carry the second, revealed only when the whole paper is finished (decision 14), and the checks. dewlab's option shuffling is off in both, so "option C" means the same thing to every student and marker.
3. **The mutation test.** The checker rewrites every key in the file (every gap word, every `answer:`, every accepted spelling, every scheme, solution and test) and builds the student half again. If anything differs, the build stops: "Leak: the student page changes when the answers change." This is stronger than today's leak check, which searches the page after stripping all `<script>` content, so the page's own JSON is never searched (`code.md` §1, L1228). In the prototype the test passes on all ten files, and fails at once when I deliberately let `answer:` through to the student record (a copy called `leaky.py`, since removed).

A naive "is the key's text on the page" test does not work, and the prototype showed why: in the PDP-style example the answer `count_capitals` is on the page legitimately, in the listing the student reads. The mutation test asks the right question: does the page *depend on* the key?

One leak the split must close on purpose is the width of a typing box (the mutation test would catch it, since changing a key changes the width). dewlab sizes a gap from its answer (`size="{max(len(expected), 3)}"`, `build.py:1631`). Exam and practice builds give every typed gap the same width unless the teacher writes `size:`.

---

## 5. Exam settings and presentation

Settings sit between two `---` lines at the top, as in every dewlab tutorial (`how-far-apart-practice.md:1-6`), and share dewlab's `title:` and `version:`. Each line is `key: value`, read as text, from a closed list.

| Key | Values | Default | Notes |
|---|---|---|---|
| `title` | text | required | the paper title ("Practice Examination 1") |
| `code` | letters, digits, hyphens | required | storage key and file names; permanent |
| `version` | text | required | shown in the footer and every submission |
| `kind` | `exam`, `practice`, `sample` | required | sets the fixed EXAMINATION/PRACTICE band (decision 12); `--as practice` builds the same file as practice |
| `institution`, `college` | text | none | "Dublin and Dún Laoghaire ETB", "Dublin College Dundrum" |
| `module`, `module_code` | text | none | "Programming and Design Principles", "5N2927" |
| `session` | text | none | "2026–2027" |
| `logo` | a file in `pictures/` | none | embedded in the page |
| `total` | number | required | checksum (§2) |
| `time` | minutes | none | |
| `timer` | `none`, `shown`, `enforced` | `shown` with `time`, else `none` | the student can always hide it (decision 11) |
| `breaks` | `on`, `off` | `off` | decision 11 |
| `calculator` | `none`, `basic`, `scientific` | `none` | |
| `maths_input` | any of `text, mathlive, photo` | `text` | per question: `input:` (decision 15) |
| `hand_in` | `pdf+html`, `pdf+json`, `pdf+html+json` | `pdf+html` | a PDF is always included (decision 10) |
| `answers_after` | `finish`, `never` | `finish` for practice | never used in exam builds |
| `reference` | a Markdown file, or `reference` fences in the paper | none | the side panel |
| `python` | `none`, `inside`, `online` | `none` | decision 7 |
| `packages` | comma list | none | "numpy, matplotlib" |
| `files` | comma list of files in `data/` | none | copied beside the page |
| `run_limit` | seconds | 10 | per run; `run_limit:` on a cell overrides |
| `completion` | `on`, `off` | `off` for exam | code completion |
| `error_hints` | `on`, `off` | `on` for practice | friendly line under a traceback |

Student name and number are always asked, on the one combined start screen (decision 9), so there is no setting for them. The front-page prose (everything before the first section or question) is the instructions page.

---

## 6. Worked examples

All five come from `examples.exam.md` in the scratch folder, which passes the checker as one paper: 7 questions, 13 answer spaces, 64 marks. Its settings are the ones in §5 with `kind: practice`.

### (a) A PDP-style question: listing, code cell, labelled boxes

````markdown
## Question 1: Reading and writing functions (10 marks)

### 1(a): Parts of a function

Study this function.

```python numbered
def count_capitals(text: str) -> int:
    total = 0
    for char in text:
        if char.isupper():
            total += 1
    return total

print(count_capitals("Dublin College Dundrum"))
```

For each term, give its name or value in this function.

```question
id: parts-of-count-capitals
type: fill-in-the-blank

- Function name: {count_capitals}
- Parameter: {text}
- Line of the conditional statement: {= 4}
- What the last line prints: {= 3}
```

```mark
marks: 4
method: points

- 1 mark: count_capitals
- 1 mark: text (accept "text: str")
- 1 mark: line 4
- 1 mark: 3
```

### 1(b): Same first and last

Write a function `same_first_and_last(word)` that returns `True` when
the first and last letters are the same, ignoring capitals. Then write
tests for it in the second cell.

```python exec
id: same-first-and-last
def same_first_and_last(word):
    # Write your function here
    pass
```

```python exec
id: same-first-and-last-tests
tests: same-first-and-last
# Call your function here to show that it works
```

```mark
for: same-first-and-last, same-first-and-last-tests
marks: 6
method: points

- 2 marks: compares the first and last characters
- 2 marks: ignores capitals, for example with .lower()
- 1 mark: returns True or False rather than printing
- 1 mark: at least two tests, one True and one False
```

```solution
def same_first_and_last(word):
    """True when word starts and ends with the same letter, any case."""
    return word[0].lower() == word[-1].lower()
---
Any version that lowers both letters before comparing earns the marks.
```

```checks
same_first_and_last("Anna") is True
same_first_and_last("Level") is True
same_first_and_last("Dublin") is False
```
````

`tests:` is dewlab's own cell key for "this cell holds the reader's tests of that cell" (`build.py:157`, `HEADER_RE`), reused with the same meaning. One mark fence covers both cells, which closes the PDP conversion gap where "several spaces share one part's marks" (`pdp-pages.md` §9.3, gap 3). For PDP's free `fields` boxes, write `{}` instead of a key and put the model answers in a `solution`.

### (b) A maths section: any 2 of 3, a number with tolerance and units, typed maths

````markdown
```section
id: maths
title: Section B: Measurement and algebra
answer: any 2
marks: 20
```

## Question 2: A ramp

A ramp rises 0.45 m over a horizontal distance of 3.6 m.

```question
id: ramp-length
type: fill-in-the-blank
working: yes

The length of the sloping surface is {= 3.63 ± 0.01 m}.

The angle of the ramp to the ground is {= 7.1 ± 0.1}°.
```

```mark
marks: 10
method: points
accept: 1 = metres, metre

- 3 marks: Pythagoras set up, $\sqrt{3.6^2 + 0.45^2}$
- 2 marks: 3.63 m (unit required)
- 3 marks: $\tan^{-1}(0.45 / 3.6)$ or equivalent
- 2 marks: 7.1°
```

## Question 3: Factorising

```question
id: factorise-quadratic
type: maths
answer: (x - 4)(x + 2)

Factorise $x^2 - 2x - 8$ fully.
```

```mark
marks: 4
accept: (x + 2)(x - 4)

Full marks for either order of the brackets. 2 marks for a correct
pair of numbers (-4 and 2) without brackets.
```

```question
id: solve-quadratic
type: maths
input: text, photo

Hence solve $x^2 - 2x - 8 = 0$. Show your working.
```

```mark
marks: 6
method: points

- 2 marks: sets each bracket equal to zero
- 2 marks: x = 4
- 2 marks: x = -2
```

## Question 4: Simultaneous equations

```question
id: simultaneous-pair
type: fill-in-the-blank
working: yes

Solve $2x + y = 7$ and $x - y = 2$.

$x$ = {= 3}, $y$ = {= 1}
```

```mark
marks: 10
method: points

- 4 marks: eliminates one unknown correctly
- 3 marks: x = 3
- 3 marks: y = 1
```
````

The first gap in Question 2 gives a number box and a unit box; the second writes the degree sign as fixed text after the box, so no unit box appears. The checker confirms each question carries 10 marks and the section 20.

### (c) Biology: a shared data table, a label bank, a matching part

````markdown
## Question 5: Osmosis in potato cylinders

```stimulus
id: table-1
title: Table 1

Five potato cylinders were weighed, left in sugar solutions for one
hour, and weighed again.

| Sugar solution (M) | 0.0 | 0.2 | 0.4 | 0.6 | 0.8 |
| --- | --- | --- | --- | --- | --- |
| Change in mass (%) | +12 | +5 | -1 | -7 | -12 |
```

```question
id: osmosis-no-change
type: fill-in-the-blank
see: table-1

From Table 1, the concentration at which the mass would not change is
about {= 0.37 ± 0.03} M.
```

```mark
marks: 2
```

```question
id: osmosis-explain
type: written
size: short
see: table-1

Explain why the cylinder in 0.8 M solution lost mass.
```

```mark
marks: 3
method: points

- 1 mark: water moves out of the potato cells
- 1 mark: by osmosis
- 1 mark: from a higher to a lower water concentration
```

```question
id: plant-cell-labels
type: fill-in-the-blank
bank: cell wall, cell membrane, nucleus, chloroplast, vacuole, mitochondrion

![A plant cell with four numbered pointers: 1 the thick outer
boundary, 2 a round body near the edge, 3 a small green oval, 4 the
large pale space in the middle.](pictures/plant-cell.svg)

1. {cell wall}
2. {nucleus}
3. {chloroplast}
4. {vacuole}
```

```mark
marks: 4
```

```question
id: organelle-jobs
type: fill-in-the-blank
bank: makes food by photosynthesis, releases energy in respiration, controls the cell's activities, stores cell sap

Match each part of the cell to its job.

- Nucleus: {controls the cell's activities}
- Mitochondrion: {releases energy in respiration}
- Chloroplast: {makes food by photosynthesis}
```

```mark
marks: 3
```
````

`see: table-1` gives each part a "Show Table 1" button at large text sizes and keeps the table pinned beside its parts on a wide screen (`question-types.md` §6.1). The bank holds more choices than gaps, so the last answer cannot be found by elimination. A mark fence with no method and no body is enough for a closed question: the key proposes a mark per gap, and the marker confirms.

### (d) Multiple choice

````markdown
## Question 6: Recognising a variable

```question
id: valid-variable-name
type: multiple-choice
answer: C

Which of these is a valid variable name in Python?

- `first-name`
  - A hyphen is read as a minus sign.
- `9lives`
  - A name cannot start with a digit.
- `_total`
  - An underscore may start a name.
- `for`
  - `for` is a keyword.
```

```mark
marks: 2
```
````

This is dewlab's fence, notes and all (the indented notes are dewlab #314). In a tutorial it shuffles and shows a note beside the reader's choice. In a practice paper the notes appear after the paper is finished. In an exam they are never sent.

### (e) An essay with a criteria grid

````markdown
## Question 7: Essay

```question
id: essay-remote-learning
type: essay
words: 400 to 600
planning: yes

"A recording of a class is as good as being there." Discuss.
```

```mark
marks: 20
method: grid

- Argument and structure, 8 marks
  - 7 to 8: one position, sustained; each paragraph moves it forward
  - 4 to 6: a clear position, developed unevenly
  - 0 to 3: drifts, or retells the title
- Evidence and examples, 8 marks
  - 7 to 8: specific cases, examined rather than listed
  - 4 to 6: real examples, summarised
  - 0 to 3: little or no evidence
- Clarity of language, 4 marks
  - 4 to 4: precise throughout
  - 2 to 3: clear, with lapses
  - 0 to 1: meaning often unclear
```
````

The checker confirms that the criteria add up to 20 and that each criterion's bands cover every mark from 0 to its top exactly once.

---

## 7. Conversion

### 7.1 The PDP papers: by script

`pdp2fence.py` reads the `exam-src` block and maps it line for line (`pdp-pages.md` §3):

| PDP | Becomes |
|---|---|
| front matter | settings; `exam_id` → `code`, `duration_minutes` → `time`, `allow_completion` → `completion`, `time_limit_seconds` → `run_limit`, `error_hints` → `error_hints`, module split into `module` and `module_code` |
| ` ```answer 1A (i) ` | `question`, `type: written`, `id: q1a-i`; pre-filled text goes after a `---` line |
| ` ```python 2A ` | `python exec`, `id: q2a`, starter code unchanged |
| ` ```python 4B (i): your tests ` | `python exec` with `tests: q4b-i-function` |
| ` ```python … (optional) ` | `marked: no` |
| ` ```fields 4A ` | `fill-in-the-blank`, one `- Label: {}` line per field |
| ` ```text `, ` ```pseudo ` | listings, `numbered` |
| `### 1A: … (3 marks)` or `**(i) … (4 marks).**` | unchanged; the script writes one `mark` fence covering every space under that marker, with `draft: yes` |

Results, run on all four papers:

| Paper | Source lines | Lines kept unchanged | Lines changed or removed | Answer spaces | Mark fences written | Checker |
|---|---|---|---|---|---|---|
| Sample | 271 | 236 | 35 | 17 | 12 | passes, 60 marks |
| Practice 1 | 269 | 234 | 35 | 17 | 12 | passes, 60 marks |
| Practice 2 | 267 | 232 | 35 | 17 | 12 | passes, 60 marks |
| Exam 2027 | 457 | 403 | 54 | 28 | 21 | passes, 60 marks |

About 87% of each paper survives untouched. The additions are larger than the changes: each mark fence is seven lines, so a practice paper grows by about 130 lines, mostly `draft` scheme skeletons. That is the right place for the work to show up, because none of the four papers has a marking scheme; writing one is the real authoring cost (about one to two hours a paper for Josh) and no format removes it. The 2027 paper also has three inline-HTML maths spans and one inline SVG figure, which are converted by hand to `$…$` and a `pictures/` file (fifteen minutes). The script also writes a table from PDP's positional names (`b1`, `b2`, …) to the new ids, so that any PDP-era JSON a student already handed in can still be opened in the workbench.

### 7.2 dewmark's five samples: by script

`dm2fence.py` reads the typed YAML blocks and writes fences: `answer` → `question` or `python exec`; `marking` → `mark` (points and criteria become `points` and `grid`); `model_answer` → `solution`; `section` with `choose` → `section` with `answer: any N`; the `question` grouping block disappears, because its heading now does that job; `### Question` headings move up to `##`. Complete-the-table becomes a Markdown table with gaps; label-the-diagram a picture and a numbered list; numeric-answer and describe-a-sketch become sentences with number and drop-down gaps.

| Sample | Answer spaces | Marks | Checker |
|---|---|---|---|
| HVIT database practical | 14 | 60 | passes |
| Maths for IT 5N18396 | 70 | 120 | passes |
| Biology | 10 | 60 | passes |
| Essay | 7 | 100 | passes |
| Mixed | 10 | 50 | passes |

With the PDP papers: nine papers, 190 answer spaces, all passing. The checker found two real problems on the way, which is the argument for a strict checker. The first run of the samples converter left out mark fences for answers whose marks had no separate `marking` block (a multiple-choice question in the biology and mixed samples, and 53 answers in the maths paper). The checker reported every one, and the paper totals came out 58 of 60 and 45 of 50. The second problem was one converter judgement the checker refused: the maths sample's expected value "about -3.46" is not a number; the converter now writes `{= -3.46 ± 0.05}`, and a teacher should confirm that tolerance. Two more judgements are left to the teacher: maths short answers convert to `type: written` and would be better as `type: maths` (a one-word change), and the 56 placeholder mark fences say "no marking guidance was written" because none was.

**Effort.** The two converters took one afternoon between them. A production version of each is about 250 lines with tests. Converting a new Word paper by hand into this grammar takes a teacher about as long as retyping the paper's structure: the prose is pasted as it is, and each answer space adds four to eight lines.

---

## 8. Translation by a language model

**Why a model gets this grammar right.**

- **It is the most common shape in its training material.** Markdown with `key: value` front matter is how most static sites, notes apps and README files are written. Nothing here is invented notation except the gap forms, and those are one rule with four cases.
- **There is no indentation to get wrong and no quoting.** Most model errors in YAML are indentation, a colon inside a value, or a bare `No`. Here a value is the rest of the line, so `prompt: Why: explain` cannot break anything.
- **The prose stays prose.** The prompt and options are Markdown, not a YAML string. That was dewlab's own reason for the design (7.179: "student-facing prose the plain-language pass … has to be able to read as prose"), and it matters more here: decision 19's modes (tidy the wording, check that the language is accessible, make it more UDL-friendly, rephrase commands as invitations) all rewrite prose, and a model rewriting prose inside YAML breaks the YAML.
- **One vocabulary, one package.** The paste package (decision 20) holds one idealised file for the subject, this grammar's one-page guide and the teacher's exam. The same guide already describes the `question` fence dewlab authors use, so the package and its examples are tested every week by tutorial writing.
- **The checker closes the loop.** Every message names a line, says what is wrong in the teacher's words, and suggests the fix, so the studio can hand the messages straight back to the model, or the teacher can fix them by hand.

I have not tested a model converting a real Word paper into this grammar; the claim rests on the shape of the grammar and on the converters above, and a trial on two real papers should come before the studio ships.

**Three builder messages, as a teacher reads them.** These are the prototype's messages, tidied so that one mistake gives one message (the prototype prints knock-on messages too, which a real builder must suppress; see §10).

```
Line 60: a mark block has no setting called "mraks". Did you mean "marks"?
```

```
Line 251: in "plant-cell-labels", the answer "vacuole" is not in the bank
(cell wall, cell membrane, nucleus, chloroplast, mitochondrion).
Add it to the bank, or change the answer.
```

```
Line 293: the answer space "valid-variable-name" has no mark block.
Add one under it, or write "marked: no" if it is rough work.
```

---

## 9. What a non-programmer teacher has to learn

The cheat sheet, as it would be printed.

> **Writing a dewmark paper: one page**
>
> **1. The top of the file** is your paper's details, one per line, between two lines of three dashes:
>
>     ---
>     title: Practice Examination 1
>     code: pdp-5n2927-practice-1
>     version: 1
>     kind: practice              (or exam)
>     module: Programming and Design Principles
>     module_code: 5N2927
>     college: Dublin College Dundrum
>     total: 60
>     time: 120
>     ---
>
> **2. Write the paper as you would type it.** `## Question 1: Title` starts a question. `###` headings, bold and lists are for your students to read. Put maths between dollar signs: `$x^2 - 4$`.
>
> **3. Every place a student answers is a box** that starts with three backticks and a word, and ends with three backticks. Its first lines are settings; then a blank line; then what the student reads.
>
>     ```question
>     id: plant-cell-labels
>     type: fill-in-the-blank
>
>     The control centre of the cell is the {nucleus}.
>     ```
>
> - `id:` is the answer's name, a few words joined by hyphens. **Never change it after students have sat the paper.**
> - `type:` is one of: multiple-choice, fill-in-the-blank, written, essay, maths, ordering, on-paper.
> - For code, start the box with ```` ```python exec ```` and put the starting code after the `id:` line.
>
> **4. Gaps** in fill-in-the-blank: `{word}` a typing box; `{right|wrong|wrong}` a drop-down, right answer first; `{}` a free box; `{= 3.6 ± 0.1 m}` a number, with the unit if the student must give one. Add `bank: a, b, c` to turn every gap into a drop-down from that list.
>
> **5. Multiple choice:** the options are lines starting `- `, and `answer: B` says which is right.
>
> **6. Under every answer box, a mark box:**
>
>     ```mark
>     marks: 3
>     method: points
>
>     - 1 mark: names the nucleus
>     - 2 marks: explains what it controls
>     ```
>
> `method:` is `total` (just a number and your notes), `points` (as above), or `grid` (criteria, each with bands). One mark box can cover two answer boxes: `for: my-function, my-tests`. Rough work: write `marked: no` in the answer box instead.
>
> **7. Model answers** go in a `solution` box; hidden code tests go in a `checks` box. Students never see either in an exam.
>
> **8. Sections with a choice:**
>
>     ```section
>     id: b
>     title: Section B
>     answer: any 2
>     ```
>
> **9. Press Check.** Every problem is listed with its line number and what to do. The marks are added up for you.

---

## 10. Self-critique

**1. The key sits beside the prompt, so exam safety rests on the builder, not on the file.** In the typed-blocks proposal a key can only be in a marking block; here `answer: C` and `{nucleus}` are in the answer fence itself, because that is how dewlab writes them and what lets a question move unchanged. The split at reading time and the mutation test make a leak unlikely, but the guarantee is now a property of code, and code changes. **What breaks first:** a new question type added next year whose shape record includes a field it should not (a hint text, a default value, a box width). The defence is a rule in `CONTRIBUTING.md` that every type ships with a fixture the mutation test runs, enforced by a test that fails when a type has none. A teacher who opens the source file in class, projected, also shows the answers; that is equally true of every rival.

**2. The gap language carries a lot, and braces are common in maths.** `{word}`, `{a|b}`, `{}`, `{= n ± t unit}`, and a `bank:` that changes what `{word}` means: five meanings for one pair of braces. Braces in maths are protected only inside dollar signs. A maths teacher who writes the set `A = {1, 2, 3}` in a fill-in-the-blank question without dollar signs gets a typing box with the key "1, 2, 3". Gaps are only read inside fill-in-the-blank bodies, and `\{` escapes a brace, but a teacher will not know that. The checker should warn when a gap holds a comma and there is no bank ("Is `{1, 2, 3}` a set? Put maths between dollar signs"), and the typeset preview in the studio will show the box where the teacher expected a set. **What breaks first:** the maths paper, on its first set-theory question.

**3. One family means two repositories must stay in step.** dewlab does not yet read the new parts: its header loop stops at an unknown key and turns that line into prompt text (`parse_question()`, `build.py:1522-1528`), and its `extract_blocks()` would show a `mark` fence as a read-only code listing (the "any other fence" branch). So today the family works in one direction only: tutorial to paper, with no edits. Paper to tutorial needs dewlab to learn to ignore `mark`, `checks` and exam-only types. The fix, and its cost, is one shared reader module (`dewfence.py`, the prototype's shape) that lives in dewlab and is copied into dewmark, with a CI check that the copy matches a pinned dewlab version, in the way dewlab already guards its vendor bundle (`standalone-bundle-is-current`). **What breaks first:** dewlab's question fence has changed four times since it shipped (7.182 maths, #314 notes, 7.235 no verdict, 7.255 the blank "choose" option). A fifth change made for tutorials could change how an already-sat exam rebuilds. Exams must therefore pin the reader version they were first built with, recorded in the names lock.

Two smaller costs. A mark fence per answer makes files longer than the paper-first layout (a practice PDP paper grows by about 130 lines). And headings as question boundaries mean a stray `##` inside a question ("## Hint") splits it; the checker catches this only when the split leaves a question with no marks.

**What ships first, and what waits.** First: the reader and checker (settings, headings, sections, the seven types, the four gap forms, `mark` with three methods, `solution`, the mutation test, the names lock), the PDP converter, and the samples converted. That is enough for the four PDP papers and the three non-programming samples. Next: `checks` in the workbench and practice pages, `accept:` numbering, the maths warnings from point 2, and dewlab learning to ignore exam fences. Later: `ordering` and `on-paper` in the workbench, significant figures on number gaps, the separate scheme file, and version A/B papers through the world suffix.

**Decisions for Josh.**

1. **Adopt the one-fence family as the exam grammar**, with dewlab's `question` fence unchanged at its centre. Recommended: yes, for the shared vocabulary and the tutorial-to-practice route; the cost is critique 1 and 3.
2. **Where the shared reader lives.** Recommended: in dewlab, copied into dewmark with a version check, because dewlab is where the fence was born and where it is exercised weekly. The alternative (dewmark owns it, dewlab copies) suits dewmark's stricter needs better but moves the tutorial parser's source out of the tutorial project.
3. **Mark fences beside answers, or a scheme at the back.** Recommended: beside, as the default, with `for:` allowing the back-of-paper layout for teachers who prefer it.
