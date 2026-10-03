# The exam file: the unified format

> **Status.** Adopted on 28 September 2026 (decision 21 in
> `planning/DECISIONS_2026-09-27.md`), with the ten choices in
> "Decisions for Josh" at the end taking their recommended options.
>
> **The reader** is `dewmark/reader.py`; `python -m dewmark check FILE`
> runs it. It reads the settings (§4.9), the split at `# Marking scheme`
> with the lookalike refusals (§4.1, §4.5 layers 1 and 2), headings,
> marks and sums (§4.2), fences, kinds and notes (§4.3), permanent names
> (§4.4), the marker's half with keys, points, criteria, model answers,
> tests and drafts (§4.6, §4.7), and gives the messages of §7 with stable
> codes. **The names lock** (§4.4) is `dewmark/lock.py`: `python -m
> dewmark lock FILE --sitting NAME` writes it, and `check` reads it.
> **The paste route** (§4.10) is `dewmark/package.py` and
> `dewmark/reply.py`: `python -m dewmark package MODE FILE` makes the
> text to give an assistant, and `python -m dewmark reply MODE PAPER
> REPLY` checks what came back. **The checker page** (`checker/`, on the
> dewmark site) runs the reader and the paste route in a browser.
> **The marker's half as JSON** (§4.6) is `dewmark/scheme_json.py`, and
> **the search and the mutation test** (§4.5 layers 3 and 4) are
> `dewmark/secrecy.py`. **The pages** are built by `dewmark/render.py` and
> `dewmark/build.py` (`python -m dewmark build FILE -o DIR`): a student page,
> a practice page and an answer key, and the marking scheme as JSON, with
> both secrecy layers run over every page built, so a paper that lets the
> scheme or a hint through is refused (`DECISIONS_LOG.md`, entry 0.12). The
> page draws `answer`, `maths`, `essay`, `code`, `python exec` (an editor
> only, until step 5), `choice`, `boxes`, `blanks` and `table`; a paper using
> `match`, `order`, `photo` or `on-paper` is refused with a message until
> step 8. The two start screens, reading settings, branding and the list of what a
> paper needs are built (`DECISIONS_LOG.md`, entry 0.13); the timer, breaks and PDF
> of step 4 are not. A paper's **fingerprint** (the Paper ID students see) is made when
> it is built, from the paper above the marking scheme and the pictures it carries
> (`dewmark/receipt.py`, `docs/ANSWER_FILE.md`).
> Not yet built: the dewlab import form (§4.11) and the JSON schema for a
> connected model (§4.10). `build_exam.py` still builds the pages of the
> older format in `planning/THE_EXAM_FILE.md` for the workbench, which reads
> only those pages' submissions until step 6. Where the reader, the lock, the
> paste route, the secrecy layers and the pages depart from the text below is
> in `DECISIONS_LOG.md`, entries 0.7 to 0.12. The three rival
> proposals this document judges, and the other files it names, are kept
> in history at commit `b3823f91799f` under
> `planning/research-2026-09-27/design/`. Decision 22 later added an
> automatic practice build with `hint` blocks (see the proposal's D2);
> this document does not yet describe those.


*Design round 2, 2026-09-27. This document judges the three rival proposals (`format-paper-first.md`, `format-typed-blocks.md`, `format-one-fence-family.md`) and sets out the one format dewmark should build. It follows Josh's twenty decisions (`planning/DECISIONS_2026-09-27.md`); where a proposal and a decision differ, the decision wins. Every claim marked **(run)** was checked with one of the three prototypes, or with `unified.py`, a patched copy of the paper-first reader that implements the changes below. Scratch files, including the hostile test papers, are in `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/design-round/format-judge/` (`pf/`, `tb/`, `of/`, `unified.py`, `specimen.exam.md`, `pdp-sample.exam.md`). None of it is in either repository.*

## The verdict in brief

**Paper-first is the base.** It is the only proposal whose file a teacher who is not a programmer could read aloud as the paper, and it converts the four PDP papers with the smallest change. It lost points on three things, all fixable: its checks let the whole marking scheme reach students if the one dividing line is misspelt; it gives ```` ```python ```` the opposite meaning to dewlab and to every Markdown reader; and it compares any key that starts with a digit as a number, which brings back the YAML trap it set out to remove.

**Grafted from typed blocks:** strict reading (every value is text, closed lists, "Did you mean…?"), a registry entry per answer box with a fixed key shape, inner names recorded in the names lock with their text, the full-page leak search, and a JSON form of the file for a connected model that dewmark then writes out as text.

**Grafted from one fence family:** dewlab's meanings for code fences (```` ```python ```` is a listing, ```` ```python exec ```` is a cell the student runs), a named `material` fence for material shared by some parts, the mutation test, the reader version pinned in the lock, and dewlab's `question` fence accepted as an import form in practice papers.

**New, from the hostile cases:** lookalike scheme headings and scheme-shaped lines above the line are refused; an exam with no scheme is refused; keys are text unless they carry a tolerance; starter text that resembles the model answer is refused; "Award 2 marks for…" in a scheme gets a suggested rewrite; one mistake gives one message.

---

## 1. Breaking the proposals

Each proposal was given the same sixteen hostile cases. **(run)** means a prototype was fed a test paper (`format-judge/pf/h*.exam.md`, `tb/t*.exam.md`, `of/o*.exam.md`); otherwise the outcome is read from the proposal's text. The last column is what the unified format does.

| # | Hostile case | Paper-first | Typed blocks | One fence family | Unified |
|---|---|---|---|---|---|
| 1 | The question shows code in a ```` ```python ```` fence | The listing becomes an answer cell; the message is "Two answer boxes would both be stored as q1", which points at the wrong thing (run, h01) | Listing shown correctly (run, t01) | Inside a `question` fence the inner fence closes it early; message "has no mark block" (run, o01) | ```` ```python ```` is a listing; a cell is ```` ```python exec ````; a box that ends early gets "use four backticks" |
| 2 | Two answer boxes with the same label | Refused, both lines named (run, h02) | Refused (run, t02) | Refused (run, o02) | Refused, both lines named |
| 3 | 2(b) renumbered 2(c) after a sitting | Build stops unless `version` changes (lock; not in prototype) | Allowed; names hold, but the graded paper prints "(c)" to a student who saw "(b)" | Allowed silently; same problem | Stops, as paper-first; the lock records the printed labels each sitting saw |
| 4 | "Answer any 2 of 3" with nested parts | Read from the section heading (run, h04) | `choose: 2`; sentence generated (run, t04) | `answer: any 2` (run, o04) | As paper-first |
| 5 | A part answered on paper | ```` ```on-paper ```` (run, h05) | `type: answer-on-paper` (run, t15) | `type: on-paper` | ```` ```on-paper ```` |
| 6 | Parts total 11 under a "(10 marks)" heading | Caught (run, h06) | Caught, twice: `total:` and `total_marks` (run, t06) | Caught, twice (run, o06) | Caught once; knock-on totals suppressed |
| 7 | `No`, `1.10`, `0123` as values | Text in settings, but a key "starting with a number is compared as a number": `0123` matches `123` (§4.3 of the proposal) | Text (run, t07); but an option reading "it is: a function" is refused until quoted (run, t09) | Text (run, o07) | Keys are text; a number comparison needs a tolerance |
| 8a | "Model answer:" written above the line | Refused (run, h08) | `expected:` in an answer box refused | Not applicable | Refused |
| 8b | The model answer pasted as starter text | Passes the prototype; the designed page search catches it only if the scheme repeats it | Passes (run, t08) | Passes: pre-filled text is public by design, so the mutation test cannot see it (run, o08) | Refused when starter text is close to a model answer |
| 8c | `# Mark scheme` or `# Solutions` for the dividing line | **Every marking point is shown to students**; the only message is "1 has no entry in the marking scheme" (run, h18) | Not applicable | A misspelt ```` ```marks ```` fence **is shown to students as a code listing** (run, o09) | Variants of "marking scheme" accepted; lookalikes and scheme-shaped lines above the line refused; an exam with no scheme refused (run, h18, h20) |
| 9 | A Word paper pasted by a model: en dashes, "1.(a)", "Q1 b)", `Answer: “B”` | Numbers all parsed (run, h09); curly quotes in the key kept, so "“B”" never matches | Numbers are generated, but the model must invent every name; "“B” is not one of the options" (run, t17) | Odd message for “B” (run, o09) | Curly quotes tidied in keys and headings |
| 10 | A table used by 5(a) to 5(c); a figure used by (d) and (e) only | Table before the first part is shared (run, h10); no way to share with (d) and (e) only | `stimulus`, only before the first part | `stimulus` plus `see:` per part, any subset (run, o10) | Implicit sharing plus a `material` fence |
| 11 | A multiple-choice option that is itself code | Four-backtick outer fence (run) | Works only if the inner fence is indented four spaces; at two, PyYAML's own words: "found character '`' that cannot start any token" (run, t18) | Four backticks (run, o11) | As paper-first |
| 12 | A number with units and a tolerance | `Answer: 4.88 m ± 0.01`; a second `Answer:` line in the same entry is accepted silently (run, h12) | `value`, `tolerance`, `units` (run, t12): the clearest | `{= 4.88 ± 0.01 m}`; but `A = {1, 2, 3}` in a sentence silently becomes a gap whose key is "1, 2, 3" (run, o12) | Paper-first's phrase; two `Answer:` lines refused |
| 13 | A misspelt fence word (`anwser`) | Refused | Refused, with a suggestion | **Shown to students as a code listing**; message is about the orphaned mark block (run, o14) | Refused with "Did you mean ```` ```answer ````?" (run, h21) |
| 14 | A stray heading inside a question (`## Hint`, `### Table 1`) | Treated as text (run, h13) | `###` refused outright (run, t13) | `## Hint` becomes a new question and takes the marks, silently (run, o13) | As paper-first; warned if it looks numbered |
| 15 | Python pasted into a starter without indenting | Kept as written | "\"def f(x)\" is not a setting an answer box can have" (run, t14) | Kept as written | Kept as written |
| 16 | A scheme written Word-style: "Award 2 marks for…", "(2)", "2m:" | Read as guidance; the tick boxes vanish without a word (run, h15) | A method must be named, so the teacher is asked | Guidance | Read as guidance, with a warning and the rewrite |

**What the cases show.** The two worst failures (8c, 13) are the same failure: a small spelling slip turns secret text into student-visible text. Paper-first and one fence family both have a path from a typo to a leak; typed blocks does not, because it has no fall-through to "show it". The unified format closes both paths by refusing anything that looks like a scheme or a fence it does not know. Typed blocks fails differently: its errors are caught, but the teacher meets YAML's rules (quotes around colons, indentation) and, in two cases, messages no teacher could act on. One fence family's brace gaps (12) and its heading-as-boundary rule (14) produce silent mistakes, the kind no message can fix.

---

## 2. Scores

Each proposal was scored 1 (poor) to 5 (strong) on eight criteria.

| Criterion | Paper-first | Typed blocks | One fence family |
|---|---|---|---|
| Ease of writing by hand for a non-programmer | 5 | 2 | 4 |
| Reads like the paper | 5 | 2 | 3 |
| Stable names | 3 | 5 | 4 |
| Builder checks and messages | 3 | 4 | 2 |
| How reliably a language model can produce it | 4 | 3 | 4 |
| Coverage and extensibility (a type registry) | 3 | 5 | 3 |
| Migration cost from the PDP papers and the samples | 5 | 4 | 4 |
| One family with dewlab's `question` fence | 2 | 1 | 4 |
| **Total (of 40)** | **30** | **26** | **28** |

**Ease and reading.** Paper-first asks for headings with marks and one word per box; the rest is the paper. One fence family adds an `id:` and a `mark` fence per answer, which is learnable but interrupts the paper every few lines. Typed blocks turns headings into `title:` settings, wraps every part in a block, and asks for quoting and indentation rules; its own self-critique predicts the first teacher who writes a code paper in Notepad will stall.

**Names.** Typed blocks is strongest: names are written, inner names too, and the lock records option text, so swapping options after a sitting is refused. One fence family writes ids but stores gaps and options by position. Paper-first derives names from printed numbers and captions: right for exams (the number is what everyone quotes), but a caption typo fixed after a sitting needs special logic, and a practice paper that gains a part mid-term shifts every later name.

**Checks.** Typed blocks' closed lists catch the most, but raw PyYAML errors reach teachers (t18) and one message misleads (t14). Paper-first's sums and number checks are good, but it has the 8c leak and silent guidance (16). One fence family has three silent or leaking paths (12, 13, 14).

**Models.** A model writing paper-first copies the Word paper and adds fences; it invents no names. One fence family is close, but the model must coin ids. Typed blocks scores lowest for the paste route that ships now (decision 20), because models slip on YAML quoting and indentation; it would score 5 with a connected model and a JSON schema, which the unified format grafts in (§4.10).

**Coverage.** Typed blocks maps one-to-one onto the registry in `question-types.md` §2.2: each type has closed public settings and a key shape. Paper-first's per-box phrases in the scheme will grow into small languages (its self-critique 3). One fence family folds matching, labelling and tables into fill-in-the-blank, so an exporter cannot tell a matching question from a sentence with gaps.

**Family.** One fence family's claim holds in one direction only. A tutorial fence copied into a paper passes its checker, but dewlab's `parse_question` accepts only a digit for `answer:` (`/home/user/dewlab/build.py:1556`), knows only two types (`build.py:175`), and would show a `mark` fence as a listing; its own self-critique says so. Paper-first departs from dewlab on gaps and on what ```` ```python ```` means.

**The choice.** Paper-first wins on the three criteria a teacher feels every day (writing, reading, converting). Its weaknesses are in checks, names and the registry, which are the builder's business and can be fixed without changing what a teacher writes. The grafts below do that.

---

## 3. What each graft costs

| Graft | From | Cost to the teacher | Cost to the builder |
|---|---|---|---|
| Values read as text; closed lists; did-you-mean; duplicate settings refused | Typed blocks | None | Small: the reader already reads text |
| A registry entry per box kind: body grammar, key shape, inner names, stored shape | Typed blocks | None | The registry refactor in `question-types.md` §2, planned anyway |
| Lock records inner names with their text | Typed blocks | None | Small |
| JSON form for a connected model, written out as text | Typed blocks | None | About a day, after the registry |
| ```` ```python ```` a listing, ```` ```python exec ```` a cell | One fence family (dewlab) | One extra word per code cell | None; the PDP converter changes 11 lines per practice paper |
| `material` fence | One fence family (`stimulus`) | One new word, rarely needed | Small |
| Mutation test; reader version in the lock | One fence family | None | A CI test; one field |
| dewlab `question` fence as an import form | One fence family | None unless used | Second wave |

---

## 4. The unified format

### 4.1 The carrier

An exam file is a plain text file named `<code>.exam.md`, with `pictures/` and `data/` folders beside it. It is **CommonMark**, the precisely specified form of Markdown, read by one reader in pure Python (`markdown-it-py`), so the command line and the browser studio run the same code (decision 5). Before reading, the builder tidies Windows line endings, tabs, non-breaking spaces, and curly quotes in settings, headings, fence lines and scheme keys; prose keeps its typographic quotes. `$…$` is maths, typeset at build time wherever students read text: prose, options, box labels, table cells, keys.

A file has five layers, always in this order:

```
---
settings, one per line                      (§4.9)
---
the front page: everything before the first section or question
# Section A: … (N marks)                    optional sections
## Question 1: … (N marks)                  questions, parts, boxes, material
# Reference                                 optional side-panel cards
# Marking scheme                            the marker's half (§4.6)
```

The student page is built from the first four layers only. The fifth is split off before anything is rendered.

### 4.2 Headings: numbers and marks

| Written | Means |
|---|---|
| `# Section B: Answer any two of Questions 2 to 4 (20 marks)` | A section. "any N" (digits or words) sets a choice rule. |
| `## Question 3: Loops (20 marks)` | A question. It counts only if it carries a number and ends in marks. |
| `### 3(a): Tracing a loop (5 marks)` | A part. `### (a) …`, `### 3A: …`, `### 3.a …` also work. |
| `#### (i) First pass (2 marks)` | A sub-part, only when it has its own marks. |
| any heading without marks | Text, such as `## Instructions to candidates` or `#### Table 1`. Warned if it looks numbered. |

**Marks** are `(N marks)`, `(1 mark)`, `[N marks]` or `[N]`; halves are allowed. **Numbers** take the usual printed styles, including the PDP papers' `1A (i)` and section-numbered `B2(c)(ii)`. A `#` heading before the first question that is not a section, such as a repeated paper title, is refused: the title comes from the settings.

**Sums.** Parts add up to their question, questions to their section, sections to `total marks`. For "any N", the alternatives must be worth the same and outnumber N; the section is worth N of them. The page never blocks an extra attempt; the workbench counts the best N and the marker can override. When sums disagree, the builder reports the lowest level that disagrees and suppresses the totals above it.

**Marks come only from headings.** A box shares the marks of the heading it sits under, which is how the PDP papers are marked (1A's three boxes share 3 marks; 4B(i)'s function and tests share 4). In the workbench the unit a marker marks is the lowest heading with marks, shown with all its boxes.

### 4.3 Fences

A fence opens with three backticks and a word and closes with three backticks. A fence that must hold another fence opens with four. The line that opens a fence reads:

````
```KIND  LABEL  (NOTE) (NOTE)
````

**KIND** comes from the closed lists below. An unknown word is refused with the nearest match; it is never shown as code. **LABEL** is a printed number, optionally followed by `: caption`, and is needed only when a part has two or more boxes. **NOTES** are from a closed list: `(not marked)`, `(choose 2)`, `(about 800 words)`, `(6 lines)`, `(input: text, photo)`, `(letters may repeat)`.

**Answer boxes.** Each kind is one registry entry (§4.8).

| Kind | The student gets | The body is | Key shape in the scheme |
|---|---|---|---|
| `answer` | A written box that grows, with a word count | Starter text | none; model answer, points |
| `maths` | A maths box in the routes the paper allows: plain text with a "reads as" line and a symbol palette, the visual editor (MathLive), a photograph (decision 15) | Starter text | optional `Answer:` |
| `python exec` | A code cell with Run; all cells share one Python session | Starter code | model code, `tests` |
| `code` | A monospaced box with line numbers and no Run: pseudocode, SQL, a trace | Starter text | model answer |
| `essay` | A writing view with a word count against the note | Empty | criteria grid |
| `boxes` | One labelled box per line; `____` puts the box inside the line; a last line `Choose from: a / b / c` makes every box a drop-down | The labels | `Answers:` one per line |
| `blanks` | Text with gaps: `____` to type, `[a / b / c]` to choose | The text | `Answers:` one per gap |
| `table` | A table with `____` in the cells to fill | A pipe table | the completed table |
| `choice` | Lettered options; `(choose N)` allows several | `A.`, `B.` …, each may hold Markdown and code | `Answer: B`, or `A, C` |
| `match` | A drop-down of letters beside each numbered item | `1.`, `2.` …, then `A.`, `B.` … | `Answer: 1 B, 2 A, 3 C` |
| `order` | A list to reorder, with keyboard buttons | `A.`, `B.` … in the order shown | `Answer: C, A, D, B` |
| `photo` | A photograph of handwritten work | The instruction | model answer, points |
| `on-paper` | "Answer this on the sheet provided"; the mark is typed in the workbench | The instruction | model answer, points |

A box noted `(not marked)` is rough work: saved, printed and shown to the marker, labelled "Rough work · not marked", and left out of progress and finish checks. A number answer is a `maths` or `on-paper` working box plus a `boxes` answer line; label-the-diagram is a picture plus `boxes`. Neither needs a kind of its own.

**Gaps** (`____` and `[a / b / c]`) are three or more underscores, or square brackets holding options separated by ` / `. They are found before Markdown runs, as dewlab tokenises its gaps (`find_gaps`, `/home/user/dewlab/build.py:1471`), and never inside `$…$` or backticks. Every typed gap is the same width, unless a note says otherwise; dewlab sizes a gap from its answer (`build.py:1631`), which in an exam would leak the answer's length.

**Things students read**

| Written | Shown as |
|---|---|
| ```` ```python ````, ```` ```sql ````, ```` ```text ````, ```` ```pseudo ````, ```` ```output ```` (a closed list of languages) | A listing with line numbers, coloured for a language; `start=4` and `plain` (no numbers) are allowed |
| ```` ```python setup ```` | Code that runs before Begin, shown collapsed as "Set-up code (runs automatically)" |
| ```` ```material Figure 1 ```` | Its body (a table, picture, passage) shown where written, and kept available ("Show Figure 1") for the rest of the question |
| `![what it shows](pictures/cell.svg)` | A picture; the description is required |
| `[registry.db](data/registry.db)` | A data file, listed in the side panel and placed in Python's folder |
| raw HTML | Shown as text, never run |
| ```` ```hint ```` | A hint for the part or question it sits under. The practice page and the answer key show it folded under the box, as "Hint"; the student page leaves it out entirely. The search covers the hints' words in the student page along with the scheme's strings, and the mutation test makes the hints nonsense too and demands the same page (decision 22). |

**As built** (`dewmark/render.py`; `DECISIONS_LOG.md` 0.12). The page draws each kind of box as ordinary form controls named for the box, so the page needs nothing from a paper but its names: a `choice` is radio buttons, or check boxes when more than one may be chosen, each carrying its letter; `boxes`, `blanks` and `table` are one input or drop-down for each place to fill; `answer`, `maths`, `essay`, `code` and `python exec` are text areas that start with the body they were given, which counts as no answer until the student changes it. The height of a written box follows its marks. A picture is a `![description](path)` from inside the paper's own folder, and is built into the page as a data address; a picture that is missing, undescribed, remote, outside the folder (by `..`, a full path or a symbolic link) or not an image refuses the build. A link is shown as its text and its address, never followed. Raw HTML in prose, in a hint, in an option and in material is shown as text, never run.

**Shared material** needs no syntax when it sits between a question heading and its first part: it belongs to the whole question and stays available beside every part, as on paper. The `material` fence is for anything shared by some later parts only.

### 4.4 Names

**An answer's permanent name is the number printed beside it**, tidied: `q`, the question number and part letter, then `.` and the sub-part numeral, then `.` and the caption in lower case with dashes.

| As printed | Stored as |
|---|---|
| no label, under `### 1(a)` | `q1a` |
| `1A (i)`, `1(a)(i)`, `1a (i)` | `q1a.i` |
| `4B (i): your function` | `q4b.i.your-function` |
| `Question 1: rough work (not marked)` | `q1.rough-work` |
| `B2(c)(ii)` | `qb2c.ii` |

**Inner names**: options by printed letter, `match` items by number, `boxes` lines, gaps and table cells by position. Each registry entry declares its inner names.

**The names lock** (`architecture.md` §6) is written the first time a paper is published, for an exam sitting or as a practice page. It records every name and inner name with its kind, marks, printed label and, for options, match items and order items, their text; and the reader version that built it. After that:

- renaming, removing, retyping or re-marking a locked name stops the build, unless `version` changes;
- a change to an option's text or order stops the build, naming the stored answers it would misplace;
- a caption-only fix (same number, kind and position) keeps the stored name, and the builder says so;
- moving whole questions without renumbering keeps every name, with a warning;
- adding a box is always allowed.

A practice page restores saved work only from the same version, so a practice paper edited mid-term never puts an old answer in a new part.

**As built** (`dewmark/lock.py`; `DECISIONS_LOG.md` 0.8). The lock is `names.lock.json` beside the exam file. It holds each paper in the folder under its `code`, each version under its `version`, and each version's sittings. Until the studio's Issue button exists (step 7), `python -m dewmark lock FILE --sitting "2026-10-20 Group A"` writes it, and refuses a paper with problems; issuing the same version again adds the sitting and locks any new boxes. `python -m dewmark check` reads the lock whenever one sits beside the file. A part counts as renumbered when its title now sits under another number, or, if its title changed too, when a new number stands in its place; a question renumbered with its parts is reported once. Changing the `code` of a file that has been issued is refused. The problems are `renumbered-after-sitting`, `locked-part-removed`, `locked-box-removed`, `locked-marks-changed`, `locked-kind-changed`, `locked-options-changed`, `locked-inner-changed` (the number of gaps, lines or cells) and `code-changed-after-issue`; the warnings are `caption-changed`, `questions-moved` and `lock-reader-changed`.

**Why printed numbers, not written names.** The number is what the student, the scheme, the graded paper, the appeal and the external authenticator all quote. A written name is a second identity a teacher cannot see on the paper and a model must invent; that was typed blocks' price. The case it guards against, renumbering after a sitting, is exactly the case that should be refused: the student saw "2(b)".

### 4.5 Keeping secrets off the student page

Four layers, the first structural:

1. **Structure.** The file is split at `# Marking scheme` before anything is rendered. "Marking scheme" and "Mark scheme" are accepted in any capitals, with or without a colon. The student and practice renderers never receive the lower half.
2. **Refusals.** A `#` heading that begins "Solutions", "Answers", "Answer key", "Mark…" or "Scheme" is refused ("everything below it would be shown to students"). So is any line above the dividing line shaped like scheme text: `Answer:`, `Model answer:`, `- 2 marks: …`, a criterion. A `kind: exam` file with no scheme is refused. A starter text or starter code closer than 80% to a model answer is refused.
3. **Search.** The builder searches the whole built page, **including the embedded data block today's check skips** (`code.md` §1, stage 5), for every scheme string of eight characters or more.
4. **Mutation test.** In CI, every scheme string is replaced with nonsense and the student page rebuilt; it must be byte-identical. This guards the renderers, not the teacher: it fails when a future box kind lets a key through.

**As built** (`dewmark/secrecy.py`; `DECISIONS_LOG.md` 0.11). `scheme_strings(text)` lists every string of the scheme a page could give away: keys, model answers, tests, points, criteria, bands, the marker's guidance a line at a time, and any text below the line that is in no entry. Strings shorter than eight characters, and strings the paper itself shows, are listed but not searched. `find_leaks(page, strings)` looks for each in the whole built page, data and scripts included (the check this replaces stripped scripts first), as written, escaped for HTML, and escaped for JSON, ignoring capitals and spacing; a string over 40 characters is also looked for by its first and last 30, since a page may show only an excerpt (each piece only if the paper does not already show it, as a point may open with the question's own words). `mutation_test(text, build)` writes the scheme again with nonsense in place of everything it says and a different valid key for each choice, match, order and drop-down box, builds the page from both files, and demands the same bytes; if they differ it names the entries that make the difference. Neither layer knows how a page is made: `build` is any function from the text of an exam file to a page.

