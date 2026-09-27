## 3. The teacher's journey, end to end

Twelve stages. The table names the tool and what each stage leaves behind; the prose says what the teacher sees.

| # | Stage | Where | What results |
|---|---|---|---|
| 1 | Open dewmark | studio (web address or downloaded folder) | — |
| 2 | Write, or start from a template | studio editor | `<paper>.exam.md` in the paper folder |
| 3 | Convert an existing paper | studio, Convert | the same exam file |
| 4 | Check | live in the editor | a list of problems, or "ready" |
| 5 | Sit it as a student | studio preview | a test submission the teacher can mark |
| 6 | Issue for a sitting | studio, Issue | `issued/<sitting>/`: pages, scheme, sitting card, room check; the names lock |
| 7 | Prepare the room | room check on one or every PC | a green light per PC |
| 8 | Give it to students | Moodle, shared drive, USB | — |
| 9 | Collect | Moodle download, hand-in folder, USB | `submissions/<sitting>/` |
| 10 | Mark | workbench | `marking/<sitting>/marking-record.json` |
| 11 | Export | workbench | graded papers, `marks.xlsx`, QQI records |
| 12 | Archive | workbench | one archive with checksums and a delete-after date |

### 3.1 Where a teacher's papers live

- **A `private/` folder that git ignores**, in a clone of the public repository, suits only a careful programmer: `git add -f`, a mistyped rule or a copied command publishes a live paper, and a published commit stays reachable after its branch is deleted (`../extraction.md`, §0).
- **A separate private GitHub repository** gives history and sharing, but needs git, and GitHub is not a college-approved store for personal data.
- **The teacher's own storage** (college OneDrive, network home drive, laptop) needs no git; the studio reads and writes it directly.

**Recommendation:** teachers use their own storage. Josh keeps paper *sources* in a private repository such as `deweydex/dewmark-papers`, and `private/` in the public clone only as ignored scratch space with CI's `privacy` job behind it. **Submissions and marking records live only in college-approved storage**; QQI's guidelines (§4.2.6) treat them as personal data kept "until appeals processes are exhausted".

The studio proposes one **paper folder** per paper:

```
PDP 5N2927 Sample/
  pdp-5n2927-sample.exam.md          ← the only file the teacher writes
  pictures/   data/
  issued/2026-10-20 Group A/         ← exactly what was given out; never rebuilt
  submissions/2026-10-20 Group A/    ← personal data
  marking/2026-10-20 Group A/        ← record and exports, apart from submissions (fixes ../code.md bug G)
  names.lock.json                    ← written at first issue (section 6)
```

### 3.2 Open, write and convert (stages 1–3)

The studio's home (see the mockup) offers **Continue** (recent paper folders with their state: draft, issued, being marked), **New paper**, **Open a paper**, **Convert a paper**, and **Mark submissions**, which leads to the workbench. A status line reads "Builder ready · works offline", beside one sentence: *"This page came from the internet; your papers never go back to it."* The page enforces that itself: its content security policy (a rule telling the browser which addresses a page may contact) allows only its own address, plus a local model server if the teacher turns the assistant on. Folders are remembered through the **File System Access** API, which lets a page read and write a folder the user picks; Chrome and Edge have it, and Firefox and Safari fall back to opening single files and downloading results.

The exam file stays the single source: plain text that any editor can open, that can be emailed, and that a language model can produce. The studio makes the text pleasant rather than hiding it behind a form. **New paper** starts from a template (a Python practical from the PDP Sample, a maths paper, a science paper, an essay paper, or blank). The editor is dewlab's CodeMirror 6 with an **Insert** menu holding one ready snippet per question type from the type registry (`question-types.md`), so nobody types a type name from memory. An outline lists sections, questions and a running marks tally against the stated total. A form-based "guided" mode writing the same file waits until the format settles.

**Convert** comes in two kinds. **From a PDP page, first:** a deterministic converter of about 150 lines, reusing the PDP page's own patterns (`../pdp-pages.md`, §9.3), writes the exam file and marks what it cannot know (marking schemes, model answers) as `draft`, which the check will not let into an exam issue. **From Word or PDF, later:** a local model drafts the file and the builder's check loops over it until it passes (`assistant.md`); with no model, the studio packages the same instructions to paste into whatever tool the ETB allows and checks the pasted reply the same way.

### 3.3 Check, and sit it as a student (stages 4 and 5)

