# dewmark: the design proposal

*28 September 2026. This joins the design round's work into one plan: the unified exam format, the architecture and teacher's journey, the student's journey, the question types, and the assistant, all read against Josh's twenty decisions of 27 September (`planning/DECISIONS_2026-09-27.md`). Where a design and a decision differed, the decision won. Written in parallel, the designs contradicted each other or Josh's decisions in fifty-six places; each, and how it was settled, is recorded in [`synthesis-notes.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/design/synthesis-notes.md). Sections 1 and 2 are the part to read first.*

---

## 1. What this proposes

**dewmark becomes its own repository first, and nothing else changes in that move.** The rehearsed extraction carries dewmark's eight commits and forty files out of dewlab with their history, under dewlab's licence; dewlab's old `/dewmark/` address redirects to dewmark's home page. Before anything new is built, the two bugs that lose students' answers are fixed: reloading the start screen wipes saved work, and practice and exam papers share one save slot (`code.md` §2).

**Then the exam file is frozen.** A teacher writes one plain text file that reads like the printed paper: headings carry the numbers and the marks (`### 2(a): Height (6 marks)`), a short fenced block under a part is its answer box (```` ```answer ````, ```` ```choice ````, ```` ```python exec ````), and the marking scheme sits underneath one dividing line, `# Marking scheme`. The number printed beside an answer is its permanent name (`2(a)` is stored as `q2a`), and a *names lock* written at first issue stops a paper being renumbered after students have sat it. The builder refuses anything that could put the scheme in front of students, a misspelt dividing line included. The specification is [`docs/EXAM_FORMAT.md`](../docs/EXAM_FORMAT.md), with a one-page cheat sheet in its §8.

**One builder, two front doors.** The Python builder runs on the command line for Josh and CI, and unchanged inside a web page for teachers. Tested: today's builder gave byte-identical output in the browser for all five samples, in under a fifth of a second each, from a double-clicked page with the network off (`architecture.md` §0). The first teacher-facing piece is a small **checker page**: open or paste an exam file, read the problems in plain words, see the paper as students will. It carries the **paste route** Josh asked to ship now: a package (a specimen paper, the format guide, the teacher's paper, no student data) for whatever assistant the college allows, and a check of the reply. The full **studio** grows from that page.

**The student's page works in a room with no internet.** Python travels inside the exam file (about 16 MB; ready in under three seconds with the network off, `architecture.md` §0), or from the internet when the teacher chooses. The student sees one start screen (two, if D5(a)) with name, number, reading settings and a checklist of what is loading; the paper, with a save indicator that reports only finished saves; and a finish sheet that saves an answer file and a PDF, checks them, and shows a receipt code the invigilator and teacher both see.

**Marking is assisted, never automatic.** Rules the teacher wrote (a key, a tolerance, a code test) propose a mark on closed questions and give evidence on the rest; a person confirms every mark, and the record says how each mark was made. The workbench exports graded papers and a marks spreadsheet with QQI's columns.

**Thirteen kinds of answer box cover programming, maths and biology**: written answers, code cells, matching, ordering, labelled boxes with a word bank, tables, maths in three input routes, photographs, paper sheets. Each kind is one folder in a registry, so a new kind never changes the file format.

**The assistant is optional.** With a model on the teacher's computer, a college box or an approved cloud service, dewmark calls the widely used OpenAI "Chat Completions" API (Ollama's own when it finds Ollama), asking for replies in a fixed JSON shape it can check. It checks papers, converts Word papers in Josh's five modes, drafts schemes marked `(draft)`, and words feedback notes. It never suggests a mark; the student's page never calls it.

**The order**, each step shippable on its own (§9): 1 the move; 2 stop losing answers; 3 the format, the reader and the checker page with the paste route; 4 the exam page for written papers; 5 Python in the room; 6 the workbench; 7 the studio; 8 biology and maths kinds; 9 the connected assistant; then what use asks for.

**What I need from Josh:** nine decisions (§2). D1 and D2 block step 3; D3 to D5 block step 4; D6 sets the order. The rest can wait for their step.

---

## 2. Decisions for Josh

Each decision gives the question, the options, a recommendation, and what follows. Steps refer to §9.

### D1. Adopt the unified exam format as written (blocks step 3)

**Decided 28 September: yes, paper-first and strict.**

**Question.** Should `format.md` become the format dewmark freezes before any paper is sat?

**Options and recommendation.** The format's own ten choices, with the recommendation first in each:

