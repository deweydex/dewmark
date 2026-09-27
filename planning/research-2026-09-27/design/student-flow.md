# The student's journey through a sitting, and exam branding

Design proposal, 2026-09-27. Topic owner: the student flow. It builds on the seven research reports in `planning/research-2026-09-27/` and on the four PDP 5N2927 papers in `experiments/pdp-5n2927/`. The clickable mockup is [`planning/mockups/student-start.html`](../../mockups/student-start.html). It opens from disk and makes no network requests. Its **Try a scenario** menu shows returning work on a shared computer, slow and failed Python loading, a browser that cannot save to a file, a full browser store, and the practice variant.

Two limits on scope. The exam file's grammar belongs to the format design, so the keys below are named but not given a final syntax. The question types belong to the question-types design; this document covers how any type looks and saves during a sitting.

---

## 0. The recommendation on one page

A sitting has five screens.

1. **Cover.** The front of the paper, as on a printed booklet: institution, college, module and code, paper title, session, time and marks, under a band that says EXAMINATION or PRACTICE PAPER. The student types their name and number. If this computer holds their saved work, the page offers it now, and only to them.
2. **Reading settings.** Font (Lexend and OpenDyslexic built in), size, spacing, line length, colours, reading ruler, reduced motion, and code-editor options. The screen restyles as the student chooses, and a preview shows a real question from the paper. Settings stay reachable from every screen.
3. **Get ready.** Candidate instructions, a checklist of everything the paper needs with each row's true state, the choice of where the answer file goes, extra time, and Begin. Python has been loading since the page opened.
4. **The paper.** A slim bar with the kind badge, student, time, a save indicator that reports only completed saves, and Finish. A side panel with progress per question. Code cells with Run, Stop, and `input()` as a line in the output.
5. **Finish.** Check your answers, save your answer file, hand it in. A confirmation card shows name, number, file, answer count and a receipt code, which the teacher's workbench also shows.

**Decisions for Josh**, most urgent first. Each is argued in the section named.

| # | Question | Recommendation | Section |
|---|---|---|---|
| D1 | Identity before settings, or settings first? | Identity first, then settings as a full step. Settings stay reachable from the cover with one button. | §3, §4 |
| D2 | What does a student hand in? | One answer file: a `.html` page that shows the paper with the answers in place and carries the answers inside as data. Drop the zip. In exam mode, drop the student-made PDF. | §8 |
| D3 | Timer? | Show "time left", which the student can hide. Never enforce it. Extra time and rest breaks are declared on the Get ready screen and recorded in the answer file. | §6 |
| D4 | Which student details? | Two fixed keys, `name` and `number`, whose labels the teacher can change. The teacher also gives one example number instead of a pattern. The workbench matches on `number`. | §3 |
| D5 | Branding reach | Text keys plus an optional logo in the first release. The logo is decoration, so it has no alt text. There is no college accent colour for now. dewmark's fixed band tells an exam from practice. | §11 |
| D6 | Saved work on a shared computer | Key it by paper, variant and student number. Show nothing until the student types their number. Never delete: "start again" sets the old copy aside. | §3 |

**What ships first:** the cover, settings and Get ready screens for written papers, together with the storage fixes, the save indicator and the finish screen. Python loading, `input()` and Stop come with the new engine. The logo, print headers, the time display and the invigilator's recovery view come third. §12 has the steps.

---

## 1. Principles the flow keeps

Each comes from a failure already seen in dewmark's drafts or the PDP pages.

- **Nothing blocks written work.** Offline, a missing CodeMirror stops the whole PDP page (`pdp-pages.md` §7).
- **The page never shows one student's name to another.**
- **Saved work is read-only until the student enters the paper.** This fixes Bug A (`code.md` §2).
- **Every status comes from a completed event.** "Saved 10:42" means a write finished at 10:42; "Ready" means a test ran. PDP's "Saved in browser" stayed on screen after storage filled (`pdp-pages.md` §8.2).
- **One kind of student file**, which the student can open to check.
- **Practice rehearses the exam**, with the same screens, labelled differently.
- **No pop-up dialogs** (`alert`, `confirm`, `prompt`), except the `input()` fallback on older browsers (§7.4).
- **Messages say what happened, whether the work is safe, and what to do next** (`APPEARANCE_AND_READABILITY.md` §6).

---

## 2. Opening the page

### 2.1 The ways a student opens an exam