A practice or sample page receives keys, model answers and tests on purpose, locked until the student finishes the whole paper (decision 14). `show answers` and `practice tests` on a `kind: exam` file are refused.

### 4.6 The marker's half

Below `# Marking scheme`, entries are found by the number they mark.

| Line | Meaning |
|---|---|
| A heading starting with a number: `### 2(a)`, `### 2(a): answer`, `## Question 2` | The entry for that part, box or question. Level does not matter. `(draft)` at the end marks it unchecked. |
| `Answer: …` | The key for a single box or gap |
| `Answers:` and a numbered list; `Answers (any order):` | One key per box or gap, in order |
| `Model answer: …`, or a code fence | The model answer |
| ```` ```tests ```` | Hidden tests for code (§4.7) |
| `- 2 marks: …` | A point to tick |
| `- **Name** (15 marks)` with indented `- 13 to 15: …` | A criterion and its bands |
| `Topic:` / `Outcomes: 3, 7` | Fields for the marks spreadsheet and QQI records; outcomes are checked against the paper's `outcomes` list |
| anything else | Guidance for the marker |

**Methods.** Each entry uses one: **marks out of a total** (guidance only; the marker types a number in half-mark steps), **points** (tick boxes, capped at the part's marks; points must reach the part's marks and may exceed it for "any of"), or **criteria** (criteria add up to the part; each criterion's bands run from 0 to its top with no gap or overlap). The method is read from the lines, a mix of points and criteria is refused, and the preview labels every part "Marked by points: 5 listed, up to 4 marks". A guidance line that starts like a mark ("Award 2 marks for", "(2)", "2m:") gets a warning with the rewrite.

**Keys.** Alternatives are separated by ` / `, with spaces, so `3/8` is one answer. A key is **text**, compared ignoring capitals, spacing and quote style. It is compared **as a number** only when it carries a tolerance, a range or a precision: `4.88 ± 0.01 m` (`+-` also works), `± 2%`, `12.4 to 12.6 cm`, `(2 d.p.)`, `(3 s.f.)`, and `± 0` for an exact number. A number-shaped text key such as `40` also reports "agrees as a number" to the marker, as a separate fact, so `0123` and `123` are never silently treated as the same. A unit written after the number is part of the key; the student types number and unit in one box, and a missing or different unit is shown to the marker, never converted. A `choice` key may carry a check phrase: `Answer: B (range(1, 6))` makes the builder confirm that option B contains "range(1, 6)", which catches options swapped before issue. Two `Answer:` lines in one entry are refused.

In line with decision 13, a key proposes a mark on a closed box and gives evidence on the rest; the marker confirms every mark.

**As JSON** (`dewmark/scheme_json.py`; `python -m dewmark scheme FILE -o OUT`). The marker's half is written as `dewmark-scheme/1`: the paper's identity and total, the names (every part and box with its kind, marks and the text of each option, from the names lock's snapshot), and one entry for each heading of the scheme in file order, with its marks, the box its key belongs to, its method, key, model answer, tests, points, criteria and guidance. A number with a rule is a number (`{"number": 4.88, "tolerance": 0.01, "unit": "m"}`); everything else, `0123` included, is text. The file is stable, so a change to a scheme shows in a diff. It holds the paper's secrets and goes in the teacher's folder, never one students receive. A field may be added later; one is not renamed or taken away without a new format number.

### 4.7 Model answers, tests, drafts

**Model answers** are a `Model answer:` paragraph or a code fence. They appear in the answer key and the workbench, and on a practice paper after the student finishes.

**Hidden tests** are a ```` ```tests ```` fence, one test per line, in the three shapes the PDP papers need:

```
longer_word("cat", "horse") == "horse"
run with input: 17 | prints: junior
after run: len(odd_numbers) == 10
```

A plain line is a Python expression that should be true after the part's cells have run. `run with input:` runs the program, typing each input in turn (inputs separated by ` / `), and looks for the text after `prints:`. `after run:` checks a value after the whole cell has run. In the workbench a fresh Python session runs the set-up code, the part's cells, then each line, and the marker sees which pass. On a practice paper with `practice tests` on, the same lines run in the student's page (decision 16). They are never placed in an exam page.

**Drafts.** An entry ending `(draft)` is labelled "draft" everywhere. A draft builds for preview and practice; an exam cannot be issued while one remains.

### 4.8 The registry

Each box kind is one folder in `dewmark/types/` (`question-types.md` §2.2): the builder half (body grammar, notes allowed, key shape, checks, student, print and key markup, exports), the page half (collect, restore, answered, reveal), the workbench half (view, summary, suggest), a README that is the cheat-sheet line, an example that is the studio's Insert snippet, and fixtures. **Adding a kind never changes the format**: an unknown kind is refused today, and tomorrow's kind is one more folder and one more row in §4.3. The registry is also what the JSON schema for a connected model (§4.10) and the GIFT and Moodle XML exports are generated from.