| # | Choice | Recommended | The alternative |
|---|---|---|---|
| 1 | Base | Paper-first: headings with numbers and marks, one word per box, with strict checks grafted on | Typed YAML blocks (strictest, hardest to write by hand); one fence family with dewlab (silent mistakes with gaps and headings) |
| 2 | Where the scheme lives | At the end of the same file, under `# Marking scheme` | Beside each box; a companion file |
| 3 | Names | The printed number, locked at first issue, practice papers included | A written name for every box |
| 4 | What ```` ```python ```` means | A listing students read; ```` ```python exec ```` is a cell they run (dewlab's meaning) | PDP's meaning, where ```` ```python ```` is a cell |
| 5 | Gaps | `____` to type, `[a / b / c]` to choose; keys in the scheme | dewlab's `{word}` everywhere |
| 6 | Keys | Text unless they carry a tolerance (`4.88 ± 0.01 m`) | Anything starting with a digit is a number, so `0123` matches `123` |
| 7 | Set-up code | Shown to students, collapsed | Hidden |
| 8 | Check phrase on a choice key, `Answer: B (range(1, 6))` | Offered, optional, second wave | Not offered |
| 9 | dewlab's `question` fence | Read as an import form in practice papers; converted for exams | Not accepted |
| 10 | When practice tests run | See D7 | |

**What follows.** Yes means step 3 builds a new reader in pure Python rather than extending today's YAML parser; the PDP papers convert by script (the Sample's paper half changes in 61 of 271 lines, `format.md` §6), and the five samples by a second script, since none has been sat. Typed blocks would keep today's parser but ask teachers to learn YAML's quoting rules, whose errors the format judge found no teacher could act on (`format.md` §1, cases 11 and 15).

### D2. What "practice" means (blocks step 3)

**Decided 28 September: (c) both.** Every exam file also builds a practice page with `hint` blocks the exam build strips out, and Make a practice copy exists too.

**Question.** Today every exam file also builds a practice page with hints, and the studio mockup's Issue screen asks "exam, practice or sample?". The unified format instead puts `kind: exam | practice | sample` in the file, and has no hints. Which?

**Options.**
(a) **The file's `kind` decides; an exam file builds only the exam page.** To practise on an exam, **Make a practice copy** creates a new file with a new code and `kind: practice`, where hints are written as prose and answers can be shown after finishing.
(b) Keep an automatic practice build of every exam file, with a new `hint` block that exam builds strip out.
(c) Both.

**Recommendation: (a).** It is what `format.md` specifies and what `question-types.md` §7 proposes for revision copies. One file, one kind, one save slot, so bug B's confusion cannot return through a second build of the same code. Josh's PDP Sample and Practice papers are already separate files.

**What follows.** (a) drops today's `.practice.html` output and the mockup's kind question. (b) needs a new block kind, a strip rule the leak search must cover, and a second save slot per paper.

Either way, **answers in a practice page are hidden from view, not secret**: a practice page that shows answers after finishing, or runs tests, carries its keys inside the file, and anyone who opens the page source can read them. So **Make a practice copy** warns, and refuses unless the teacher confirms, when the exam it copies has been issued for a sitting that has not yet happened; and the Before-you-issue list checks that no practice page issued from a paper shares a sitting with it.

### D3. Where the PDF in every hand-in comes from (blocks step 4)

**Decided 28 September: (c).**

**Question.** Decision 10 requires a PDF with every submission. No design says how an offline page makes one.

**Options.**
(a) **The page writes the PDF itself**, with a PDF-writing library and a font carried inside the page, at the finish sheet's "Save your answer file" step and on "Save a copy now".
(b) **The browser's print dialog**, guided: "choose Save as PDF". This is what the PDP papers do.
(c) (a) by default, with (b) as a "Print or save as PDF" button for a full-fidelity copy.

**Recommendation: (c).** A student-made print is error-prone: students pick the lab printer, Chrome prints the `file:///` path on every page, and two artefacts must be matched by hand (`pdp-pages.md` §8.12). A PDF the page writes is always the same, carries the paper's fingerprint and the receipt code on every page, and is saved beside the answer file in one step. The first version gives, for each part, its printed number and heading and the answer as typed (text; code with line numbers and last output; maths as typed, or its LaTeX from the visual editor; photographs; "not attempted"). Full question wording with typeset maths stays in the `.html` answer file.

**What follows.** (a) and (c) cost a PDF library and a font covering Irish and maths characters inside every page (sizes to be measured in step 4), and by my estimate two to three weeks: code with line numbers, photographs, page breaks, and the fingerprint and receipt on every page all take work. The font cannot cover every script, so a student name or answer with a character the font lacks (Arabic, Chinese, Ukrainian) makes the page say so and offer the print button instead. Maths appears in the PDF as its plain-text "reads as" line, never as LaTeX (the typesetting code, such as `\frac{3}{4}`), which a marker in Moodle's grader could not read. (b) costs nothing and keeps the failures above. In Chrome and Edge the student chooses a folder once and both files go there; Firefox and Safari download both (decision 8).

### D4. What `timer: enforced` does (blocks step 4)

**Decided 28 September: (a).**

**Question.** Decision 11 allows an enforced timer. `student-flow.md` §6 argues that a hard lock is wrong for a student who started late or lost ten minutes to a crash, and its extra time is declared by the student, which only works when nothing is enforced.

**Options.**
(a) **At time up, the page saves, the answer boxes become read-only, and the finish sheet opens. The invigilator can add time or reopen with a short code printed on the sitting card.** Extra time under an enforced timer is entered with the same code. A break (when `breaks: on`) covers the paper, pauses the clock and records its start and end.
(b) A hard lock with no override.
(c) Enforced, but with extra time declared by the student.

**Recommendation: (a).** It gives the teacher a real deadline and the invigilator the remedy a paper exam already has. The code guards against accidents and casual attempts, not against a student with developer tools; the invigilator covers that. Under `timer: shown`, `student-flow.md` §6 stands: the student declares extra time, the answer file records it, the invigilator checks it.

Under `enforced`, the time the student began is kept per paper and student number, outside the saved record, so **Start again** does not restart the clock; and Start again, like resuming work saved under a different name, needs the invigilator's code.

**What follows.** (a) adds a code to each issue and one row to the sitting card. (b) will lock out a student the college has given extra time unless the teacher builds a separate paper for them. (c) makes "enforced" meaningless.

### D5. What shares the combined start screen (blocks step 4)

**Decided 28 September: (a), two screens.**

**Question.** Decision 9 puts name, number and reading settings on one screen. Josh's own words also put the loading screen there. Should the candidate instructions, the choice of where the answer file goes, extra time and Begin join it?

**Options.**
(a) **Two screens before the paper.** *Start*: details, reading settings with a live preview, and the "what this paper needs" checklist beside them; saved work is offered inline once the number is typed. *Before you begin*: the candidate instructions, the answer folder, time and extra time, and Begin, with the questions still hidden, as a printed paper stays face down.
(b) Everything, Begin included, on one screen.

**Recommendation: (a).** Python loads while the student reads, so the checklist belongs where the student starts; Begin belongs under the instructions the invigilator asks them to read. At 32 px text on a narrow screen, (b) is one long scroll with Begin far from its instructions.

*Start* carries only the four settings most students need (font, text size, colours, reading ruler); the rest sit under **More settings** and in the **Aa** drawer on every screen, because the mockup's full settings run to about 2,260 px at desktop and far more at large text. Note that (a) adds a second screen to decision 9's "one combined screen", so this is a choice to make knowingly.

**What follows.** (a) replaces the mockup's three steps with two. (b) saves one press of Next.

### D6. The order of steps 3 to 9, and the first paper to be sat (sets the plan)

**Decided 28 September: (a), with a PDP practice paper sat in class first.**

**Question.** The designs proposed four orders: the studio before Python in the room (`architecture.md` §7), the start screens with the data-loss fixes (`student-flow.md` §12), the registry refactor first (`question-types.md` §10), the assistant after the studio (`assistant.md` §8).

**Options.**
(a) **The order in §9**: format and checker page, then the exam page, Python in the room, the workbench, and only then the full studio.
(b) The studio straight after the format, before Python in the room.

**Recommendation: (a).** Josh's next papers are programming papers, which need Python in the room and a workbench that reads the new answer files, and no other teacher can use dewmark before the student page and workbench exist. The checker page puts the builder in teachers' hands at step 3 anyway. And since every hand-in includes a PDF, a practice sitting after step 5 can be marked from the PDFs if the workbench is not ready.

**What follows.** (a) delays the full studio by two steps. (b) delays the first dewmark sitting by one. **Josh, please also say which paper you want dewmark to carry first, and when**: I recommend a PDP practice paper sat in class, and a counted exam only after one clean practice sitting.

### D7. When practice tests run (step 8)

**Decided 28 September: (a).**

**Question.** Decision 16 lets hidden code tests run in practice pages "so students see which pass"; decision 14 shows practice answers only after the whole paper is finished.

**Options.** (a) **`practice tests: after finishing` by default, with `while working` available per paper**; (b) after finishing only; (c) while working only.

**Recommendation: (a).** After finishing matches decision 14's principle that practice rehearses the exam. `while working` suits a practice paper meant as a set of exercises, and the teacher chooses it knowingly.

### D8. Where a photograph comes from in an exam room (step 8)

**Decided 28 September: (a).**

**Question.** Decision 15 offers photographs of handwritten working. Phones are normally banned in exams, and Safe Exam Browser turns uploads off (`question-types.md` §4.1).

**Options.** (a) **In exams, only from college equipment**: a webcam on the PC, captured by the page, or a picture file from a college tablet or scanner; students' phones only for practice. (b) Students' phones, in exams too. (c) Photographs for practice only.

**Recommendation: (a)**, shipped first for practice papers, with the room check reporting each PC's camera, and exam use after a rehearsal. Photographs are shrunk so answer files stay small. Where PCs have no camera, the teacher uses `on-paper`. (b) raises integrity and data-protection questions for the college.

### D9. Whether a cloud endpoint may receive student text (step 9)

**Decided 28 September: (c), and permanently: cloud endpoints never receive student text, even after the DPO has answered.**

**Question.** Decision 18 allows local and approved cloud endpoints, at the teacher's responsibility. Two workbench tasks involve student-related text: wording the marker's feedback notes, and (later) comparing two answers that received different marks.

**Options.**
(a) Any configured endpoint runs every task.
(b) Cloud endpoints run the studio tasks, which hold no student data, freely; a workbench task sends student-related text to a cloud endpoint only for a service the college has approved for student data, recorded in a settings file set by the college or its IT staff, not by a per-teacher tick.
(c) **Cloud endpoints never receive student text; studio tasks, which hold no student data, may use them freely.**

**Recommendation: (c) now, (b) once the data protection officer has answered.** Decision 18 makes the choice of service the teacher's; it does not move the ETB's duties under GDPR. The ETB is the controller of student data, and only the controller can bring in an outside processor, which needs a signed processing agreement and often a risk assessment first. A teacher's tick creates neither. When the DPO has answered the seven questions in `assistant.md` §6.2, (b) becomes available for the services the college names.

### Also assumed: confirmed 28 September

These are recommendations the proposal builds on that you have not decided: dewmark **copies** what it takes from dewlab, with a record of the source commit, rather than linking to it (§3.3); **Issue** asks the teacher to confirm "I have sat this paper myself" (§4, stage 6); and the assistant speaks the **OpenAI Chat Completions** format, switching to Ollama's own when it finds Ollama (§8.2). The last is the direct answer to your question about which API to call.

### Things only Josh can find out

These are not decisions, but steps wait on them.

1. **The new programming exams you offered.** Please send them. They become test papers for the converter and the paste route, kept in the private `dewmark-papers` repository unless you clear them (step 3).
2. **The college's results template**: the column order the QA office expects, and its wording below 50% (step 6).
3. **The room PCs**: the Chrome and Edge versions (137 or later gives `input()` as a line in the output; older falls back to a pop-up), and whether they have webcams (steps 5 and 8).
4. **Moodle**: that PDF submissions open in the assignment grader, and whether `.html` uploads are accepted at all; if not, the data file travels as `.json` (step 4).
5. **The exams officer**: whether a paper not yet sat may be pasted into the college's approved assistant. The paste route's notice depends on the answer (step 3).
6. **The data protection officer**: the seven questions in `assistant.md` §6.2, before any workbench task sends text to a model (step 9).
7. **Moodle's largest upload.** A Python paper with Python inside is 16 to 17 MB; many Moodle sites cap uploads at 20 MB or less (step 5).
8. **Python in a folder beside the page** cannot travel through Moodle as one file: it needs a zip, and a page opened from inside a zip cannot load its neighbours. If Moodle is the route, papers carry Python inside the file or load it from the internet (step 5).
9. **The college's managed Chrome and Edge**: whether they allow pages opened from disk to save into a folder the student chooses. `room-check.html` should reach the PCs by the same route as the paper, downloaded from Moodle, so the room check tests the real route (step 4).
10. **The approved assistant's limits**: how much text it accepts in one paste, measured against a real package at step 3.

---

### What the review left open

An adversarial review of this proposal is in [`critique.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/design/critique.md). Its two blockers and most of its should-fix findings are folded in above. Still open: the steps in §9 carry no sizes yet (S13), so D6's "when" cannot be answered precisely; the student mockup's top bar breaks at 32 px text (S7); sections 1 and 2 run longer than ten minutes and use some terms unexplained (S17); and the mockups lag the decisions in small ways (the review's minor list).

---

## 3. dewmark after the move

### 3.1 The move

The procedure is `extraction.md`'s rehearsal as set out in `architecture.md` §1.2: tag dewlab, extract `dewmark/` with `git filter-repo` so its eight commits keep their history (pull-request numbers rewritten to point at dewlab), merge with a merge commit, fix about twelve `dewmark/`-prefixed command lines in one follow-up commit, add the root files, turn on Pages, then remove dewmark from dewlab in one pull request. dewlab keeps a redirect at `deweydex.github.io/dewlab/dewmark/` to dewmark's home page (decision 4), one sentence in its README, and its log entry 7.179 as history. The move carries no behaviour changes: the eighteen tests and five sample builds pass unchanged (`extraction.md` §3).

Decisions 1 to 4 have cleared everything the move needed. Two details this synthesis adds, both now done: the research cleanup of decision 2 keeps the research in history at commit `b3823f91799f`, which the appendix links to (a tag, `design-round-2026-09`, can be added there from any clone with push rights); and `format.md` moved to `docs/EXAM_FORMAT.md`, the stable home of the format.

### 3.2 The repository

After the move and the first builder steps:

```
LICENSE.md  THIRD_PARTY_NOTICES.md  README.md  CLAUDE.md  CONTRIBUTING.md  DECISIONS_LOG.md
pins.json                 Pyodide version and every package with its checksum, in one place
build_exam.py             a three-line shim, so `python build_exam.py paper.exam.md` keeps working
dewmark/                  the builder as a Python package
  core.py                 build(files, text, options) -> pages, scheme, names, problems; never touches a disk
  reader.py  check.py  render.py  lock.py  cli.py
  types/<kind>/           one folder per answer-box kind (§7.3)
  assist/                 assistant tasks, schemas and validators (§8)
runtime/                  the exam page: engine.js, page.js, page.css, pdf.js, exam_tools.py
checker/  studio/         the teacher's builder pages (the checker grows into the studio)
workbench/                marking
shared/                   visual tokens, the Python worker, assistant-client.js
vendor/dewlab/            files copied from dewlab, with SOURCE.json
vendor-src/               editor bundle sources
tools/                    sync_from_dewlab.py, fetch_python.py, make_download.py, convert_pdp.py, convert_v0.py
docs/                     EXAM_FORMAT.md, FOR_TEACHERS.md, AI_ACT_ASSESSMENT.md
planning/                 PROPOSAL.md, mockups/, the rewritten planning documents (§10)
samples/  experiments/pdp-5n2927/  tests/  dev/
.github/workflows/        tests.yml, deploy.yml
```

CI runs `architecture.md` §1.6's six jobs (unit tests; samples built twice with identical output; the same builds inside Pyodide, byte-identical to the command line; vendored copies against their checksums; browser rehearsals with the network blocked; a privacy job refusing `private/`, `dewmark_*` files and any `.exam.md` outside `samples/` and `experiments/`), plus `format.md` §4.5's **mutation test**: every scheme string replaced with nonsense must leave the student page byte-identical. Pages serves the home page, the checker (later the studio), the workbench, the samples, the PDP experiments, a downloadable folder for double-click use, and each release under `/dewmark/v/<version>/`.

### 3.3 What dewmark shares with dewlab, and how

**Code is copied, never linked.** An exam page must not depend on dewlab when it runs, and dewlab changes weekly (eight engine commits in fifteen days). Verbatim copies live under `vendor/dewlab/` with a checksum each in `SOURCE.json`, and CI fails on a hand edit. Files rewritten for exams carry a banner naming their source and commit. A monthly report lists upstream changes; taking one is a person's reviewed decision, logged in `DECISIONS_LOG.md` (`architecture.md` §2). The files, in the order the steps need them:

| From dewlab | Kind | For |
|---|---|---|
| `dev/fetch_pyodide.py` | copy, extended | downloading the pinned Python and packing it into or beside a page (step 5) |
| `compose/dewmini-fs.js` | port | remembering folders; reconnecting the answer folder after a reload (steps 4, 7) |
| `vendor-src/codemirror-entry.js` | copy | the code editor in the page and the studio (steps 5, 7) |
| `assets/vendor/accessible-fonts.css`, Lexend, OpenDyslexic | copy | reading settings (step 4) |
| `assets/tutorial-style.css` lines 1–165 | port | one visual system across the three pages (step 4) |
| `assets/pyodide-engine.js`, `pyodide-worker.js` | port | the exam engine: `input()`, Stop, time limit (step 5) |
| `assets/tutorial_tools.py`: output rendering, error formatting, `compare()` | port | code output and the test runner (steps 5, 6) |

**The format is shared by meaning.** In both projects ```` ```python ```` is a listing, ```` ```python exec ```` a cell the student runs, ```` ```python setup ```` set-up code, and `$…$` maths typeset at build time. dewlab's `question` fence is read as an import form in dewmark's practice papers (`format.md` §4.11). Traffic can run the other way: dewmark's engine and in-page Python would give dewlab's downloaded tutorials the Stop and `input()` they lack (dewlab 7.77, 7.240).

---

## 4. The teacher's journey

The mockup is [`mockups/teacher-studio.html`](mockups/teacher-studio.html); it opens from disk. It predates the format and the decisions, so four things in it are out of date: its editor shows the old YAML blocks; its Issue screen asks for the paper's kind and Python delivery, which now live in the file (`kind`, `python from`) and are only shown there; its preview has a "Practice" tab with hints, which D2 removes; and it offers Word conversion only through a model, where the paste route now ships first.

**Where papers live.** On the teacher's own college storage (OneDrive, a network home drive), one **paper folder** per paper; Josh's sources also go in a private `dewmark-papers` repository; submissions never go on GitHub (decision 6). The folder, with one change from `architecture.md` §3.1, splitting what students receive from what they must never see:

```
PDP 5N2927 Sample/
  pdp-5n2927-sample.exam.md            the only file the teacher writes
  pictures/  data/
  names.lock.json                      written at first issue
  issued/2026-10-20 Group A/
    for-students/                      the exam page, python/ if needed, room-check.html
    for-teachers/                      answer key, marking-scheme.json, sitting-card.html
  submissions/2026-10-20 Group A/      personal data
  marking/2026-10-20 Group A/          marking record and exports, kept apart from submissions
```

**The journey**, in twelve stages:

1. **Open dewmark** from its web address or a downloaded folder: Continue, New paper, Open a paper, Convert a paper, Mark submissions. One line says "This page came from the internet; your papers never go back to it", and the page's security policy enforces it.
2. **Write** from a template (Python practical, maths, science, essay, blank), with an **Insert** menu holding one snippet per answer-box kind and a running marks tally.
3. **Convert.** A PDP page converts exactly, by script; a Word or PDF paper through the assistant or the paste route (§8.5). What a converter cannot know arrives as `(draft)`.
4. **Check.** About 400 ms after typing stops, the builder runs in a background worker; every problem has a line, what is wrong and what to do (`format.md` §7).
5. **Sit it.** The real page opens full-window, apart from real students' storage; one click opens the attempt in the workbench to test the scheme.
6. **Issue.** A **Before you issue** list gates the button: checks pass, no `(draft)` left, every picture described, no locked name changed, and "I have sat this paper myself". Issue asks only for the sitting's name, and writes the issued folder, the names lock (also copied into the scheme JSON and the student page, so a paper moved or emailed without its lock file is still checked) and the **fingerprint** (a short code such as `7KQ-4MD` identifying exactly this paper).
7. **Prepare the room.** `room-check.html`, opened on each PC beforehand, reports in about thirty seconds on the browser, Python with the network off, `input()`, Stop, saving, storage, the camera if needed, and screen size.
8. **Give it out.** On Moodle as a file resource set to "Force download", never as a page shown inside Moodle; or on a shared drive or USB, copying `for-students/` only.
9. **Collect** Moodle's "Download all submissions" zip or a folder. The workbench logs each file received with its checksum, receipt and fingerprint: QQI's record of evidence received.
10. **Mark** in the workbench (`architecture.md` §3.6, `question-types.md` §2.5; see §4.1).
11. **Export** graded papers, `marks.xlsx` and the QQI results columns.
12. **Archive**: one file for each sitting, holding a checksum manifest and a delete-after date.

The checker page of step 3 in §9 is stages 2 to 4 alone, with a Markdown text box instead of the editor; the studio of step 7 adds the rest.

One burden stays with maths teachers until then: maths in a question is written as LaTeX between dollar signs (`$x^2 + 3x$`), which a teacher who has never met LaTeX must learn. The studio should gain a maths insert with a live preview (MathLive is already a step 8 dependency) in step 7 or 8.

### 4.1 Marking: not yet designed

No design in this round covers the marking screens: marking by question or by student, blind marking, keyboard entry, a second marker, and how propose-and-evidence looks on screen. `architecture.md` §3.6 names them as the workbench's own design, which does not yet exist. That design, with a mockup, is the first deliverable of step 6, before any of its code.

---

## 5. The student's journey and branding

The mockup is [`mockups/student-start.html`](mockups/student-start.html); its **Try a scenario** menu shows returning work, slow and failed loading, a browser that cannot save to a folder, and a full browser store. It predates decisions 9 to 11: it has three steps where the design now has two (D5), loads Python "from the room computer" where the file now carries it, has no PDF and no break control, and offers a practice copy "of the same paper", which D2 replaces.

### 5.1 The screens

**Start.** The front of the paper under a band reading EXAMINATION (solid) or PRACTICE PAPER (striped: a different word, pattern and colour, so the difference never rests on colour alone). Name and number, and beside them the reading settings from `student-flow.md` §4.2: four fonts including Lexend and OpenDyslexic carried inside the page, text size from 14 to 32 px, spacing, line length, six colour schemes, a reading ruler, reduced motion, and code-editor options when the paper has code. The screen restyles as the student chooses, with a preview from this paper. Beside them, **What this paper needs** lists the paper, fonts, Python and its packages, data files, set-up code, a Python self-test and browser saving, each with a word and an icon (Waiting, Loading with megabytes, Ready, Failed, Not needed). Python starts loading when the page opens, and "Ready" follows a test. When the student types a number with saved work on this computer, the page says so there, and only to that number; **Start again** sets old work aside, never deletes it.

**Before you begin.** The candidate instructions from the file's front page; where the answer file goes (a folder the student chooses, where the browser allows); the time, with extra time as D4 settles; Begin. The questions stay hidden until Begin.

**The paper.** A slim top bar (code, kind badge, name, time, save indicator, **Aa** for settings, Reference, Calculator, Finish), a side panel with progress per question in words, and the answer boxes. The **save indicator** shows a time only when a write finished at that time, and says plainly when a save route failed, offering **Save a copy now**. Output is stored apart from answers and capped, so a runaway `print` loop cannot stop answers saving. Code runs in a background worker, with `input()` as a line in the output, Stop, and a time limit that `except Exception` cannot swallow (`student-flow.md` §7).

**Finish** is three steps. *Check your answers*: empty spaces and code changed since it last ran, by the paper's own numbers. *Save your answer file*: the page writes the `.html` answer file and the PDF, reads the file back and confirms "Checked: the file holds 17 answers. Receipt 7F3A 92C1." *Hand it in*: the paper's own `hand in` wording. A confirmation card for the invigilator shows name, number, paper and fingerprint, answer count, save time and receipt; the workbench shows the same receipt. A change after finishing asks the student to save and hand in again.

### 5.2 Saving without mixing students or papers

Browser storage for every double-clicked page is shared across a browser profile, so one college PC may hold several students' work. Keys are `dewmark:1:<paper code>:<variant>:<student number>`, looked up only when the student types their number, and nothing is written before Begin or Continue. The record inside carries the paper's version, fingerprint and sitting: the same version is restored (the names lock guarantees its names), with a note if the paper was corrected since; another version or sitting is set aside for the invigilator, not restored. A second window on the same work turns read-only and never writes. **I have an answer file** on the start screen moves a student to another computer. A small **Saved work on this computer (for invigilators)** link lists this paper's saved sittings, masked, with when each expires. Student numbers are printed on cards, so resuming work saved under a different name needs the invigilator's code; and nothing stays on a shared PC longer than needed: a record is deleted once its answer file has been saved and read back, or after 14 days, checked each time a dewmark page opens. (Synthesis notes B28.)

### 5.3 Timer and breaks

`timer: none | shown | enforced` and `breaks: on | off` are the teacher's (decision 11); the student can always hide the time. "Time left" is Begin plus the time allowed plus extra time. At ten minutes left, words, an icon and weight change, announced once, with no sound and nothing that takes focus. Under `shown`, nothing locks at zero. Under `enforced`, D4 applies. A break covers the paper, pauses the clock and records its start and end in the answer file with any extra time, which the workbench shows in an accommodations column. Reading settings are never recorded, since a font choice can reveal a disability.

### 5.4 Practice and exam

A practice or sample paper has the same screens, with the band, a striped top-bar badge, and each finish step introduced with "In the real exam, you will…". With `show answers: after finishing`, once the student finishes the whole paper each closed question shows the paper's answer beside the student's, with no tick, cross or score (dewlab's manner since its 7.235), and written parts show the model answer. With `practice tests` on, code tests run in the page as D7 settles. Keys, model answers and tests are refused in any `kind: exam` build.

### 5.5 Branding

The keys are text: `institution`, `college`, `module`, `module code`, `title`, `session`, plus an optional `logo` (SVG, PNG, JPEG or WebP; warned above 30 KB, refused above 150 KB; stripped of scripts and shown only as an image). dewmark owns the colours and fonts, so every theme keeps its checked contrast and the band means the same in every college (decision 12). The logo is decoration, since the names are always written beside it. Where each appears:

| | Start screen | Top bar | Masthead (scrolls away) | Print and PDF | Answer file | Tab title |
|---|---|---|---|---|---|---|
| Band | large | badge | yes | footer | yes | |
| Logo | up to 48 px | | 28 px | page 1 | yes | |
| Institution, college, session | yes | | yes | header: college | yes | |
| Module and code, title | yes | code only | yes | header | yes | code and title |
| Time, marks, weighting | yes | time left | yes | | yes | |
| Name and number | typed | name | | footer, every page | yes, and the file name | name, after Begin |

---

## 6. The exam file

A summary; the specification, worked examples for all three subjects, the converted PDP Sample, the builder's messages and the cheat sheet are in [`docs/EXAM_FORMAT.md`](../docs/EXAM_FORMAT.md).

**Layers.** Settings between two lines of dashes; the front page (instructions); sections, questions and parts as headings; optional reference cards (a formula sheet); and the marking scheme under `# Marking scheme`. The student page is built from the first four; the fifth is split off before anything is rendered.

**Headings carry numbers and marks.** `# Section B: Answer any two of Questions 2 to 4 (20 marks)`, `## Question 3: Enzymes (20 marks)`, `### 3(a): Reading the graph (5 marks)`. A heading without marks is text. Parts must add up to their question and questions to the total; when they do not, the builder reports the lowest level that disagrees, once.

**Answer boxes are fences** from a closed list (§7.2). An unknown word is refused with the nearest match ("Did you mean ```` ```answer ````?"), never shown as code. A part with two boxes labels them (```` ```python exec 4B (i): your tests ````); boxes under one heading share its marks, as the PDP papers mark.

**Names are printed numbers**, tidied: `1A (i)` is `q1a.i`; options by letter, match items by number, gaps and cells by position. The names lock records every name with its kind, marks, printed label and option texts; renaming, removing, retyping or re-marking a locked name after a sitting stops the build unless `version` changes.

**Secrets stay off the student page** in four layers: the structural split; refusals of lookalike headings ("# Mark answers", "# Solutions") and of scheme-shaped lines above the line, and of an exam with no scheme; a search of the whole built page, including the embedded data block today's check skips; and the mutation test in CI.

**The marker's half.** Entries are found by number. `Answer:` gives a key; keys are text, compared as numbers only with a tolerance (`4.88 ± 0.01 m`, `(2 d.p.)`); ` / ` separates accepted answers; `Model answer:` or a code block; ```` ```tests ```` for code; `- 2 marks: …` for points to tick; a bold criterion with indented bands for a grid; anything else is guidance. `(draft)` on an entry's heading lets it preview but not issue.

A small example:

````markdown
## Question 2: A ladder (10 marks)

A ladder 5.2 m long leans against a wall. Its foot is 1.8 m from the wall.

### 2(a): Height (6 marks)

How far up the wall does the ladder reach, to two decimal places?

```maths 2(a): working
```

```boxes 2(a): answer
Height = ____ m
```

# Marking scheme

### 2(a)

Answer: 4.88 ± 0.01 m

- 3 marks: Pythagoras with the ladder as the hypotenuse
- 2 marks: correct working to 4.878
- 1 mark: 4.88 with the unit
````

---

## 7. Kinds of exam and question

### 7.1 Kinds of exam

| Kind | QQI technique | In dewmark |
|---|---|---|
| Theory examination, mixed types (PDP written paper, biology) | Examination-Theory | Yes: the main case |
| Timed programming practical (the HVIT paper) | Skills Demonstration, when timed and supervised | Yes, with Python in the room |
| Timed assignment under exam conditions (the maths sample) | Assignment | Yes; the export says Assignment |
| Practice and sample papers | formative | Yes |
| A typed paper with some parts on paper sheets | any of the above | Yes, with `on-paper` |
| Learner records, projects, collections of work, lab skills, take-home work | the rest | No: Moodle and the lab |

(`question-types.md` §1.1.)

### 7.2 The answer-box kinds

| Kind | The student | Subjects | Marking help | Wave |
|---|---|---|---|---|
| `answer` | writes in a growing box, optional starter text | all | none | 1 |
| `essay` | writes with a word count | all | none; criteria grid | 1 |
| `code` | writes pseudocode, SQL or a trace, monospaced, no Run | programming | none | 1 |
| `python exec` | writes and runs Python; `input()` in the output | programming | evidence from tests | 1 |
| `boxes` | fills one box per labelled line; `Choose from:` makes drop-downs | all | evidence; propose with a bank | 1 (bank: 2) |
| `blanks` | fills `____` gaps or picks from `[a / b / c]` | all | evidence; propose for picks | 1 |
| `table` | fills cells in a table | all | evidence per cell | 1 |
| `choice` | picks one lettered option, or several with `(choose 2)` | all | propose | 1 |
| `maths` | types maths in the routes the paper allows | maths, biology | evidence with a key | 1 as text; 2 with preview, palette, visual editor |
| `match` | picks a letter beside each numbered item | biology, theory | propose | 2 |
| `order` | reorders a list with Move up and Move down | biology, theory | propose | 2 |
| `photo` | adds a photograph of handwritten work | maths, biology | none | 2 (D8) |
| `on-paper` | answers on a labelled sheet; the mark is typed in the workbench | all | none | 2 |

"Propose" means the teacher's key proposes a mark the marker confirms; "evidence" means facts ("matches the key", "differs", "could not read") and no mark; the words are never "correct" or "wrong", because an equivalent answer the rule missed must not look like a mistake (`question-types.md` §2.5). A number answer is a `maths` working box plus a `boxes` answer line; label-the-diagram is a picture plus `boxes` with `Choose from:`; predict-the-output is a listing plus `boxes` labelled by line; rough work is any box noted `(not marked)`. Shared material (a results table, a figure) sits under the question heading, or in a `material` fence for later parts only.

### 7.3 The registry

Each kind is one folder in `dewmark/types/`: a Python half (grammar, key shape, checks, markup, exports), a page half (collect, restore, answered, reveal), a workbench half (view, summary, suggest), a README that is its cheat-sheet line, an example that is the studio's Insert snippet, and sample stored answers. Generic tests run over every folder: the example builds, no secret reaches a student page, stored answers round-trip, keyboard entry and an accessibility scan pass. Stored answers are plain data and record whether the box was touched, so "not attempted" and "left blank" differ. The registry also generates the JSON schema a connected model writes to, and the Moodle exports (`question-types.md` §2; `format.md` §4.8).

### 7.4 By subject

**Programming.** Code cells with starter code, `input()` and Stop; hidden tests in the scheme in three shapes the PDP papers need (a function call, a program run with typed input, values after a run), run in the workbench on a fresh copy of Python beside the model answer's result, and in practice pages when the teacher allows (decision 16); labelled boxes for the PDP "Line 1: … Line 12:" scaffolds; pseudocode; listings with line numbers. Seven of the ten marked code spaces in the Sample and practice papers can carry tests as worded (`question-types.md` §5).

**Maths.** Three input routes (decision 15), chosen per paper with `maths input`: plain text with a typeset "reads as" line and a symbol palette (light, fast, screen-reader friendly); the visual editor MathLive (about 1.1 MB, carried only by papers that allow it, storing LaTeX); and photographs. One small maths reader, grown from the page calculator's parser, serves the calculator, the preview and the workbench, so student and marker see one meaning; it reads 18 of 26 typical final answers today, and each miss is a small addition (`question-types.md` §4.3). Numbers with tolerance, precision and units; "any N of M" sections; paper sheets for long working; expression keys with a form check later.

**Biology.** Shared tables and figures that stay beside their parts; label banks; matching and ordering with keyboard controls, never dragging alone; numbers with significant figures and units, counted from what the student typed; results tables and Punnett squares; drawings and hand-plotted graphs on paper.

**Waits:** hotspots, plotting points, Parsons problems, freehand drawing, per-student shuffling, and QTI export. GIFT and Moodle XML export come after the subject waves.

---

## 8. The assistant

### 8.1 Where it runs

Only the teacher pages (checker, studio, workbench) and the command line call a model; the student page never does, and its security policy forbids every connection except, when the paper loads Python from the internet, the one pinned Python address, with checksums. Each teacher page limits itself to the one address the teacher configured, by writing its security policy from the saved address when it opens (verified from a double-clicked page, `assistant.md` §0). Every feature works without a model.

### 8.2 The API dewmark calls

dewmark speaks the **OpenAI Chat Completions** format, which Ollama, llama.cpp's `llama-server`, vLLM, LM Studio and most cloud services accept: `GET {address}/v1/models` lists models; `POST {address}/v1/chat/completions` carries the task's instructions, the material inside tags with a one-off code, `temperature: 0`, a fixed seed, streaming for progress, and `response_format` holding a JSON Schema generated for that request. When it detects **Ollama**, it uses Ollama's own `POST /api/chat` with `"truncate": false`, because Ollama's compatible endpoint silently cut a 7,189-token paper to its last 2,050 tokens and still answered "200 OK" (`assistant.md` §0). Schemas use only features both servers enforced in testing, with per-request lists: a finding's "where" can only be one of this paper's own numbers, so a model cannot invent one. **Test connection** identifies server, model, working memory and image reading, and diagnoses the usual failures in plain words ("Ollama is running but will not talk to pages opened from a folder. Set OLLAMA_ORIGINS and restart Ollama."). The recipe sets it to dewmark's own addresses rather than `*`, which would let any website the teacher visits use the model; whether pages opened from disk can be allowed without `*` is tested in step 9. Full shapes, fallbacks, time limits and cancellation: `assistant.md` §1.

With decision 18 the address may be local, on the college network, or an approved cloud endpoint; settings and logs say which. For cloud endpoints, some services refuse requests from a web page, and a key stored in a browser is only as safe as that browser profile; both need testing per service.

### 8.3 The tasks

| Task | Where | Student data | Paste | Step |
|---|---|---|---|---|
| Check a paper: ambiguity, two questions in one, marks against demand, a key that disagrees with its question, reading level, accessibility, notation students cannot type | studio | no | yes | 9 |
| Convert a Word or PDF paper, in decision 19's modes: copy without composing; tidy the wording; check the language is accessible; make it more UDL-friendly; rephrase commands as invitations | studio | no | yes (ships at step 3) | 3 (paste), 9 (connected) |
| Draft model answers and schemes, marked `(draft)`; code answers must pass their own tests, numeric keys are recomputed | studio | no | yes | 9 |
| Word my feedback notes, from the marker's notes and the mark already given, never from the student's answer | workbench | marker's notes | no; the phrase bank from the scheme alone is pasteable | 9 |
| Check my marking, by rule: near-identical answers with different marks, marks on blank answers, ticks that disagree with the total, drift through a session | workbench | yes, but no model | n/a | 6 |
| Compare two answers that got different marks, after marking: flags only | workbench | yes (D9) | no | later |

Every mode except "copy without composing" changes only prose above `# Marking scheme`; a reply that changes a number, a mark, a fence line or the scheme is refused, and every wording change is shown line by line for the teacher to accept. Every task's findings go into the same problem list as the builder's, labelled *Assistant*, and never lock the Issue button. Every call is logged beside the paper or the marking record: task version, model and its checksum, settings, input and output checksums, and what the teacher did with each finding (`assistant.md` §3, §6).

### 8.4 What it will not do

No suggested marks or bands on any paper (decision 17), no feedback written from a student's answer, no verdicts on submitted code, no "suspicious" or "AI-written" detection, no ranking or grade prediction, and no model on the student page. No task's reply has a field for a mark, and validators drop text that looks like one. The reasons are in `assistant.md` §3.9: the EU AI Act makes a mark-suggesting system high-risk from December 2027, and the evidence on model marking shows moderate agreement with human markers and penalties for non-native phrasing (`local-llm.md` §4–5). Decision 17 asks for a separate study of how mark suggestion could be done; §9 schedules it.

The workbench's rule-based proposals (§1, "Marking is assisted") are not AI in the Act's sense: Recital 12 excludes systems whose rules are "defined solely by natural persons" (`local-llm.md` §5). A key, tolerance or test the assistant drafted becomes the teacher's rule only when its `(draft)` mark is removed. `docs/AI_ACT_ASSESSMENT.md` should say both.

### 8.5 With no model: the paste route

The checker page (and later the studio) builds one block of text for any assistant the college allows: the task's instructions, the format's cheat sheet, a specimen paper for the subject, and the teacher's paper **without its marking scheme** (the scheme is included only for "Draft model answers and schemes"), headed "This contains your exam paper. It contains no student information. Paste it only into an assistant your college allows for exam material." The teacher pastes the reply back; the same builder checks it, and **Copy these problems** hands its messages back to the assistant for another round. The studio holds no submissions, so a package cannot contain student data, and a scan for student-number patterns runs before copying. The package is offered both to copy and as a `.txt` file to attach, since some assistants limit how much can be pasted. It is decision 20's "small exercise in AI literacy": the teacher sees what was sent and what came back, and the builder has the last word.

### 8.6 Hardware

A 16 GB or 24 GB graphics card, or a Mac mini with Apple silicon: `gpt-oss:20b` on 16 GB, `qwen3.8:27b` (which reads images) on 24 GB. A shared box runs `llama-server` with a key, on the staff network only. `assistant.md` §7 is a one-page setup recipe.

---

## 9. The order of work

Each step ships on its own and ends with a test that shows it worked. Steps 1 and 2 need no decisions beyond those already made.

**Step 1. The move.** *Delivers:* §3.1; dewmark's own CI and Pages; the redirect in dewlab; `LICENSE.md` (dewlab's terms), `THIRD_PARTY_NOTICES.md`, `CLAUDE.md`, `CONTRIBUTING.md` and a `DECISIONS_LOG.md` opening with the move, the licence, sharing with dewlab, the cleared PDP papers, and the twenty decisions; then decision 2's cleanup behind a tag. *Done when* dewmark's CI is green, Pages serves the samples and the workbench, dewlab's tests pass, and the old address lands on dewmark's home page.

**Step 2. Stop losing answers.** *Done, September 2026: `DECISIONS_LOG.md` entry 0.6; the rehearsals are `tests/browser/test_saving.py`.* *Delivers,* on today's page and workbench: nothing written before Begin or Continue (bug A); the variant in the storage and window-channel keys, and an answer key that never saves (bug B); a second window that never writes; the workbench no longer reading the scheme and its own record as students (bug G, `code.md` §3). The fixes are small, today's pages are public, and the rehearsals carry over to the new page. *Done when* new browser rehearsals reproduce each bug before the fix and pass after it, and run in CI.

**Step 3. The format, the reader and the checker page.** *In progress: the reader (`dewmark/reader.py`) and the PDP converter are done, `DECISIONS_LOG.md` entry 0.7, the names lock (`dewmark/lock.py`), entry 0.8, and the paste route's package and reply check (`dewmark/package.py`, `dewmark/reply.py`), entry 0.9; the checker page (`checker/index.html`), entry 0.10, and the marker's half as JSON with the search and the mutation test (`dewmark/scheme_json.py`, `dewmark/secrecy.py`), entry 0.11. What is left of step 3 waits for step 4's renderer: running the search and the mutation test over every sample.* *Waits for* D1 and D2. *Delivers:* `docs/EXAM_FORMAT.md`; the new reader as a pure core; settings, headings, sums, names, notes and the lock; the four secrecy layers with the mutation test; the registry skeleton with the first-wave kinds' builder halves; the marker's half, written out as `dewmark-scheme/1` JSON; the builder's messages with stable codes; the PDP converter; the `builder-in-browser` CI job from the first commit (the new Markdown library in Pyodide is not yet probed; this job is the probe); and the **checker page**, with the paste route and its package, the before-and-after screen that shows each changed line to accept or reject, and the rule that refuses a reply changing a number, mark, fence line or the scheme. *Done when* the four PDP papers convert and pass apart from their `(draft)` scheme entries; `format.md`'s sixteen hostile cases are tests; and a colleague who is not a programmer converts a Word paper through the paste route to a passing file without help.

**Step 4. The exam page for written papers.** *In progress, in five slices (`DECISIONS_LOG.md` entries 0.12 to 0.18). Slice 1 is done: the renderer and builder for the new format (`dewmark/render.py`, `dewmark/build.py`; `python -m dewmark build FILE -o DIR`), with the search and the mutation test run over every page built; the page's kinds of answer box and the saves of §5.2 (`assets/page.js`), as `docs/ANSWER_FILE.md` sets out; and the step-2 rehearsals, repeated against the new page (`tests/browser/test_page.py`). Slice 2 is done (entry 0.13): the two start screens, saved work offered only for its own number, the reading settings and their drawer, branding and the band, and the list of what a paper needs. Slice 4 (the PDF, the finish sheet and the receipt) is being done in parts: the receipt, the paper's Paper ID and the rule that work from another version of a paper is set aside, not restored, come first (entry 0.14); the PDF writer, with its fonts, follows (entry 0.15); the finish sheet follows, with one press that saves both files into one folder and reads them back (entry 0.16); the timer, extra time, breaks and the invigilator's code follow, with the invigilator's view of saved and set-aside work, a name check before saved work is continued, and the sitting in the record (entry 0.17). The browser's print window gets the same header and footer (entry 0.18). What is left of step 4 is its "done when": a college PC, the keyboard and NVDA walk-through, and a test Moodle assignment.* *Waits for* D3, D4, D5. *Delivers:* the start and before-you-begin screens; reading settings; branding and the band; storage keys and restore rules (§5.2); the save indicator and the output cap; the finish sheet; the `.html` answer file and the PDF; the receipt; `timer`, extra time and `breaks`; print headers and footers on every page; the first-wave kinds' page halves. *Done when* a written sample is sat start to finish on a college PC with the network off, by keyboard alone and with the NVDA screen reader (start screen, one part of each first-wave kind, finish sheet), in Chrome and Edge; the reload, crash, second-window and full-storage rehearsals pass; and the PDF and answer file upload to a test Moodle assignment and open in its grader.

**Step 5. Python in the room.** *Delivers:* the exam engine ported from dewlab (worker, `input()` in the output, Stop, a two-layer time limit, output cap); Python inside the file, in a folder beside it, or from the internet (`python from`); set-up code and data files; the loading checklist's real states; `room-check.html`. *Done when* a converted PDP practice paper is sat on the college PCs with the network cable out, and the runaway-loop, `except Exception` and cancelled-`input()` rehearsals pass.

**Step 6. The workbench grows up.** *Delivers:* the new answer files and scheme JSON; marking by part with propose and evidence; hidden tests beside the model answer's results; how each mark was made; Moodle zips and the received log; `marks.xlsx`; a combined graded-paper print and per-student feedback files; the rule-based marking check; the archive; an importer for PDP submissions already sat. *Done when* a mock marking of the PDP Sample with ten test submissions is exported and read cold by a colleague, and the marks match the college's results template. **The first practice sitting can happen after step 5**, marked from the PDFs if step 6 is not done.

**Step 7. The studio.** *Delivers:* §4's studio grown from the checker: home, editor with Insert, live check, preview, Sit it, Issue (split folder, lock, fingerprint, sitting card), templates, converters, the downloadable folder and offline use. *Done when* a teacher who has never used a terminal writes, checks and issues a paper like the mixed sample, watched by Josh, without help.

**Step 8. Subject waves.** In the order the next papers need: *biology* (`match`, `order`, `Choose from:` banks, material that stays in view); *maths* (the maths reader, preview and palette, MathLive, `photo` per D8, `on-paper` with labelled sheets); *practice* (`show answers`, `practice tests` per D7, Make a practice copy, dewlab's import form, the check phrase). *Done when* the biology and maths samples, rewritten, are sat and marked in rehearsal with keyboard-only and screen-reader passes, and a practice paper shows its answers only after finishing while its exam build passes the leak search.

**Step 9. The connected assistant.** *Delivers:* settings and Test connection; the per-page security policy; the client in both dialects; tasks, validators and log; Check a paper; connected conversion in five modes; draft schemes; Word my notes; D9's rule; `docs/AI_ACT_ASSESSMENT.md`. *Done when* every failure in `assistant.md` §1.7 is produced on purpose and reads correctly to a non-programmer, and the paper check finds at least 60% of twenty planted faults with no more than one false alarm per ten questions on the recommended models (Josh sets the final bar).

**Alongside:** the mark-suggestion study decision 17 asks for, `planning/MARK_SUGGESTION_STUDY.md` (evidence, regulation, what a design would need), best written once step 9's evaluation harness can supply measurements.

**Later, when use asks:** a guided form editor, expression keys with form checks, per-student PDFs with full question wording, a learning-outcomes sheet and verification pack, a tested Safe Exam Browser profile, a room server for a Stop that keeps variables, read-aloud, a college colour, Parsons problems and hotspots.

---

## 10. Which planning documents change

dewmark's planning documents (in `dewlab/dewmark/planning/` today, `planning/` after the move) were written before this round. Each changes in the step that builds what it describes, following dewlab's rule that a change is not finished until the document describing the behaviour describes the new one.

| Document | Change | Step |
|---|---|---|
| `THE_EXAM_FILE.md` | Replaced by `docs/EXAM_FORMAT.md`; kept as a one-line pointer | 3 |
| `QUESTION_TYPES_AND_MARKING.md` | Rewritten around the kinds and the registry; the three marking methods stay; "assisted, never automatic" replaces "no pre-checking"; §4 "Adding a type" becomes the registry | 3, 8 |
| `THE_EXAM_BUILDER.md` | One builder, two front doors; the pure core; the four secrecy layers; the lock, fingerprint and pins | 3 |
| `TRANSLATING_AN_EXISTING_EXAM.md` | The PDP converter; the paste route; decision 19's modes; the connected route | 3, 9 |
| `THE_EXAM_PAGE.md` | Rewritten from §5: the two start screens, loading, save indicator, engine, finish, recovery, practice after finishing | 4, 5 |
| `THE_SUBMISSION.md` | The `.html` answer file with embedded data plus the PDF; the zip dropped; the file name as typed, not surname first; the receipt; the version and restore rules | 4 |
| `APPEARANCE_AND_READABILITY.md` | Extended: the reading settings list, the band, branding placement, print headers on every page | 4 |
| `THE_MARKING_WORKBENCH.md` | The unit of marking is the lowest heading with marks; propose and evidence; tests; the "how" of each mark; the exports; the received log; the assistant record | 6 |
| `ROADMAP.md` | Replaced by §9; its standing rules stay (formats frozen before a real sitting; no real papers or submissions committed) | 1 |
| `OPEN_QUESTIONS.md` | Closed with log entries: Q1 (decision 6), Q3 (xlsx), Q4 (decision 11), Q6 (best N counted, marker overrides), Q7 (decision 7 and the probes), Q9 (`on-paper`, decision 15), Q10 (decision 5), Q12 (decision 8), Q13 (decision 12), Q14 (show both, never merge), Q15 (decision 13), Q17 (decision 15). Narrowed: Q2 (a combined print first), Q5 (matching on number; the class list optional), Q8 (rare with the worker engine), Q19 (suggest with quotes, later). Still open: Q11 (the name), Q16 (what is promised to a screen-reader user), Q18 (passage comments) | 1, then as settled |
| `LESSONS_FROM_THE_EXPERIMENTS.md` | Kept as history; gains the PDP lessons from `pdp-pages.md` | 1 |
| `docs/FOR_TEACHERS.md` | Rewritten around the checker and studio (no `pip`, no terminal), the paper folder, Moodle's "Force download", the room check | 3, 7 |
| `docs/DEVELOPMENT.md` | Becomes `CONTRIBUTING.md` and `ARCHITECTURE.md` in dewlab's shape | 1 |
| `README.md` | Rewritten for the standalone repository | 1 |

New documents: `DECISIONS_LOG.md` (step 1), `docs/EXAM_FORMAT.md` (step 3), `docs/AI_ACT_ASSESSMENT.md` and `docs/ASSISTANT_EVALUATION.md` (step 9), `planning/MARK_SUGGESTION_STUDY.md` (after step 6).

---

## Appendix: every design and research file

Decision 2's cleanup took these files off `main`. They are kept in the repository's history at commit `b3823f91799f`, where the links below point. Elsewhere in this proposal, a file named in backticks without a path, such as `architecture.md` or `code.md`, is one of these; the exam format itself, `format.md` in the designs, now lives at [`docs/EXAM_FORMAT.md`](../docs/EXAM_FORMAT.md).

**Decisions:** [`DECISIONS_2026-09-27.md`](DECISIONS_2026-09-27.md).

**Designs** (`design/`): [`docs/EXAM_FORMAT.md`](../docs/EXAM_FORMAT.md), the unified exam format; the three rival proposals it judged, [`format-paper-first.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/design/format-paper-first.md), [`format-typed-blocks.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/design/format-typed-blocks.md), [`format-one-fence-family.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/design/format-one-fence-family.md); [`architecture.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/design/architecture.md), the move, sharing with dewlab, the teacher's journey, the two front doors, versioning; [`student-flow.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/design/student-flow.md), the sitting and branding; [`question-types.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/design/question-types.md), exam kinds, answer kinds, the registry, maths, programming, biology, QQI fields; [`assistant.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/design/assistant.md), the language-model assistant; [`synthesis-notes.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/design/synthesis-notes.md), every contradiction between them and its settlement.

**Mockups:** [`mockups/teacher-studio.html`](mockups/teacher-studio.html), [`mockups/student-start.html`](mockups/student-start.html).

**Research** (`research-2026-09-27/`): [`design-docs.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/design-docs.md), dewmark's written design and its critique; [`code.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/code.md), the builder, page and workbench audited and run, with the bugs; [`pdp-pages.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/pdp-pages.md), the PDP pages taken apart; [`dewlab-runtime.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/dewlab-runtime.md), dewlab's reusable pieces and the verified engine; [`extraction.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/extraction.md), the move rehearsed; [`local-llm.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/local-llm.md), serving, models, marking evidence, the AI Act; [`exam-types.md`](https://github.com/deweydex/dewmark/blob/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/exam-types.md), question types, QTI and QQI. Probes: [`probes/`](https://github.com/deweydex/dewmark/tree/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/probes/); screenshots: [`shots/`](https://github.com/deweydex/dewmark/tree/b3823f91799f9332b4b16a596fa8a9d6147a6906/planning/research-2026-09-27/shots/).

**Primary sources:** the PDP papers in [`../experiments/pdp-5n2927/`](../experiments/pdp-5n2927/); dewmark's current code and documents in `dewlab/dewmark/`; dewlab's `build.py` (`parse_question`, line 1515), `DECISIONS_LOG.md` 7.179, `assets/pyodide-engine.js` and `assets/tutorial-style.css`.