| Route | Address | Written paper | Python | Saving to a file as you go | Browser storage |
|---|---|---|---|---|---|
| Double-click in a folder (a room kit on a shared drive, a USB stick, the desktop) | `file://` | Works with no network | From a room server, from Python built into the page, or from a warm cache (§5.3) | Yes, in Chrome and Edge | One store shared by every `file://` page in that browser profile (verified, `dewlab-runtime.md` §6) |
| Downloaded from Moodle, then double-clicked | `file://` from Downloads | Same | Same | Same | Same |
| Opened inside Moodle as a web page | Moodle's own address | Works, but runs inside Moodle's site | Internet only | No | Moodle's, shared with every file on that Moodle |
| Link to the dewmark site (practice at home) | `https://deweydex.github.io/…` | Works | From the internet | Yes | This site's own |
| Page served from a teacher's laptop over the room network | `http://10.x.x.x:…` | Works | From that laptop, with a true Stop | **No.** A plain-http network address is not a "secure context", so the browser refuses file saving | That laptop's own |

I checked two cells in headless Chromium 141 this round (`scratchpad/design-round/student-flow/probe.html`): a `file://` page is a secure context, with working `crypto.subtle` and `showSaveFilePicker`, but `fetch()` of a file beside the page fails. The second result shapes §5.3.

For a room, students double-click the exam in the kit folder. At home, a Moodle download or the site link both work. The teacher guide should say to put the exam on Moodle as a file to download ("Force download"), never as a page shown inside Moodle.

### 2.2 The first second

Before anything paints, a tiny script applies the reading settings stored on this computer (`dewmark:reading`), so a student who chose OpenDyslexic at 22 px last week sees the cover that way with no flash. Python then starts loading in a background Worker, overlapping the first two screens. dewmark today starts Python only after Begin (`exam-page.js` L297); PDP starts at page open, which is better.

Three quiet checks speak only when they fail. Inside Moodle's site: "This exam is open inside Moodle, so your work cannot be saved safely. Download the file, then open it from your computer." A browser too old for MathML: "This browser is too old to show the maths in this paper. Tell your invigilator." Storage: a test key is written, read back and deleted, the only write before Begin. A small line on the cover says where the page came from ("Opened from this computer"), so an invigilator can see a student has the right copy.

---

## 3. Screen 1: the cover, and who you are

### 3.1 What the cover shows

A sheet under the kind band (§10): logo if any, institution, college, a rule, module name and code, paper title, and a facts row (session, time allowed, total marks, weighting). The PDP name card has most of this (`PDP_5N2927_Sample_Exam.html` L344–371); dewmark's start screen has only a navy band with the title (`build_exam.py` L1136–1153, `shots/code/01-mixed-start-screen.png`). The candidate instructions move to Get ready, directly above Begin, where the student acts on them.

### 3.2 Which details, and how they are typed

Today `student_details` is a free list of labels, and the page and workbench look up the literal strings `"full name"` and `"student number"` (`exam-page.js` L225–230, `workbench/index.html` L219). Any other label silently becomes `student` in the file name. I recommend a small fixed vocabulary of keys, each with a label the teacher can reword.

| Key | Default label | Required | Stored as | Used for |
|---|---|---|---|---|
| `name` | Full name | yes | typed text | display, file name, workbench |
| `number` | Student number | yes | typed text, plus a normalised copy (upper case, no spaces or hyphens) | save key, matching in the workbench, file name |
| `seat` | Desk or seat | no | typed text | invigilator's lookup in a large room |

One name field, not first name and surname: Ó Briain, Mac Giolla Phádraig and single names do not split cleanly, so `THE_SUBMISSION.md`'s surname-first file name is dropped and the name is used as typed.

The number is the key everything depends on, so the teacher gives an example instead of a pattern: `number_example: D00123456`. The page derives a loose shape from it and warns once, without blocking: "D0012345 has 8 characters. Student numbers here usually look like D00123456. Check it, then press Next again to continue." The workbench's class-list check (Q5) catches the rest. Errors sit under their field (`aria-describedby`), and focus moves to the first one, replacing `alert()` (`exam-page.js` L259–266).

### 3.3 Recognising a return without mixing students or papers

Every `file://` page in a browser profile shares one storage area (verified, `dewlab-runtime.md` §6), so a shared computer may hold several students' work on one paper, in both variants. dewmark keys storage too loosely: `beforeunload` writes an empty state from the start screen and wipes saved answers (Bug A, `exam-page.js` L892–896), and the key `"dewmark:" + exam_code` (L6) lets the practice paper and the answer key share the exam's slot (Bug B). PDP shows "This browser has saved work for **Name**" to whoever opens the page next, continues it with no identity check, and deletes it on "Start this paper again" (`PDP_5N2927_Sample_Exam.html` L842–857).

**Keys.** Keys start with `dewmark:1:`, where `1` is the storage format version.

```text
dewmark:reading                              reading settings, shared by every paper on this computer
dewmark:1:<exam_code>:<variant>:<number>     one sitting's answers (the same data as the answer file)
dewmark:1:<exam_code>:<variant>:<number>:out code output, stored apart from the answers and capped
dewmark:1:set-aside:<ISO time>:<same tail>   a sitting the student chose to start again
```