The second-wave maths kind, a one-line final-answer expression with a `(factorised)`-style form check (`question-types.md` §4.5), arrives this way, as `maths` with a key shape `Answer: (x - 4)(x + 2) (factorised)`.

### 4.9 Settings

Settings are `key: value` lines between two `---` lines. Capitals, spaces, underscores and hyphens in a key are ignored, so `time_allowed` and `Time allowed` are one key. Every value is text until the builder converts a key it knows. An unknown key, a repeated key, or a value outside a key's list is refused with the nearest match. Switches accept `on`/`off`, `yes`/`no` and `true`/`false` in any capitals, because the key's type is known.

| Setting | Example | Notes |
|---|---|---|
| `dewmark` | `1` | The format version. A file without it is offered **Upgrade this file**. |
| `code` | `pdp-5n2927-exam-2027` | Permanent: file names, save keys, the lock. Required. |
| `version` | `1`, `2026.10.01` | Any text; default `1`. |
| `kind` | `exam`, `practice`, `sample` | Sets the EXAMINATION or PRACTICE band (decision 12). Required. |
| `title`, `module`, `module code` | Written Examination; Programming and Design Principles; 5N2927 | Required for an exam. |
| `institution`, `college`, `session`, `logo` | Dublin and Dún Laoghaire ETB; Dublin College Dundrum; 2026–2027; `pictures/dcd-logo.svg` | Branding (decision 12); logo optional, 150 KB at most. No colour setting yet. |
| `total marks`, `time allowed` | `60`; `2 hours` | Required. |
| `timer` | `none`, `shown`, `enforced` | Default `shown` when there is a time, else `none`. The student can always hide it (decision 11). |
| `breaks` | `on`, `off` | Default `off` (decision 11). |
| `calculator` | `none`, `basic`, `scientific` | Default `none`. |
| `maths input` | `text, visual, photo` | Default `text` (decision 15). A box may narrow it with `(input: …)`. |
| `hand in` | Upload your PDF and answer file to "PDP exam" on Moodle. | Finish-screen wording. Every hand-in includes a PDF (decision 10); the data file's form is dewmark's choice, not the paper's. |
| `python from` | `this file`, `internet` | Default `this file` (decision 7); `internet` on an exam is warned, not refused. |
| `python packages` | `sqlite3, pandas` | Checked against the pinned Python kit. |
| `python time limit` | `10 seconds`, `off` | Per run. |
| `code completion`, `error hints` | `on`, `off` | Defaults `off` and `on`. |
| `python reference` | `yes`, `no` | Adds dewmark's standard Python sheet. |
| `show answers` | `never`, `after finishing` | Practice and sample only (decision 14). |
| `practice tests` | `never`, `after finishing`, `while working` | Practice and sample only (decision 16). |
| `weighting`, `technique`, `outcomes` | `30%`; `Examination-Theory`; `1, 3, 6, 7, 8` | For QQI records. |