About 400 ms after typing stops, the studio's background Python worker runs the builder's checks and rebuilds the preview. At 45–180 ms a build, this feels immediate, and typing never waits. Problems appear in the builder's own words, each linked to its line; the builder already reports every problem at once (`BuildError`, `build_exam.py:100`). Step 3 adds a stable code to each, such as `marks-dont-add-up`, linking it to a help page.

A **Before you issue** list gates the Issue button: checks pass; no `draft` remains; every picture has a description; no locked answer name has changed; and "I have sat this paper myself", which only the teacher can tick. The preview is the real built page, switchable between Student, Practice, Answer key and Print. **Sit it** opens it full-window in a sandboxed frame with no access to real storage, so a teacher's attempt cannot collide with a student's. One click opens that attempt in the workbench, testing the marking scheme against a real submission: the "single most effective check an exam gets" (`THE_EXAM_BUILDER.md`, §1).

### 3.4 Issue (stage 6)

**Issue** asks four questions, each with a default:

1. **What kind of paper?** Exam, practice or sample: sets the band and whether hints survive.
2. **Which sitting?** For example "2026-10-20 Group A": it goes into the folder, the page and every submission.
3. **How does Python reach the room?** Asked only for papers with code.
   - **Inside the file** (recommended): about 17 MB for plain Python with `sqlite3`, verified offline; nothing else to copy.
   - **In a `python` folder beside the file**, for numpy, pandas or matplotlib (about 30 MB more). The page loads only the packages the paper names, and papers on one drive can share the folder.
   - **From the internet**, for practice at home. Not for a room: twenty PCs fetching about 20 MB in the same minute is what the PDP pages depended on (`../pdp-pages.md`, §7).
4. **How will students get it?** Moodle, shared drive or USB: changes only the sitting card's wording.

dewmark writes `issued/<sitting>/` (student, practice if asked, answer key, marking scheme, `room-check.html`, and `sitting-card.html`: one printable page for the invigilator with the paper, its fingerprint, how to open it, what to do after a crash, and the hand-in steps) and writes or updates `names.lock.json`. The summary shows sizes and the paper's **fingerprint**, a short code such as `7KQ-4MD` that students also see in their finish-screen receipt.

### 3.5 Prepare the room, give it out, collect (stages 7–9)

`room-check.html` uses the same Python delivery as the paper. Opened on a PC beforehand, it takes about 30 seconds and shows green, amber or red, with a plain fix, for the browser version, Python starting with the network off (and how long it took), `input()` (Chrome and Edge 137 or later, otherwise a pop-up fallback), Stop, save-to-file, browser storage and screen size. It replaces "open each machine the day before" and hoping the cache holds. A tested Safe Exam Browser profile (`../exam-types.md`, §5) comes later.

- **Moodle:** upload the student file as a File resource with display "Force download", so every student opens their own downloaded copy; hand-in is an assignment.
- **Shared drive or USB:** copy the issued folder; students double-click; hand-in goes to a drop folder or Moodle.
- **Collecting:** the workbench takes Moodle's "Download all submissions" zip as it comes (compressed, so it needs the browser's `DecompressionStream`; today only uncompressed zips are read, `../code.md`, §3) or a folder. It logs each as received, with file name, checksum, time and fingerprint match: the evidence-received record of QQI §4.2.7.

### 3.6 Mark, export, archive (stages 10–12)

Marking views, blind marking, keyboard entry, re-running Python and hidden tests belong to the workbench design (`question-types.md`: "assisted, never automatic"), and the optional assistant to `assistant.md`. The architecture sets three rules: a person enters or confirms every mark; the record names the marker and date of every change; and nothing in a submission is ever run except student code, inside the Python worker.

| Export | First | Later |
|---|---|---|
| Graded papers | One combined print document, each student starting a new page with name, number, paper and fingerprint on every page: one print, one PDF. Plus a zip of per-student HTML papers for Moodle's "Upload multiple feedback files in a zip". | One PDF per student, which needs a layout engine for maths and code; wait until asked. |
| Marks | `marks.xlsx` from a small writer (an xlsx file is a zip of XML, and the workbench already writes zips): **Results** (learner number, name, per-question marks, total, percentage, band, weighted mark), **Columns explained**, **Received**, **Marking log**. CSV stays. | A **Learning outcomes** sheet once the format has `outcomes` (`../exam-types.md`, §4). |
| QQI records | Results in the column order of the college's results return (Josh to supply the template). | An internal-verification pack: sampled graded papers, scheme, marks and log in one zip. |

**Archive** writes one file per sitting (the exam file, the issued folder as issued, submissions, record, exports, a checksum manifest) and asks for a delete-after date set by college policy.

---