`variant` is `exam` or `practice`; the answer key stores nothing. `version` lives inside the record, not the key, so a corrected paper still finds the work, and permanent names put answers back on the right questions. The lookup runs when the student presses Next on the cover, with the number they typed.

| What the page finds under this paper, variant and number | What the student sees |
|---|---|
| Nothing | Nothing. They continue to settings. |
| Unfinished work, same name | "Welcome back. This computer has your work on this paper: 14 answers, last saved at 10:41 today." Buttons: **Continue my work** and **Start again** (explained below). |
| Unfinished work saved under a different name | "Work for D00123456 on this computer was saved under the name Aoife Byrne. Is this you?" This is shown only to someone who typed that exact number. |
| Work already finished on this computer | "You finished this paper on this computer at 11:58." Options: **Save my answer file again**, and **Open the paper again** (to be used when the invigilator grants more time). |
| Work saved under a different paper version | As for unfinished work, plus: "This paper was corrected after your work was saved. Your answers go back to the same questions." |
| Only practice work, while opening the exam | Nothing. The variants never see each other. |

**Start again** confirms on the page and never deletes: the old record moves to a `set-aside` key that the invigilator's view (§9) can still find. **Writes begin at Begin or Continue**; after that, `beforeunload` writes only unsaved changes. **A second window** on the same sitting (a `BroadcastChannel` named after the full key) says "This paper is already open in another window for D00123456. Use that window. This window will not save.", turns read-only and never writes; today's guard calls `alert()` but its `beforeunload` still saves (`code.md` §2). **I have an answer file**, a quiet link on the cover, is the route to a new computer (§9).

---

## 4. Screen 2: reading settings

### 4.1 Why second, and why a full step

Josh asked whether settings should come first. I recommend identity first. Resume needs identity: the page must know who is asking before it mentions saved work. Settings are remembered per computer, not per student, so straight after identity is the place to say "these may be someone else's; check them". And the cover is two fields: a student who needs different settings even for that presses **Aa Reading settings** in its corner, which opens the same panel.

Settings get a full step rather than PDP's small link (`PDP_5N2927_Sample_Exam.html` L367) because a step reaches students who would never ask. Many adult learners have needs that were never assessed, and a step tells everyone that changing the page is normal. It costs one press of Next.

### 4.2 The settings

The baseline is the PDP drawer (`PDP_5N2927_Sample_Exam.html` L412–461) and dewlab's texture panel (`TEXTURE_DEFAULTS`, `tutorial-runtime.js` L40; tokens in `tutorial-style.css` L1–80).

| Group | Setting | Choices | Default | Notes |
|---|---|---|---|---|
| Reading | Font | Standard (serif), Plain (sans), Lexend, OpenDyslexic | Standard | Lexend and OpenDyslexic are built into the page from dewlab's vendored files: about 29 KB and 464 KB, or roughly 660 KB inlined (`dewlab-runtime.md` §4). dewlab chose Lexend over Atkinson Hyperlegible (DECISIONS_LOG 7.127); dewmark follows. |
| | Text size | 14 to 32 px | 18 px | Slider with − and + buttons and a visible value |
| | Line spacing | 1.3 to 2.4 | 1.6 | |
| | Letter and word spacing | Normal, Wide, Wider | Normal | |
| | Line length | Narrow, Medium, Wide, Full width | Medium (about 65 characters) | |
| | Colours | Match my computer, Light, Cream paper, Blue tint, Dark, High contrast | Match my computer | "Match my computer" follows `prefers-color-scheme` and `prefers-contrast`. The PDP pages ignore both (`pdp-pages.md` §6). |
| | Reading ruler | Off, On | Off | Follows the text cursor and keyboard focus as well as the mouse. PDP's follows the mouse only. |
| | Reduce motion | Follow my computer, On | Follow | Honours `prefers-reduced-motion` |
| Code (only on papers with code) | Code text size | 12 to 28 px | 16 px | |
| | Code colours | Match the page, Light, Dark | Match | |
| | Wrap long lines | On, Off | Off | |
| | Close brackets and quotes | On, Off | On | |
| | Code suggestions | On, Off, "Pop up while I type" | On, when the paper allows | The teacher's `completion` key can remove this group. PDP's Jedi setting. |
| Time | Show time | Time left, Clock, Hidden | Time left (exam), Hidden (practice) | §6 |