**As built** (`dewmark/build.py`; `DECISIONS_LOG.md` 0.13). The band at the top of every screen shows `institution` and `college` on one line, `module` with its `module code`, the `session`, the time allowed and the total marks, under a word that says whether the page is an examination, a practice version or an answer key. `logo` is a picture file inside the paper's own folder (SVG, PNG, JPEG, GIF or WebP), at most 150 KB, carried in the page; one that is missing, outside the folder, remote, not a picture or too large stops the build (`logo-unavailable`, `logo-too-big`). The Get ready list is the paper, its fonts, and, when the paper has a `python exec` box or a set-up block, Python with where it comes from (`python from`), the `python packages` and the set-up code; the page adds the two ways of saving unless it is the answer key. Hostile words in any of these are shown as text.

The student's name and number are always asked, on the one combined start screen (decision 9), so there is no setting for them; `number example: D00123456` sets the hint. The Get ready list is generated from what the paper declares (Python, packages, data files, set-up code), so a teacher never configures a loading screen. **Reference cards**: each `##` under `# Reference` becomes one side-panel card, which is where a formula sheet goes.

### 4.10 Conversion by a language model

**The paste route** (decision 20) ships first. The studio prepares a package for any assistant: the cheat sheet (§8), a specimen paper for the subject, and the teacher's exam, with no student data. The reply is pasted back and checked by the same builder; a "Copy these problems" button hands the messages back to the assistant. The model's output looks like its input: Word papers are already numbered headings with "(15 marks)", and Word schemes already read "1(a) … 2 marks". The model invents no names.

**With a connected endpoint** (decision 18), the model returns JSON under a schema generated from the registry (typed blocks §8): closed kind lists, fixed notes, a key shape per kind. Local model servers turn such a schema into a grammar the model cannot step outside (`local-llm.md` §1). dewmark then writes the JSON out as the text format, so the teacher still reads a paper.

**As built** (`dewmark/package.py`, `dewmark/reply.py`; `DECISIONS_LOG.md` 0.9). The modes are `copy`, `tidy`, `plain`, `udl` and `invite`. A package opens with the notice, then says what to do, gives the rules for the reply, the cheat sheet (§8) and the paper, and for `copy` also a short specimen and the settings block the teacher filled in. The wording modes send the paper half only: `# Reference` and `# Marking scheme` and everything after them stay on the teacher's computer and are joined back unchanged. The assistant is asked to return the paper between `=== BEGIN PAPER ===` and `=== END PAPER ===`, and its notes between `=== BEGIN NOTES ===` and `=== END NOTES ===`; a reply without markers, in a code fence, or with chat above the settings is still found.

A wording mode's reply is refused, with every reason listed, if it changes a setting (`reply-settings-changed`); a heading's number, marks or "any N" (`reply-heading-changed`); any line of an answer box or listing, including the text inside (`reply-box-changed`); a number in the prose (`reply-number-changed`); a formula, a piece of code in backticks or a picture's file name (`reply-formula-changed`); or if it carries a scheme or reference cards (`reply-has-scheme`). A reply that keeps all of these is shown as a list of changes, each with the passage before and after, the part it is under and an id. The teacher takes or leaves each one; leaving them all gives the teacher's file back exactly. A numbered list turned into bullets is not a change of number. Wording inside an answer box, such as the options of a `choice` or the sentences of `blanks`, is not reachable yet; it is fixed, because the scheme and the lock key on it.

A `copy` reply must begin with the settings the teacher gave (`reply-settings-changed`). Its words are compared with the Word text in order: every difference is a warning naming the words (`reply-words-changed`), a number in the Word text that the reply lacks entirely is refused (`reply-number-lost`), and one it has fewer times is a warning (`reply-number-fewer`). The paper is then read by the reader, whose messages come back with their own codes, and a marking scheme of `(draft)` entries is added, as the PDP converter does. A scan for e-mail addresses, PPS numbers, phone numbers, long numbers and "student number:" runs before a package is offered; it asks the teacher to check, and never refuses, since a paper has numbers of its own.