**Live preview.** The whole screen restyles as the student changes a setting, and a preview card shows real content from this paper (the builder picks the first question's opening, one answer box and three lines of code), not "the quick brown fox".

**Use standard settings** is always visible. When stored settings differ from the standard, a note beside it says: "These settings are remembered on this computer. If someone else used it before you, check them." Printing always uses the standard layout, and the panel says so.

**Nothing about reading settings is recorded.** They are for everyone, and a font choice can reveal a disability. The answer file records only accommodations a marker or QQI record needs: extra time and rest breaks (§6).

**Fixes to the PDP drawer:** a closed panel is `inert` (PDP's kept 32 focusable controls, `pdp-pages.md` §6); Escape closes it and focus returns to its button; radio groups are native radios styled as segments (dewlab 7.130).

---

## 5. Screen 3: get ready

### 5.1 What is on it

In reading order:

1. **You are** "Aoife Byrne · D00123456", in large type, with Change.
2. **Instructions to candidates**, from the exam file.
3. **The checklist** (§5.2).
4. **Your answer file.** **Choose where to save…** opens the save dialog from a button the student pressed, not as a surprise at Begin (today's behaviour in dewmark and PDP). The row then names the file. Where the browser cannot save as you go (Firefox, Safari, Safe Exam Browser with file access off) it says: "This browser saves your work in the browser only. You will save your answer file at the end."
5. **Time.** "Time allowed: 2 hours. Your time starts when you press Begin." **Extra time**: None, 10 minutes for each hour (20 minutes), 15 minutes for each hour (30 minutes), Other; "Only choose this if the college has given you extra time. Your invigilator will check."
6. **Begin**: "Press Begin when your invigilator tells you to start." The questions stay hidden until then, as a printed paper stays face down.

### 5.2 The checklist, and progress that tells the truth

| Row | Where it comes from | Possible states |
|---|---|---|
| The paper: questions, pictures, maths | Inside this page | Ready |
| Fonts and code editor | Inside this page | Ready |
| Python (12.3 MB core, Pyodide 0.28.3) | Built into the page, the room server, or the internet (§5.3) | Waiting, Loading (with MB), Ready, Failed, Not needed |
| Packages this paper uses, for example pandas 23.8 MB | Same source | as above, or "Not needed for this paper" |
| Data files, for example `hvit_registry.db` | Inside this page | Ready ("copied into Python") |
| Set-up code | The exam file | Ready, or Failed with a message for the invigilator |
| Python check | A short test program | Ready ("print and input work, 0.2 s") |
| Code suggestions (5.3 MB) | Same source as Python | Loading, Ready, Off. Optional: Begin never waits for it |
| Saving in this browser | Test write | Ready, or Failed |

Rules: a bar appears only when the total size is known (the builder writes every file's size into the page and the engine counts bytes); otherwise a moving indicator and elapsed seconds, never a percentage. Every row ends in a word with an icon, never colour alone. **Ready follows a test**: Python is Ready only after running a short program that answers an `input()` call, after set-up code has finished; PDP enables Run before set-up finishes (`pdp-pages.md` §4.4), and dewmark hides set-up errors in `"dm-nowhere"` (`code.md` §2). One polite live region announces "Python is ready", not every byte.

**Slow.** After 20 s with no new bytes: "Python is loading slowly. You can begin now. Run buttons will turn on by themselves." After 90 s: "Python is still loading. Written answers work now. Tell your invigilator."

**Failed.** "Python did not load. Your written answers work normally, and the code you write is saved even though it cannot run yet. Tell your invigilator." With **Try again** and **Details for your invigilator** ("Could not reach http://10.0.0.5:8756/python/ (connection refused)"). Today dewmark shows only "Python failed — click to retry" (`shots/code/16-python-offline-failure.png`).

**Begin never waits for Python.** A code cell says in place: "Python is still loading (7.4 of 12.3 MB). You can write code now. Run will turn on by itself." That keeps PDP's read-while-loading and dewmark's rule that code never blocks written parts.

### 5.3 Where Python comes from

The engine design decides this; the Get ready row names the source.

- **Room server with CORS, page opened from disk.** Proven in dewlab (7.92, 7.95). File saving still works; Stop restarts Python (§7.4). Check Chrome's local-network rules for `file://` on the ETB build (`local-llm.md` §2).
- **Built into the page.** No room set-up; about 16 MB more for plain Python. Not yet tried.
- **A `python` folder beside the page.** The simplest kit, but `fetch()` from `file://` is refused (checked), so the files would go in as scripts and reach the Worker as bytes. Not probed.
- **Page served from the room server.** A true Stop, but plain http cannot save to a file. Not for exams.
- **Internet**, for practice at home; the exam file can forbid it for the exam variant.

---

## 6. Begin, and the timer

**Begin** records `started_at` unless one exists (it travels in the answer file, so it survives a move of computer), makes the first save, moves focus to the paper's first heading, and starts the time display.

**The timer.** Q4 assumed none. PDP shows a per-student countdown, hideable and never enforced (`pdp-pages.md` §4.4). I recommend that, with three changes.

1. **"Time left" = Begin + time allowed + declared extra time.** The chip reads "1 h 12 min left"; the student can switch to the clock or hide it. The teacher's `timer` key: shown, hidden by default, or off.
2. **At ten minutes left** the words, an icon and bold weight change, announced once and politely. No colour-only warning (PDP's is, `pdp-pages.md` §6), no sound, nothing that takes focus.
3. **At zero nothing locks.** "Time allowed has passed. Keep working until your invigilator tells you to stop." A lock would be wrong for every student who started late or had a crash.

**Extra time** changes only the time shown. It goes into the answer file as `accommodations: {extra_time_minutes: 20, declared: "student"}` and the workbench's accommodations column, which QQI's records guidance asks for (`exam-types.md` §4). Declaring it falsely gains nothing, since nothing is enforced and the invigilator checks. **Rest breaks** (step 3): a button in the time chip pauses the count and records the break.

---

## 7. During the sitting

### 7.1 The screen

- **Top bar** (fixed, slim): Questions (narrow screens), short paper name, kind badge, student name, time chip, save indicator, **Aa**, **Reference** and **Calculator** when the paper has them, and **Finish**.
- **Masthead:** the cover's branding in one compact row at the top of the paper, which scrolls away (§11).
- **Side panel** (a drawer when narrow): each question with marks and progress in words and a bar ("15 marks · 3 of 6 parts answered"); rough work left out, as in PDP (`PDP_5N2927_Sample_Exam.html` L1368); "2 answered · 2 will count" for a choose-N section. Selecting a question moves focus to its heading.
- **Answer spaces** as in `APPEARANCE_AND_READABILITY.md` §2, with "answered" in the accessible name. A space is answered when it differs from its starter text, ignoring spaces (PDP's rule, L1358–1363).

### 7.2 The save indicator never lies

One indicator in the top bar stands for both routes. Selecting it shows the detail for each.

| State | The indicator shows | When |
|---|---|---|
| Saved | ✓ Saved 10:42 | Every route in use finished its latest write |
| Saving | ↻ Saving… | A change is waiting (about 1 s in the browser, 2 s for the file) |
| Browser only | ✓ Saved 10:42 in this browser | No answer file was chosen, or the browser cannot save to one |
| File problem | ! File not saved since 10:39 | A file write failed. A notice offers **Choose a file again** and **Save a copy now** |
| Browser problem | ! Not saved in this browser | Storage is full or blocked. The file route continues |
| Nothing saving | ✕ Your work is not being saved | Both routes failed. A notice that stays on screen offers **Save a copy now** |

A time on screen always comes from a completed write. The quota guard (dewlab 7.133) fixes PDP's silent failure: answers and output are stored under separate keys, output is capped (20 KB per cell in the browser, 200 KB in the file), and a failed write is retried without output, so an answer typed after a runaway `print` loop is still saved.

### 7.3 Rough work, reference and calculator

**Rough work** is labelled "Rough work · not marked", saved and shown to the marker, and left out of progress and finish checks. **Reference** is a searchable side panel holding only what the exam file provides; PDP's Python sheet becomes a standard block a teacher includes by name, with its "10 seconds" wording taken from the paper's settings (`pdp-pages.md` §8.10). **Calculator**: the existing one (`exam-page.js` L914–1036), from the top bar.

### 7.4 Running code

This follows the engine verified in `dewlab-runtime.md` §2: a blob-URL Worker, which starts from `file://`.

- **Editor:** CodeMirror 6 vendored into the page. Tab indents; **Escape, then Tab** leaves, and a hint says so. PDP's editor traps keyboard users (WCAG 2.1.2, `pdp-pages.md` §6).
- **Run** (Ctrl+Enter) becomes **Stop** while the program runs.
- **`input()`** is a labelled line inside the output: the prompt, a focused field, Enter to send, the reply echoed in a highlight, typing time not counted. It uses `run_sync` (verified: `int(input())*int(input())` returned 49). Without JSPI (Chrome 137+; Firefox and Safari unverified) it falls back to PDP's `window.prompt`, and the generated instructions describe whichever the student will see.
- **Stop** on `file://` replaces the Worker (about 1.6 s warm): "Stopped. Python restarted, so variables from other cells are gone. Run the cells this code needs, then run it again." Served with isolation headers, Stop interrupts and keeps variables.
- **Time limit** (`time_limit_seconds`, default 10) in two layers: a trace deadline that raises an exception `except Exception` cannot catch and re-arms itself (fixing PDP's frozen tab, `pdp-pages.md` §8.3), and a watchdog that replaces the Worker a few seconds later, catching `sum(range(10**9))`, which ran 66 s under PDP's limit. "Your code ran for more than 10 seconds, so it was stopped. A loop that never ends usually causes this."
- **Output cap:** after 2,000 lines the Worker stops sending and the cell says so.
- **"Edited since last run"** shows on the cell and in the finish checks. Code runs as `__main__` (`dewlab-runtime.md` §2).

---

## 8. Finishing and handing in

### 8.1 What the student hands in (decision D2)

| Option | For the student | For the teacher | Costs |
|---|---|---|---|
| **A. One answer file, `.html`** (recommended) | Double-clicking it shows their paper with their answers, so they can check it. It is the same file saved during the sitting. | The workbench reads the data block inside. A human can read the file in any browser. | The readable copy is rebuilt on each file save. Moodle must accept `.html`, which needs a check with DDLETB's Moodle admin. |
| B. Zip of `answers.json` and `your-exam.html` (current spec) | Opening it shows a folder, then two files | Needs zip code on both sides. Today's reader handles STORED entries only (`code.md` §3) | Hand-rolled zip writer with a zero date |
| C. JSON plus a student-made PDF (PDP) | Two files to make and upload. Printing to PDF is error-prone: Chrome prints the `file:///` path, and some students pick the lab printer | Two artefacts to match by hand (`pdp-pages.md` §8.12) | |

**Option A in detail.** `pdp-5n2927-exam-2027_D00123456_aoife-byrne.html` (exam code, number, name) holds a readable copy of the paper with answers, branding, times and receipt, laid out by the print rules, with no scripts and a `script-src 'none'` policy; the answers as data in `<script type="application/json" id="dewmark-answers">`, a block browsers never run, holding the schema `THE_SUBMISSION.md` §2 describes (format version, exam code and version, variant, details, times, accommodations, answers by permanent name, capped output, edited-since-run flags, `choose` attempts); and the **receipt code**, the first eight hex digits of a SHA-256 of the data, shown as `7F3A 92C1`. The workbench accepts any file with that block, whatever its name, which fixes Bug G (the scheme read as a student, `code.md` §3), and keeps reading `.json` and old zips.

**In exam mode the student makes no PDF.** The answer file is the evidence and prints cleanly; assessors' PDFs come from the workbench. Practice keeps an optional **Print or save as PDF**.

### 8.2 The finish screen

**Finish** opens a sheet of three numbered steps; the order matters.

1. **Check your answers.** Counts, then links (`APPEARANCE_AND_READABILITY.md` §6): "2 answer spaces are empty, worth 6 marks: 1(e), 3(b)." "1 code answer was changed after it last ran: 2(c)." "Section B: 1 answered, 1 will count." Labels are the paper's own, and totals respect `choose` rules; today the mixed paper reports 64 marks empty on a 50-mark paper (`code.md` §2, `shots/code/05-mixed-finish-screen.png`).
2. **Save your answer file.** With a file chosen, the page writes it, reads it back through the handle, parses it and compares the receipt: "Checked: the file holds 17 answers. Receipt 7F3A 92C1." Otherwise **Save my answer file** downloads it, and since a download cannot be checked from the page: "Your browser put the file in Downloads. To check it, open it: it shows your answers."
3. **Hand it in.** Text from the `hand_in` key, for example "Upload the file to 'PDP Written Examination submission' on Moodle. Then raise your hand. Your invigilator will check this screen." It replaces PDP's hard-coded Moodle wording (`PDP_5N2927_Sample_Exam.html` L1348–1350) and dewmark's (`exam-page.js` L421–424).

A **confirmation card** follows: name in large type, number, paper, file name, "17 of 19 answer spaces used", save time and receipt. The invigilator checks it; the workbench lists the same receipt, and its received log (file, receipt, time) is QQI §4.2.7's record of evidence received (`exam-types.md` §4).

**Finishing ends nothing.** A later change brings "You changed 2 answers after saving your file. Save it again and hand in the new one."; the workbench marks the newest file per number (`THE_SUBMISSION.md` §4). On a shared computer, **Remove my work from this computer** appears once step 2 has checked the file or the student confirms they have it.

### 8.3 Printing

Always the standard layout. Every page has a header (college · module code and name · paper) and a footer (name · number · page N of M, plus "PRACTICE PAPER" on practice), using CSS page-margin boxes; I checked this round that Chromium 141 prints them, including a custom-property string and page counts (`scratchpad/design-round/student-flow/print.html`). Empty spaces print "not attempted" (`APPEARANCE_AND_READABILITY.md` §4). PDP prints the name on page 1 only (`pdp-pages.md` §8.12).

---

## 9. Recovery

| What happened | What the student does | What the page does |
|---|---|---|
| Closed the tab, or the browser crashed | Opens the page again and types their details | Offers "Continue my work", then says "Restored 14 answers saved at 10:41. Python has restarted: run your code cells again to rebuild variables." |
| The page stopped responding | Rare with the Worker. On the fallback engine, closes and reopens the page | The remedy is in the side panel from the start (`THE_EXAM_PAGE.md` §5) |
| Moved to another computer | Opens the page, types their details, then chooses **I have an answer file** and opens their file from USB or the network drive | Checks exam code, variant and version, shows the file's answer count and save time, and asks "Is this you?" if the name differs. `started_at` comes from the file, so time left stays right |
| The browser copy and the file disagree | Chooses one | Shows both with save times and answer counts (clocks can disagree), never merging (Q14) |
| USB stick pulled out | Chooses a file again, or saves a copy | The indicator shows "File not saved since 10:39". The browser route continues |
| Browser storage full | Nothing, usually | Stores answers without output, and says so if that also fails (§7.2) |
| Lost file, and the first computer's browser still has the work | Asks the invigilator | **Saved work on this computer (for invigilators)**, a small link on the cover, lists this paper's sittings masked ("A. B. · …456 · 14 answers · 10:41") with **Save a copy**. Masking stops a casual glance; it is not security, since developer tools can read storage |
| Invigilator grants more time after Finish | **Back to the paper**, then saves again | The newer file supersedes. The finish sheet shows which version is current |

---

## 10. Practice, sample and exam

| | Exam | Practice or sample |
|---|---|---|
| Band on cover, masthead and top bar | **EXAMINATION**: white capitals on solid ink | **PRACTICE PAPER** (or SAMPLE PAPER): green capitals on a striped, outlined band. A different word, pattern and colour, so the difference never rests on colour alone |
| Storage | `…:exam:…` | `…:practice:…`, never offered in the exam |
| Help | No hints, no self-checking | Hints shown. Closed questions may check themselves (see the question-types design) |
| Python source | The room kit. Internet only if the exam file allows it | May use the internet |
| Time display default | Time left | Hidden, and the student can turn it on |
| Error hints under tracebacks | The teacher's `error_hints` (PDP's 2027 paper turns them off) | On by default |
| Finish | Three steps, `hand_in` text, confirmation card | The same steps, each introduced with "In the real exam, you will…", plus optional printing. PDP's idea that practice rehearses the real hand-in is worth keeping |
| Answer file name | `…_exam-…` code | The practice paper's own code |
| Printing | Standard, "EXAMINATION" in the footer | Standard, "PRACTICE PAPER" in the footer |

---

## 11. Branding

### 11.1 Keys

The keys are named here. The format design decides the syntax. The example values come from the PDP 2027 paper's front matter.

| Key | Example | Required | Replaces or adds |
|---|---|---|---|
| `institution` | Dublin and Dún Laoghaire ETB | Recommended | New to dewmark. PDP has it |
| `college` | Dublin College Dundrum | Recommended | New. PDP has it |
| `logo` | `pictures/dcd-logo.svg` | Optional | New |
| `logo_dark` | `pictures/dcd-logo-light.svg` | Optional | New. Otherwise the logo sits on a light plate in dark themes |
| `module` | Programming and Design Principles | Yes | New. PDP writes module and code in one string |
| `module_code` | 5N2927 | Yes | New, kept apart so file names, sorting and QQI records can use it |
| `title` | Written Examination 2026–2027 | Yes | Exists |
| `kind` | `exam`, `practice` or `sample` | Yes | New to dewmark (PDP has it). The builder's practice build switches it automatically |
| `session` | 2026–2027 | Recommended | New. PDP has it but shows it only in print |
| `time_allowed`, `total_marks` | 2 hours, 60 | Yes | Exist |
| `weighting` | 30% | Optional | New (a QQI field, see the question-types design) |
| `instructions` | Candidate instructions | Yes | Exists |
| `hand_in` | "Upload the file to … on Moodle. Then raise your hand." | Yes when `kind: exam` | New. Replaces the hard-coded Moodle text |
| `student_details`, `number_example` | name, number; D00123456 | Yes | Reworked (§3.2) |

### 11.2 Where each appears

| | Cover | Top bar | Masthead | Print header | Print footer | Answer file | Tab title |
|---|---|---|---|---|---|---|---|
| Kind band | ✓ large | badge | ✓ | — | ✓ | ✓ | — |
| Logo | ✓ up to 48 px tall | — | ✓ 28 px | page 1 only | — | ✓ | — |
| Institution | ✓ | — | ✓ | — | — | ✓ | — |
| College | ✓ | — | ✓ | ✓ | — | ✓ | — |
| Module and code | ✓ | code only | ✓ | ✓ | — | ✓ and in the file name (via exam code) | code |
| Paper title | ✓ | short | ✓ | ✓ | — | ✓ | ✓ |
| Session | ✓ | — | ✓ | ✓ | — | ✓ | — |
| Time, marks, weighting | ✓ | time left | ✓ | — | — | ✓ | — |
| Student name and number | typed here | name | — | — | ✓ every page | ✓ and in the file name | name, after Begin |

The browser tab reads "5N2927 Written Examination · Aoife Byrne" after Begin, so an invigilator walking behind a row can see whose paper each screen holds.

### 11.3 How a logo is embedded

- SVG, PNG, JPEG or WebP, converted to a `data:` URI and shown only through `<img>`, where an SVG's scripts never run; the builder also strips scripts, event attributes, external links and `foreignObject`.
- Warn above 30 KB and refuse above 150 KB, since the logo is copied into every answer file; warn when a raster is under 96 px tall.
- **The logo is decoration** (`alt=""`): the names are always written beside it, so it is never the only place a name appears and needs no description.
- In dark and high-contrast themes it sits on a small light plate unless `logo_dark` is given.

### 11.4 Keeping it tasteful and accessible

**dewmark owns the colours**: no college accent in the first release, so every theme keeps its checked contrast and the band means the same in every college; a checked `accent` key can come later. **dewmark owns the fonts**: college fonts are not reliable offline and would fight the reading settings. **Names are text**, so they read aloud and enlarge. **Branding is quiet after the cover**: one compact masthead row, and only badge and code in the top bar, so the questions hold the attention.

---

## 12. What ships first and what waits

| Step | Delivers | Needs | How we know it works |
|---|---|---|---|
| **1. Safe to sit a written paper** (before any sitting, together with the data-loss fixes) | Storage keys by paper, variant and number. No writes before Begin. Guarded `beforeunload`. The answer key never saves. "Start again" sets work aside. The second-window notice. The `name` and `number` keys with inline errors. The cover, reading settings (fonts, size, spacing, width, six colour schemes, reduced motion) and Get ready screens. Branding text keys and the kind band. `hand_in`. The save indicator and quota guard. The finish screen with correct counts and the receipt. The answer-file format (D2), implemented, because formats freeze before the first sitting (`ROADMAP.md`) | Nothing from the Python engine | Rehearsals for Bugs A and B, practice and exam side by side on `file://`, a full storage quota, a keyboard-only sitting; then a mock sitting offline (Phase 1's exit test) |
| **2. Python in the room** (with the new engine) | The loading checklist with sizes, sources, set-up and self-test. Slow and failed messages. The Worker, `input()` line, Stop, two-layer time limit, output cap and code settings. The standard Python reference block. Suggestions as an exam option | The exam engine and the room kit | The PDP Sample sat offline with a room server; rehearsals for runaway, `except Exception` and C-level loops and a cancelled `input()` |
| **3. Before wider use** | Logo. Print headers and footers on every page. Time display, extra time and rest breaks. The reading ruler following the cursor. The invigilator's saved-work view. The read-back check after saving. The "opened inside Moodle" warning and browser checks | Step 1 | A sitting on the college's own machines, under the ETB's Chrome build, and in Safe Exam Browser if the college uses it |
| **Later** | Read aloud (`speechSynthesis`, offline with Windows voices). A checked `accent` colour. An encrypted live paper (`exam-types.md` §5). A tested SEB profile. "Run the cells above" after a restart | Real use | Requests from rooms and students |

---

## 13. To verify before the steps above close

- Python from a folder beside a `file://` page, as scripts handed to the Worker (not probed).
- JSPI `input()` in Firefox and Safari, and whether the ETB's Chrome is 137 or later.
- Chrome's local-network permission for `file://` reaching the room server, on the ETB build.
- Moodle accepting `.html` uploads, and "Force download" on the exam file.
- Safe Exam Browser: downloads and file access are off by default (`exam-types.md` §5); a tested profile must allow downloads at least.
- Edge on `file://`: `crypto.subtle`, `showSaveFilePicker` and page-margin headers (all checked in Chromium 141 only). Browsers' own "Headers and footers" print option adds the file path; the teacher guide should say to untick it.

## Evidence used

`code.md` §2–3, `pdp-pages.md` §4–8, `dewlab-runtime.md` §2, §4, §6, `design-docs.md` §5, §9, `exam-types.md` §4–5, `local-llm.md` §2 (no model code on student pages; the exam page and answer file both carry a restrictive content policy), dewmark's `THE_EXAM_PAGE.md`, `APPEARANCE_AND_READABILITY.md`, `THE_SUBMISSION.md`, `OPEN_QUESTIONS.md` (Q4, Q5, Q13, Q14, Q16), and the four PDP pages. New this round, in headless Chromium 141 (probes in `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/design-round/student-flow/`: `probe.html`, `print.html`): `file://` is a secure context with `crypto.subtle` and `showSaveFilePicker`; `fetch()` of a sibling file fails; page-margin boxes print.