**Decision 19's modes** change only prose above the line. A mode's reply that changes a heading's number or marks, a fence line, or anything below the line is refused, not merely flagged, and every wording change is shown as a plain difference the teacher reads line by line. "Copy without composing" should produce a paper half almost identical to the source text, which the studio can check by matching paragraphs.

### 4.11 The dewlab bridge

Three things make the exam file one family with dewlab's tutorials:

1. **Code fences mean the same.** ```` ```python ```` is a listing, ```` ```python exec ```` a cell the student runs, ```` ```python setup ```` set-up code, in both projects.
2. **Maths is the same.** `$…$`, typeset at build time.
3. **dewlab's `question` fence is an import form** (`build.py:1515`; `DECISIONS_LOG.md` 7.179). In a practice or sample paper, the builder reads it as written: `type: multiple-choice` becomes a `choice` box, `answer: 2` its key; `type: fill-in-the-blank` becomes `blanks`, each `{word}` a gap with that key and each `{right|wrong}` a drop-down shown in written order, never shuffled. In an exam paper the fence is refused with the offer **Move answers to the marking scheme**, which rewrites it into native boxes and scheme entries. The split happens in the reader, and the mutation test covers it.

The reverse direction, an exam box into a tutorial, is a copy and a rewrite and is not promised. dewlab's `question` fence has changed four times since it shipped (7.182, #314, 7.235, 7.255), so the lock records the reader version, and an already-sat exam never rebuilds under a newer reading.

---

## 5. Worked examples

Examples (a) to (e) make one specimen paper, `format-judge/specimen.exam.md`. `unified.py` reads it with no problems **(run)**: 6 questions, 24 boxes (2 rough work), 96 marks, 1 draft entry.

### (a) A PDP-style question: listing, labelled boxes, code cells, rough work

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
total marks: 96
time allowed: 2 hours 30 minutes
timer: shown
calculator: scientific
maths input: text, visual, photo
python from: this file
python reference: yes
show answers: after finishing
practice tests: after finishing
hand in: Keep your PDF and answer file. In the real exam you will upload both to Moodle.
---

## Instructions to candidates

1. Answer Section A, **two** questions from Section B, Section C and Section D.
2. Your work saves as you go.

# Section A: Programming (17 marks)

## Question 1: Functions (17 marks)

### 1(a): Parts of a function (6 marks)

Study the following function. For each term below, give its name or value in this function, and explain what the term means.

```python
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

```python exec 1(b)(i): your function
# Write your function here
```

```python exec 1(b)(i): your tests
# Call your function and write your tests here
```

#### (ii) Counting a letter (5 marks)

Write a function named `count_letter` with two arguments, `text` and `letter`. It must use a loop to count how many times `letter` appears in `text`. Do not use `.count()`.

```python exec 1(b)(ii): your function
# Write your function here
```

```python exec 1(b)(ii): your tests
# Call your function and write your tests here
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

### 1(b)(ii) (draft)

```tests
count_letter("banana", "a") == 3
count_letter("", "a") == 0
```

- 2 marks: a loop that visits every character
- 1 mark: the count is returned, not printed
- 1 mark: `.count()` is not used
- 1 mark: at least two tests, including one where the letter is absent
````

The six `boxes` lines share 1(a)'s 6 marks, and the two cells of 1(b)(i) share its 4; nobody invents a split. Stored names: `q1a`, `q1b.i.your-function`, `q1b.i.your-tests`, and so on.

### (b) Maths: any 2 of 3, a number with tolerance and units, typed maths

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

```maths 3(b): working (input: text, photo)
```

```boxes 3(b): answer
x = ____
x = ____
```

## Question 4: Cards (10 marks)

A card is drawn at random from a standard deck of 52. Find the probability that it is a heart or a king, as a fraction in its lowest terms.

```on-paper 4: working
Show your working on the answer sheet headed "Question 4".
```

```boxes 4: answer
P(heart or king) = ____
```
````

```markdown
### 2(a)

Answer: 4.88 ± 0.01 m

Model answer: $h = \sqrt{5.2^2 - 1.8^2} = \sqrt{23.8} = 4.878\ldots \approx 4.88$ m

- 3 marks: Pythagoras with the ladder as the hypotenuse
- 2 marks: correct working to 4.878
- 1 mark: 4.88 with the unit

### 2(b)

Answer: 70 ± 1 °

- 2 marks: $\cos\theta = 1.8 / 5.2$, or an equivalent ratio using 2(a)'s answer
- 1 mark: 69.7° before rounding
- 1 mark: 70°

Follow through from the student's own answer to 2(a).

### 3(a)

Answer: (x - 4)(x + 2) / (x + 2)(x - 4)

An expanded answer earns no marks.

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

2(a)'s key is compared as a number because it has a tolerance. 3(a)'s is text with two accepted forms. 4's `4/13` is one answer, because a slash without spaces is not a separator. Question 4 shows the paper route for working: the workbench gets a box for the working mark and the typed final answer beside it.

### (c) Biology: a shared table, a figure shared by two parts, a label bank, matching

````markdown
# Section C: Biology (19 marks)

## Question 5: Enzymes and cells (19 marks)

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

The rate of the reaction is 1 ÷ time taken. Work out the rate at 40 °C, to two decimal places, and give its unit.

```boxes
Rate = ____
```

### 5(c): The result at 60 °C (4 marks)

Explain why no result was recorded at 60 °C.

```answer
```

```material Figure 1
![A plant cell with three numbered pointers. Pointer 1 points to the thick outer boundary. Pointer 2 points to one of several small oval bodies near the edge. Pointer 3 points to the large pale space in the middle of the cell.](pictures/plant-cell-3.svg)
```

### 5(d): Parts of a cell (3 marks)

Name the parts labelled 1 to 3 in Figure 1.

```boxes
1 ____
2 ____
3 ____
Choose from: cell wall / cell membrane / nucleus / chloroplast / vacuole / mitochondrion
```

### 5(e): Where it happens (4 marks)

Complete each sentence. Use Figure 1 to help you.

```blanks
Photosynthesis takes place in the [chloroplast / nucleus / vacuole].
The cell wall is made mostly of ____.
```

### 5(f): What each part does (3 marks)

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

```markdown
## Question 5

Topic: enzymes; cell structure
Outcomes: 2, 4

### 5(a)

Answer: 40

### 5(b)

Answer: 0.50 ± 0.005 per minute (2 d.p.)

- 2 marks: 1 ÷ 2 = 0.50
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

Answers:
1. chloroplast
2. cellulose

- 2 marks: chloroplast
- 2 marks: cellulose

### 5(f)

Answer: 1 B, 2 A, 3 C
```

The table sits between the question heading and 5(a), so it stays available beside all six parts. Figure 1 is a `material` fence, available from 5(d) on. 5(a)'s key `40` is text; a student who types "40 °C" is shown to the marker as "agrees as a number", and the marker decides. 5(c) lists 5 marks of points for a 4-mark part, which is allowed: the total stops at 4. The builder checks that every keyed label in 5(d) is in its bank.

### (d) Multiple choice with an option that is code

`````markdown
### 1(c): Reading a loop (2 marks)

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

Scheme entry: `### 1(c)` then `Answer: B (range(1, 6))`. Option C holds its own listing, so the box opens with four backticks. The answer is stored as the letter, and the lock records each letter's text. The check phrase means that if someone swaps A and B before issue, the builder says so instead of issuing a wrong key.

### (e) An essay with a criteria grid

````markdown
# Section D: Essay (40 marks)

## Question 6: Recording lectures (40 marks)

"Every lecture should be recorded." Discuss.

Use the planning box first if it helps. It is handed in but carries no marks.

```answer 6: plan (not marked)
```

```essay (about 800 words)
```
````

```markdown
### 6

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

Changing Clarity to `(8 marks)` gives one message: "The criteria for 6 add up to 38, but it is worth 40."

---

## 6. The PDP Sample exam, converted

The whole Sample converts by script; `format-judge/pdp-sample.exam.md` passes `unified.py` **(run)**: 60 marks, 17 boxes (1 rough work), 13 draft entries. The paper half differs from the PDP source in 61 lines of 271. Question 1 and Question 4, as converted:

````markdown
---
dewmark: 1
code: pdp-5n2927-sample
version: 1
kind: sample
title: Sample Examination
module: Programming and Design Principles
module code: 5N2927
session: 2025–2026
institution: Dublin and Dún Laoghaire ETB
college: Dublin College Dundrum
total marks: 60
time allowed: 2 hours
timer: shown
weighting: 30%
python from: this file
python time limit: 10 seconds
code completion: on
error hints: on
python reference: yes
show answers: after finishing
hand in: Keep your PDF and answer file. In the real exam you will upload both to Moodle.
---

**Weighting:** 30% of the module (60 marks, divided by 2).  **Time allowed:** 2 hours.

## Instructions to candidates

1. Answer all four questions. Each question is worth 15 marks, and the paper is marked out of 60.
4. When a program asks for input, a line for your reply appears in the output under the cell. Type your answer there and press Enter.

## Question 1: Programming Languages and Variables (15 marks)

### 1A: Programming languages (3 marks)

**(i)** Name three high-level programming languages.

```answer 1A (i)
```

**(ii)** Explain the difference between a compiler and an interpreter. Is Python usually compiled or interpreted?

```answer 1A (ii)
```

**(iii)** Put the following in order, from the oldest to the newest: Python, machine code, FORTRAN, assembly language.

```answer 1A (iii)
```

### 1B: Variable names (3 marks)

Which of the following are permitted as variable names in Python? Rewrite each one that is not permitted so that it becomes a permitted name.

(i) `total score`
(ii) `total_score`
(iii) `3rd_place`

```answer 1B
Permitted:

Not permitted:

My fixed versions:
```

You can use this cell to test your fixed names. It is not marked.

```python exec 1B: test your names (not marked)
# Try creating each fixed variable here, for example:
# my_name = 1
```

## Question 4: Functions (15 marks)

### 4A: Parts of a function (6 marks)

Study the following function. For each term below, give its name or value in this function, and explain what the term means.

```python
def shout_first_word(sentence: str) -> str:
    words = sentence.split()
    first = words[0]
    return first.upper() + "!"

print(shout_first_word("hello there friend"))
```

```boxes 4A
Function name
Parameter(s)
Variable declaration(s)
Return statement
Function call
What would happen if the last line (the function call) were removed?
```

### 4B: Writing functions (9 marks)

#### (i) Longer word (4 marks)

Write a function named `longer_word` that takes two strings as arguments and returns whichever string is longer. If both strings have the same length, it returns the first string.

```python exec 4B (i): your function
# Write your function here
```

```python exec 4B (i): your tests
# Call your function and write your tests here
```
````

The scheme half arrives as a skeleton, one `(draft)` entry per marked part, for Josh to fill:

```markdown
# Marking scheme

## Question 1

Topic:
Outcomes: 1, 3

### 1A (draft)

### 1B (draft)

## Question 4

### 4A (draft)

### 4B(i) (draft)
```

Lines elided from the instructions and from 1B's list are unchanged from the source. What the converter changed: `exam_id` became `code`; `duration_minutes: 120` became `time allowed: 2 hours` with `timer: shown`; `module` was split into module and code; the dead `reference_theory` key went; the `#` line repeating the title went; ```` ```python LABEL ```` became ```` ```python exec LABEL ````; ```` ```text ```` became ```` ```python ```` (a listing, coloured as Python, as PDP showed it); `(optional)` became `(not marked)`; `fields` became `boxes`; the bold `**(i) Longer word (4 marks).**` became a `####` heading. Instruction 4 was reworded by hand, because it described PDP's pop-up. Stored names: `q1a.i`, `q1a.ii`, `q1a.iii`, `q1b`, `q1b.test-your-names`, …, `q4a`, `q4b.i.your-function`, `q4b.i.your-tests`. A `pdp-exam/1` submission's `"label": "1A (i)"` maps to `q1a.i`, so papers already sat under PDP can be opened in the workbench.

---

## 7. Builder messages

Every message has three parts: where (line, number, short title), what is wrong, what to do. Each carries a stable code linking to a help page. One cause gives one message; totals above a disagreeing part are not reported again.

> **Line 91 · Question 2 · marks don't add up** (`marks-sum`)
> Question 2's parts add up to 11 marks, but its heading says (10 marks): 2(a) is 6 and 2(b) is 5.
> Change one part's marks, or the heading.

> **Line 140 · the marking scheme would be shown to students** (`scheme-lookalike`)
> "# Mark answers" looks like the start of the marking scheme, but it isn't one, so everything below it would appear on the student's page.
> Change the line to `# Marking scheme`.

> **Line 57 · 1(b) · students would see this** (`scheme-above-line`)
> This line looks like a marking point ("- 2 marks: …"), but it is above `# Marking scheme`.
> Move it below `# Marking scheme`, under `### 1(b)`.

> **Line 64 · 2(c) · the starter text gives the answer away** (`starter-is-answer`)
> The text already in 2(c)'s box is almost the same as its model answer.
> Delete the starter text, or change it to a prompt such as "Permitted: … Not permitted: …".

> **Line 12 · unknown box** (`unknown-kind`)
> dewmark doesn't know a box called ```` ```anwser ````. Did you mean ```` ```answer ````?

> **Line 30 · 1(a) · a box ended early** (`fence-closed-early`)
> The `choice` box that starts on line 22 was closed by the three backticks on line 30, which look like the end of a code listing inside option C.
> Open the box with four backticks (```` ```` ````) and close it with four.

> **Line 113 · 2(c) · already sat** (`renumbered-after-sitting`)
> This paper was issued for "2026-10-20 Group A", and the answers to 2(b), "Height", are stored under that number. It is now numbered 2(c).
> If that was a slip, put it back. If this is a new version of the paper, change "version: 1" to "version: 2"; the earlier sittings keep their own record.

> **Line 201 · 1(c) · the key and the options disagree** (`key-check-phrase`)
> The key says `B (range(1, 6))`, but option B reads `for n in range(5): print(n)`. Option A contains "range(1, 6)".
> Did the options move? Change the key's letter, or the options back.

> **Line 188 · 5(b) · the key contradicts itself** (`key-precision`)
> The key asks for 2 decimal places, but 0.5 is written with 1.
> Write it as 0.50.

> **Line 176 · 3(a) · marking points that aren't read as points** (`guidance-looks-like-points`, a warning)
> "Award 2 marks for the correct factors" is read as guidance, so the marker will type a number instead of ticking points.
> If it is a point, write it as `- 2 marks: the correct factors`.

> **Line 4 · a setting dewmark doesn't know** (`unknown-setting`)
> `timer: hidden` isn't one of the choices. `timer` can be `none`, `shown` or `enforced`. The student can always hide the timer themselves.

---

## 8. The teacher's cheat sheet

````
THE DEWMARK EXAM FILE ON ONE PAGE
Write the paper as it would be printed. Write the marking scheme underneath it.

1  SETTINGS go at the very top, between two lines of three dashes.
   ---
   code: bio-5n2746-jan-2027       never change this once students have sat it
   kind: exam                      or practice, or sample
   title: January Examination
   module: Biology
   module code: 5N2746
   total marks: 100
   time allowed: 2 hours
   timer: shown                    or none, or enforced
   hand in: Upload your PDF and answer file to "Biology exam" on Moodle.
   ---

2  THE FRONT PAGE is anything before the first question: the instructions.

3  NUMBERS AND MARKS GO IN HEADINGS. A heading with marks is a question or a part.
   # Section B: Answer any two questions (40 marks)   optional; "any two" is understood
   ## Question 3: Enzymes (20 marks)
   ### 3(a): Reading the graph (5 marks)               or ### (a) ...
   #### (i) The optimum (2 marks)                      only if a sub-part has its own marks
   Parts must add up to their question, questions to the total. dewmark checks.

4  AN ANSWER BOX is a fence under its part: three backticks and one word.
   ```answer      a written answer (anything inside is what the box starts with)
   ```maths       written maths, with a preview and symbols
   ```essay (about 800 words)
   ```boxes       one box per line; ____ shows where the box goes;
                  a last line "Choose from: a / b / c" makes drop-downs
   ```blanks      sentences with ____ gaps, or [a / b / c] to choose from
   ```table       a table with ____ in the cells to fill
   ```choice      options A. B. C. D.    add (choose 2) for more than one
   ```match       1. 2. 3. to be matched with A. B. C. D.
   ```order       A. B. C. to put in order
   ```photo       a photograph of handwritten work
   ```on-paper    answered on paper; you type the mark in later
   ```python exec code the student writes and runs (inside: the starting code)
   ```code        code or pseudocode the student writes but cannot run
   End every box with three backticks on a line of their own.
   Two boxes in one part? Label them:   ```python exec 4(b): your tests
   A box with no marks (rough work, a plan): add (not marked).

5  THINGS STUDENTS READ BUT CANNOT CHANGE
   ```python   ```sql   ```text   ```pseudo     code with line numbers
   ![say what the picture shows](pictures/cell.svg)     $x^2 - 4$ for maths
   A table or picture right under a question heading stays in view for all its parts.
   ```material Figure 2    for something only the later parts use

6  THE MARKING SCHEME comes after the paper, under one line:
   # Marking scheme
   ### 3(a)                          the part's number, as printed
   Answer: B                         a letter, a word, a phrase
   Answer: 4.88 ± 0.01 m             a number, how close counts, the unit
   Answers:                          one per box or gap, in order
   1. cell wall
   2. vacuole / large vacuole        " / " separates accepted answers
   Model answer: ...                 or a ```python block
   - 2 marks: a point to tick        the part's marks are the limit
   - **Argument** (15 marks)         a criteria grid, bands indented under it
     - 13 to 15: ...
   Anything else is guidance for the marker.
   Put (draft) after a heading you have not checked; an exam can't be issued until you remove it.

PRESS CHECK. Every problem has a line number and a fix.
AFTER STUDENTS HAVE SAT A PAPER, DO NOT RENUMBER IT. For next year, change version: 1 to version: 2.
````

---

## 9. Migration

| Source | Route | Effort | Notes |
|---|---|---|---|
| The four PDP papers | Script: `pdp2paperfirst.py` plus the three code-fence changes | Converter half a day; per paper 15 minutes checking the preview; one to two hours writing each scheme | Sample, Practice 1 and 2 have the same shape; the 2027 paper also needs its three HTML maths spans turned into `$…$` and its inline SVG flowchart saved as `pictures/…-figure-1.svg` with a description. Instruction 4 reworded by hand in each. |
| dewmark's five samples (`/home/user/dewlab/dewmark/samples/`) | Script reading the YAML blocks with `build_exam.py`'s own parser | About 250 lines; a day to write, a day to review, mostly the maths sample's 70 boxes | Question blocks become headings with marks; `prompt` becomes prose; each `type` becomes a kind; `{word}` gaps become `____` with the word moved to `Answers:`; `correct: 3` becomes a letter; marking blocks move below the line; `choose: 2` goes into the section heading; `setup_code` becomes ```` ```python setup ````. Headings must be placed by position, because today's parser attaches each to the previous question (`code.md` §1). None has been sat, so names may change. |
| `pdp-exam/1` submissions | Workbench importer | Small | `exam_id` plus `label` map to the new names. |
| dewlab tutorial `question` fences | Import form (§4.11) | None for practice papers | Exam papers use Move answers to the marking scheme. |
| Old dewmark files (no `dewmark:` line) | Refused with the offer **Upgrade this file** | The samples converter, reused | Shown as a before-and-after diff to accept. |

The two recreated real papers in `experiments/` (decision 3) convert with the samples converter and stay public as samples.

---

## 10. What ships first, and what waits

**First, before any sitting**, because the format must be frozen before a paper is sat: the whole grammar written down, including kinds whose renderers come later (an unknown kind is refused, so adding a renderer never changes the format); the reader with settings, headings, sums, names, notes and the lock; the four secrecy layers; the kinds the PDP papers and samples use (`answer`, `python exec`, `boxes`, `essay`, `choice`, `blanks`, `table`, `code`, listings, `python setup`, `material`, with `maths` shown as plain text until its preview exists); the marker's half (keys as text and as numbers with tolerance, model answers, points, criteria, guidance, `(draft)`); `timer` and `breaks`; the PDP converter; the messages in §7; the cheat sheet and specimen as the paste-route package.

**Second:** `match`, `order`, `photo`, `on-paper` and `Choose from:` banks; the maths preview, palette and MathLive; `tests` in the workbench and practice pages; `show answers`; the check phrase on choice keys; the dewlab import form; the samples converter; the registry-generated JSON schema for a connected model.

**Later:** a companion scheme file; a `(was 2(b))` note so a question can be followed across versions; the maths expression form check; rubric tables pasted from Word; paper variants.

---

## Decisions for Josh

Each decision lists its options; the first is the recommendation.

1. **Which format.** (a) Paper-first as the base, with the grafts in §3 (recommended: best for writing, reading and converting, with its weaknesses fixed in the builder); (b) typed blocks (strongest checks, hardest to write by hand); (c) one fence family (closest to dewlab, with silent-mistake paths in gaps and headings).
2. **Where the scheme lives.** (a) At the end of the same file under `# Marking scheme` (recommended: one split keeps secrets structural, and it matches a Word paper and scheme); (b) beside each box, as a `mark` fence; (c) a companion file.
3. **Names.** (a) The printed number, locked at first publication, including practice papers (recommended: the number is what everyone quotes, and a model invents nothing); (b) a written name for every box, with numbers generated.
4. **What ```` ```python ```` means.** (a) dewlab's meaning: a listing, with ```` ```python exec ```` for a student's cell (recommended: what every Markdown reader and model expects; one family with dewlab; hostile case 1); (b) PDP's meaning: a cell, with ```` ```text ```` for listings.
5. **Gaps.** (a) `____` and `[a / b / c]`, keys in the scheme; dewlab's `{word}` accepted only as an import form in practice papers (recommended: no braces to collide with maths sets, and nothing secret beside the question); (b) `{word}` everywhere, split out by the builder.
6. **Keys.** (a) Text by default; a number comparison only with a tolerance, range or precision, and `± 0` for exact (recommended: `0123`, `1.10` and `No` all stay as written); (b) any key that starts with a digit is a number.
7. **When practice tests run.** (a) After the student finishes, matching decision 14 (recommended); (b) while working, which decision 16 allows but which gives question-by-question feedback.
8. **Set-up code.** (a) Shown to students, collapsed (recommended: the HVIT paper's instructions already describe it); (b) hidden.
9. **Check phrase on choice keys**, `Answer: B (range(1, 6))`. (a) Offered, optional, second wave (recommended: it catches the one mistake a key kept apart from its options invites); (b) not offered.
10. **The dewlab import form.** (a) Accepted in practice and sample papers, converted for exams, second wave (recommended); (b) not accepted; tutorial questions are retyped.
