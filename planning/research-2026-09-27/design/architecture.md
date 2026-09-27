# dewmark's architecture and the teacher's journey

*Design round, 2026-09-27. Topic: the move out of dewlab, sharing code with dewlab, the teacher's journey from a blank page to an archived sitting, and the architecture that serves it. The companion mockup is [`../../mockups/teacher-studio.html`](../../mockups/teacher-studio.html). The exam file grammar, the student's start flow, the question types and the language-model assistant each have their own design document in this folder (`format.md`, `student-flow.md`, `question-types.md`, `assistant.md`). This document refers to them rather than repeating them.*

## What this recommends, in brief

1. **Move first, and change nothing else while moving.** The rehearsed extraction in `../extraction.md` becomes step 1. dewlab keeps a redirect at its old `/dewmark/` address and one line in its README.
2. **Licence dewmark under PolyForm Noncommercial 1.0.0**, with the documents and samples under CC BY-NC-SA 4.0. This keeps dewlab's "no financial gain" line in standard wording, and drops the "get in touch before classroom use" gate, which does not suit a tool meant for any teacher. Josh decides.
3. **Share code with dewlab by copying, never by linking.** Each copied file is recorded with its dewlab commit and a checksum, and CI refuses a copy that has been edited by hand. Files that are reworked rather than copied carry a banner naming their source.
4. **One builder, two front doors.** The Python builder stays the single implementation. It runs from the command line for Josh and CI. It also runs unchanged inside a browser page, the **studio**, where a teacher writes, checks, previews and issues a paper. I tested this: all five samples build **byte-identically** in the browser and on the command line.
5. **A Python exam can be one file, or one file and a folder, with no server and no internet.** I tested both: Python boots from a double-clicked page with the network switched off in about 2.5 seconds, making zero network requests.
6. **Three pages, two audiences.** The studio (writing and issuing) and the workbench (marking) are teacher pages. The exam page is the student page and never contains teacher code. A teacher opens the teacher pages from a web address or from a downloaded folder by double-clicking. A student opens the exam page from a file.
7. **Versions are recorded, never guessed.** The exam format, the tool, each built page, each submission and the marking record all carry a version. A **names lock**, written when a paper is first issued, makes the stable-names contract something the builder enforces rather than a rule people remember.

---

## 0. What I tested for this design

Section 4's choice depends on two untried questions: can the existing builder run inside a browser, and can a double-clicked page load Python with no internet? I ran four probes in headless Chromium 141 with Pyodide 0.28.3 (**Pyodide** is the Python interpreter compiled to run inside a web browser). The appendix says how to re-run them.

| Probe | What it did | Result |
|---|---|---|
| Builder in the browser, served over http | Loaded Pyodide and three **wheels** (Python package files): PyYAML 6.0.2, Markdown 3.11, latex2mathml 3.81.1. Copied `build_exam.py`, its assets and the five samples into Pyodide's in-memory disk and ran `build_exam.build()` on each. | All **20 output files byte-identical** to CPython 3.11's. 45–180 ms per build (26–126 ms on the command line). Python ready in 2.1–3.1 s; the wheels add 310 KB. A broken sample gave the builder's own messages word for word (*"total_marks says 99 but the paper adds up to 50…"*). |
| The same page, double-clicked | Opened from a `file://` address, as a double-clicked file is. | **Fails**: Chromium refuses to fetch `pyodide.asm.wasm` from a neighbouring folder (*"Cross origin requests are only supported for … http, https"*). |
| Python inside one file, network off | Pyodide's core written into the page as base64 text, booted in a background worker made from inside the page, which answers Pyodide's file requests from that copy. Opened from `file://`, browser offline. | **Works.** 16.4 MB page (17.1 MB with `sqlite3`); Python ready in 2.3–2.9 s; ran a `sqlite3` query; **no** network requests attempted. |
| Python beside the page; then the studio | A 3 KB page with a 17.1 MB `python/payload.js` beside it, loaded by an ordinary script tag. Then a 171 KB studio page carrying the builder, loading Python the same way. | **Both work**, offline from `file://`. Python ready in 2.5 s; the studio built the mixed sample 3.6 s after opening, byte-identical to the command line. |

The last two results matter most. The engine probe (`../dewlab-runtime.md`, §2) showed a background worker can start from `file://`, but not where Python itself could come from. Browsers forbid a double-clicked page to *fetch* a neighbouring file but allow it to *load a script* from one, so packaging Pyodide as a script closes the gap. The loader is about forty lines:

```js
// inside the worker: Pyodide asks for files at a made-up address; answer from memory
self.fetch = (url, opts) => String(url).startsWith(BASE)
  ? Promise.resolve(new Response(files[String(url).slice(BASE.length)],
      {headers: {"Content-Type": String(url).endsWith(".wasm") ? "application/wasm" : "application/octet-stream"}}))
  : realFetch(url, opts);
importScripts(blobUrlOf(files["pyodide.js"]), blobUrlOf(files["pyodide.asm.js"]));
const py = await loadPyodide({indexURL: BASE, packageBaseUrl: BASE,
  lockFileContents: text(files["pyodide-lock.json"]), stdLibURL: BASE + "python_stdlib.zip"});
```

**What these probes do not show.** Everything ran in Chromium on Linux. Edge on the college's Windows PCs is also Chromium but is unverified; Firefox and Safari were not tried; speed and memory on a five-year-old college PC are unknown. The room check (section 3.5) measures this on the room's own machines.

---

## 1. Step 1: the move

The move is mechanically cheap: 8 commits, 40 files, no code changes, tests passing unchanged (`../extraction.md`, §3). Do it *alone*, as a pure move, so every later change is its own reviewable diff rather than hidden inside a 40-file import.

### 1.1 Three things to settle first

1. **The licence** (1.4). Files leaving dewlab leave its `LICENSE.md`, and a public repository with no licence grants nobody anything.
2. **What the parked branch keeps.** Keep the seven research reports and `design/`, with a short folder README saying the reports' warnings about the 2027 paper are out of date. Move `probes/extraction/callback.py` to `dev/history/dewlab-import-callback.py` and `probes/engine/` (24 KB, the evidence for the exam engine) to `dev/probes/engine/`. Drop `shots/` (4.7 MB), the other probes, `PARKED.md` and the two `*-workflow.js` scripts; they stay in branch history.
3. **The two recreated real papers** (`samples/hvit-database-practical.exam.md`, `samples/maths-for-it-5n18396.exam.md`) include model answers and are already public. Josh confirms neither will be reused live (`../extraction.md`, §5b).

### 1.2 The procedure

Each item ends with how we know it worked.

1. **Tag dewlab:** `git tag dewmark-last-in-dewlab a6d2c6d4` (today's `main`). *Check:* the tag is on GitHub.
2. **Extract with history** from a fresh clone of dewlab's `main`, with **git filter-repo** (the standard tool for cutting one folder's history out of a repository):
   ```
   git filter-repo --subdirectory-filter dewmark --prune-degenerate always \
     --commit-callback "$(cat dev/history/dewlab-import-callback.py)"
   ```
   The callback turns `(#181)` into `deweydex/dewlab#181` so GitHub links the right pull requests, and adds `Imported-from: deweydex/dewlab@<sha>` to each commit. *Check:* 8 linear commits, 40 files, 18 tests pass, five samples build.
3. **Merge into dewmark** on branch `import-from-dewlab` with `git merge --allow-unrelated-histories`, taking the incoming `README.md` whole.
4. **One fix-up commit:** drop the `dewmark/` prefix from about 12 command lines (`../extraction.md`, §2), including the teacher-visible error at `build_exam.py:416`; rewrite four "lives inside dewlab" sentences as "began inside dewlab"; fix the experiments count; add `LICENSE.md`, `THIRD_PARTY_NOTICES.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `DECISIONS_LOG.md`, `.gitignore`, `.gitattributes`, `pytest.ini`; pin `requirements.txt` to exactly the versions the browser loads (`markdown==3.11`, `PyYAML==6.0.2`, `latex2mathml==3.81.1`) with pytest and Playwright in `requirements-dev.txt`; add `tests.yml` and `deploy.yml`.
5. **Merge the pull request with "Create a merge commit"**; squash or rebase would flatten the imported history. *Check:* `git log --follow build_exam.py` shows the dewlab-era commits.
6. **Merge `main` into the parked branch** (rehearsed clean), apply 1.1's keep/drop list, merge it.
7. **Turn on Pages** (Settings → Pages → Source: GitHub Actions). *Check:* `/dewmark/`, `/dewmark/workbench/` and `/dewmark/samples/` load.
8. **Remove dewmark from dewlab** in one pull request, merged only after step 7, using the rehearsed diff (`../probes/extraction/dewlab-removal.diff`): `git rm -r dewmark`, the redirect stub and its test, the `normalise_svg.py` exclusion, the `dewmark:` CI job and any required-check setting naming it, the README row, a link in `WRITING_TUTORIALS.md:801`, and a dewlab `DECISIONS_LOG.md` entry. *Check:* dewlab's tests and build pass; the old address redirects.

The two data-loss bugs (`../code.md` A: a reload on the start screen wipes saved answers; B: practice and exam share one save slot) are **not** part of the move. They are step 2, and must be fixed before any class sits a dewmark paper.

### 1.3 What dewlab keeps

- **A redirect, not a copy,** at `deweydex.github.io/dewlab/dewmark/`, to `deweydex.github.io/dewmark/workbench/`. The address has been live since 2026-09-03 and may be bookmarked. The stub follows dewlab's `compose/dewmini.html` pattern (`location.replace` keeping query and hash, a meta refresh, `noindex`).
- **One sentence in the README** and one link in `WRITING_TUTORIALS.md`. Nothing on the student-facing contents page: dewlab speaks to students, dewmark to teachers.
- **Entry 7.179 unchanged,** as history.
- **A shared vocabulary, recorded in both logs.** dewlab's `question` fence and dewmark share type names (`multiple-choice`, `fill-in-the-blank`) and `{word}` gaps, so a tutorial self-check can move into a practice paper unchanged. A small dewmark test keeps the names spelled the same. Words are shared; code is not.

### 1.4 The licence

| Option | What others may do | How it fits dewmark |
|---|---|---|
| **A. dewlab's `LICENSE.md`, renamed** | Personal use; adapt with credit; classroom use "get in touch first"; no commercial use; "All rights reserved". | Consistent with dewlab. But custom text that an ETB's IT or data-protection officer cannot look up, and the get-in-touch clause makes every teacher elsewhere ask before starting. |
| **B. PolyForm Noncommercial 1.0.0** (code), **CC BY-NC-SA 4.0** (documents, samples) | Any non-commercial use; "educational institution" and "government institution" are named as permitted "regardless of the source of funding"; no selling without permission; credit required. | Keeps what dewlab's licence protects, in standard wording, without the gate. Cost: not "open source" by the OSI definition, so some contributors will not take it; private training providers still ask. |
| **C. EUPL-1.2 or MIT** (code), **CC BY 4.0** (documents) | Anything, including commercial use (EUPL keeps changed versions under EUPL, even when hosted). | Widest uptake and contribution; EUPL has an official Irish text. Cost: a company may sell or host it. |

**Recommendation: B.** dewlab's licence shows two firm values (credit, no financial gain) and a wish (knowing who uses it). B keeps the values; the wish becomes a request in the README. Decide before accepting anyone else's pull request, while Josh is the only copyright holder. Two consequences: `LICENSE.md` says files under `vendor/dewlab/` come from dewlab and are licensed on dewmark's terms (Josh owns both); and `THIRD_PARTY_NOTICES.md`, and every built page, must credit what they bundle: Pyodide (MPL-2.0), CodeMirror (MIT), Lexend and OpenDyslexic (SIL OFL), Python-Markdown (BSD-3-Clause), PyYAML and latex2mathml (MIT).

### 1.5 The decision log

`DECISIONS_LOG.md` in dewlab's shape: numbered entries that code comments can cite, each saying what was decided, why, and what changing it would cost. It opens with:

- **0.1** dewmark leaves dewlab: filter-repo, 8 commits, `Imported-from` lines, the dewlab tag.
- **0.2** The licence.
- **0.3** Sharing with dewlab: copies with a stamp, ports with a banner, never a live link (section 2).
- **0.4** The four PDP 5N2927 papers are cleared trial runs and public. Real papers and submissions are never committed.
- **0.5** One builder, two front doors (section 4).
- **0.6** How Python reaches an exam room: inside the file, in a folder beside it, or from the internet (section 3.4).
- **0.7** Versions and the names lock (section 6).

`OPEN_QUESTIONS.md`'s rule, that a settled question gets a log entry, finally has a log to point at; until now it pointed at dewlab's, which has no dewmark entries.

### 1.6 CI

**CI** (continuous integration) is the set of checks GitHub runs on every change. `tests.yml` has six jobs:

| Job | What it proves |
|---|---|
| `unit` | `pytest tests`: the builder's checks and messages |
| `samples` | every sample builds twice with identical output, so a one-question edit shows as a one-question diff |
| `builder-in-browser` | the same builds inside Pyodide (Node with the pinned `pyodide` package) give byte-identical output. This keeps "two front doors" true. |
| `vendor-current` | copies from dewlab match their checksums, and bundles match their sources (dewlab's `standalone-bundle-is-current` rule) |
| `rehearsals` | the browser rehearsals in `dev/`, network blocked. dewlab keeps these manual; dewmark cannot, because its worst bugs live in the page (`../code.md`) |
| `privacy` | nothing under `private/`, no `*.zip` or `dewmark_*` file, no `.exam.md` outside `samples/` and `experiments/`: a second lock behind `.gitignore`, which `git add -f` defeats |

### 1.7 GitHub Pages

`deploy.yml` builds the site on every push to `main`:

```
/dewmark/                    home: what dewmark is; Studio, Workbench, Try a sample
/dewmark/studio/             the studio (installable; works offline after the first visit)
/dewmark/workbench/          the marking workbench
/dewmark/samples/            every sample built: student, practice, answer key
/dewmark/experiments/        the hand-built papers as they were, including the four PDP papers
/dewmark/download/           dewmark-<version>.zip: studio + workbench + Python, for double-click use
/dewmark/v/<version>/        each release's studio and workbench, kept for reproducibility
```

Pages serves dewmark from **the same browser origin as dewlab** (`deweydex.github.io`), so they share browser storage: every key and database name starts with `dewmark`, and the offline cache (a **service worker**, a script the browser keeps to serve a site's files without a network) is scoped to `/dewmark/`. A custom subdomain, one DNS record, would separate them if needed.

### 1.8 The repository after the move

Straight after step 1: dewlab's `dewmark/` folder plus the new root files.

```
LICENSE.md  THIRD_PARTY_NOTICES.md  README.md  CLAUDE.md  CONTRIBUTING.md  DECISIONS_LOG.md
.gitignore  .gitattributes  pytest.ini  requirements.txt  requirements-dev.txt
build_exam.py  assets/  workbench/  samples/  experiments/ (+ pdp-5n2927/)
docs/  planning/ (+ research-2026-09-27/, design/, mockups/)  tests/  dev/
.github/workflows/{tests,deploy}.yml
```

`.gitignore` covers `__pycache__/`, `/site/`, `/out/`, `/finished/`, `/private/`, `/vendor/pyodide/`, `*.zip` and `dewmark_*`. After the studio lands (step 3):

```
dewmark/                 the builder as a package: core.py (pure: text in, pages out), check.py,
                         render.py, types/ (one module per question type), cli.py
build_exam.py            a three-line shim, so `python build_exam.py exam.md` keeps working
runtime/                 the exam page's own code: engine.js, page.js, page.css, exam_tools.py
studio/                  index.html, studio.js, studio.css, worker.js, sw.js, manifest.webmanifest
workbench/               index.html, workbench.js, workbench.css
vendor/dewlab/           SOURCE.json and the files copied from dewlab
vendor-src/              editor bundle sources, package.json, package-lock.json
tools/                   sync_from_dewlab.py, fetch_python.py, make_download.py
pins.json                Pyodide version and every wheel with its checksum, in one place
```

dewlab repeats its Pyodide version in five places (`../dewlab-runtime.md`, §2); `pins.json` makes it one.

---

## 2. Sharing code with dewlab

**The rule, from the dewstack precedent:** dewstack took "dewlab's design, not its code", carried some files over whole, ported the engine "in shape", kept "no twinned files", and noted "the dewlab commit each copy was taken from so a later sync is possible" (`dewlab/staging/dewstack-import/planning/CONSOLIDATION_PLAN.md`, §8, item 9). dewmark adopts it, enforced by a checksum instead of by memory.

An exam page must never depend on dewlab at run time: rooms may have no internet, and dewlab changes weekly (8 engine commits in 15 days). Submodules fail for teachers because GitHub's "Download ZIP" leaves them out, and publishing a package needs a release pipeline dewlab lacks. So dewmark keeps **copies** of two kinds:

- **Verbatim copies** under `vendor/dewlab/`, each with a sha256 checksum in `vendor/dewlab/SOURCE.json`; CI fails on any mismatch, which catches a hand edit.
- **Ports in shape**, rewritten for exams, each with a banner such as `// Ported in shape from dewlab assets/pyodide-engine.js @ a6d2c6d4; see DECISIONS 0.3`. `SOURCE.json` records the upstream file's checksum at porting, so later upstream changes can be reported.

```json
{
  "repository": "deweydex/dewlab",
  "commit": "a6d2c6d4",
  "taken": "2026-10-04",
  "copies": [
    {"from": "assets/vendor/fonts/lexend-latin-400.woff2",
     "to": "vendor/dewlab/fonts/lexend-latin-400.woff2", "sha256": "…"}
  ],
  "ports": [
    {"from": "assets/pyodide-engine.js", "to": "runtime/engine.js", "upstream_sha256": "…"}
  ]
}
```

**Which files, and when** (from `../dewlab-runtime.md`, §11, ordered by the step that needs them):

| dewlab file | Kind | dewmark use | Step |
|---|---|---|---|
| `dev/fetch_pyodide.py` | copy, then extended | `tools/fetch_python.py`: download the pinned Pyodide release and check it against `pins.json`; write the in-page and beside-the-page Python packages | 3 |
| `compose/dewmini-fs.js`: folder handle kept in IndexedDB, permission re-asked on a click | port | the studio's "recent papers"; the exam page's save-to-file reconnecting after a reload | 3 |
| `vendor-src/codemirror-entry.js` (CodeMirror 6 at dewlab's pins) | copy of the source, bundled by dewmark's own `vendor-src/` | the studio's editor, and the exam page's code editor with a "no suggestions" switch | 3 (studio), 4 (page) |
| `assets/vendor/accessible-fonts.css`, Lexend 400/700, OpenDyslexic 400/700 roman and italic | copy | the student's reading settings, inlined only when the exam offers them | 4 |
| `assets/tutorial-style.css`, lines 1–165 (tokens and the `data-theme`/`data-font`/`data-contrast` attributes) | port | one visual system for the studio, workbench and exam page | 3 |
| `assets/pyodide-engine.js` and `assets/pyodide-worker.js` | port | `runtime/engine.js`: the worker created from inside the page, `input()`, Stop, a time limit, and code run as `__main__` | 4 |
| `assets/tutorial_tools.py`: `run_cell` output rendering, `_format_exception`, `compare()` | port of three functions | `runtime/exam_tools.py`, in the page and the workbench; `compare()` becomes "run the scheme's test cases beside the model answer" | 4–5 |
| `build.py` `SERVE_SCRIPT` | port, only if needed | a room server with isolation headers, for rooms whose papers need a true interrupt that keeps the program's state | later, possibly never |

**Staying current.** `tools/sync_from_dewlab.py --check` runs in CI; `--report`, run monthly by a scheduled workflow, opens an issue listing upstream changes since the stamped commit, for copies and ports alike; `--take <sha>` is run by a person who reviews the diff and logs the new stamp in `DECISIONS_LOG.md`. Syncing is never automatic, because a runtime change must be deliberate, and never urgent, because an issued page carries its own runtime (section 6).

**Traffic can run both ways.** dewlab's downloaded tutorials have no Stop and no `input()` (its DECISIONS 7.77, 7.240); the engine and the Python package verified above would fix both, under the same rule.

---

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

A **Before you issue** list gates the Issue button: checks pass; no `draft` remains; every picture has a description; no locked answer name has changed; and "I have sat this paper myself", which only the teacher can tick. The preview is the real built page, switchable between Student, Practice, Answer key and Print; while the file has a problem, it keeps showing the last version that built, with a note saying so. **Sit it** opens it full-window in a sandboxed frame with no access to real storage, so a teacher's attempt cannot collide with a student's (the page must cope with storage being unavailable, which locked-down browsers need anyway). One click opens that attempt in the workbench, testing the marking scheme against a real submission: the "single most effective check an exam gets" (`THE_EXAM_BUILDER.md`, §1).

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

## 4. The key choice: how teachers run the builder

Today the builder is a Python command-line program. Running it needs Python, `pip install` and a terminal (`docs/FOR_TEACHERS.md:59-61`), in a guide that "assumes no programming knowledge". Most teachers cannot do that, and ETB-managed PCs often block installing Python at all.

| | A. Command line only | B. Studio running the same Python builder in the browser | C. Rewrite the builder in JavaScript | D. A desktop app (installer) |
|---|---|---|---|---|
| A non-programmer can use it | No | Yes: a web address, or a double-click | Yes | Only where installs are allowed |
| Works with no internet | Yes | Yes (verified, section 0) | Yes | Yes |
| One implementation of the checks | Yes | **Yes: the same file, byte-identical output (verified)** | No, unless Python is dropped, and `OPEN_QUESTIONS.md` Q10 rules out a second implementation | Yes |
| Cost to build | None | Moderate: a core function that takes text and returns pages, a worker, the studio page, a CI parity job | High: 1,344 builder lines and 323 test lines rewritten; JavaScript Markdown, YAML and MathML libraries give different output | High: packaging, code signing, updates per operating system |
| Weight | None | 12.4 MB once from the web (cached), or 17 MB on disk in the downloaded folder | About 0.3 MB | Tens of MB, installed |
| First start | Instant | About 2–3 s while Python starts (verified) | Instant | Instant |
| Risk | Excludes most teachers; Josh becomes the builder for everyone | The two front doors could drift, which the CI job catches; Chromium-first file access | Two sets of behaviour; YAML and Markdown edge cases differ | Blocked on college PCs |

**Recommendation: B, one builder with two front doors.** It is the only option that is easy for teachers *and* keeps one set of checks, and it is no longer a guess: the unchanged builder produced identical bytes in the browser for every sample, in about a tenth of a second, from a double-clicked page with the network off. What it costs:

1. **A pure core**: `build(files: dict[str, bytes], exam: str, options) -> Result` returns pages, scheme, names and problems (`{line, code, message, help}`) and never touches a disk. The command line and the studio become thin wrappers that read and write files their own way. About a day's work: the builder touches the disk in only four places, all through `pathlib`.
2. **A discipline**: the builder uses only what Pyodide provides (no subprocesses, threads or network), enforced by the `builder-in-browser` job.
3. **Identical versions** of Markdown, PyYAML and latex2mathml on both sides, from `pins.json`. My run matched across PyYAML 6.0.1 and 6.0.2, but a match should come from pins, not luck.
4. **Weight on first use**: 12.4 MB from Pages, kept by the service worker, or a 17 MB `python/payload.js` on disk in the downloaded folder.
5. **A studio page to maintain**: plain JavaScript, no framework, dewlab's CodeMirror and visual tokens.

The command line stays, for Josh, CI and anyone who prefers a terminal, with exactly the same abilities.

---

## 5. How the studio, the exam page and the workbench relate

**Three pages, two audiences.** They are not one app and not one file.

- **The exam page** is built, is one file (or a file and a `python` folder), and is all a student ever opens. It holds no model answers, marking material or teacher code, and its content security policy allows no network connections (only the `data:` and `blob:` addresses its in-page Python loader uses). dewlab's `question` fence keeps answers in the page, which its own log calls "wrong for anything that has to keep its answer from a reader who opens the page's source" (DECISIONS 7.179); the exam page shares no code path with the tools that hold answers.
- **The studio**: writing, checking, previewing, issuing, converting, room checks. Always needs Python.
- **The workbench**: marking, exports, archive. Needs Python only to re-run code or hidden tests, and opens without it for written papers.

The two teacher pages share one visual system, one set of teacher settings (marker name, recent folders, assistant connection), the paper-folder convention and the Python worker file, and link to each other (**Mark this paper**). They stay separate because their risks differ: the workbench holds personal data and must open instantly, even on a day the studio has a bug.

**How each is opened:**

| | From the web | From the downloaded folder | From a local server |
|---|---|---|---|
| Studio | `deweydex.github.io/dewmark/studio/`; "Install" in Chrome or Edge gives it a desktop icon; works offline after the first visit | `dewmark/Open studio.html` with `dewmark/python/` beside it (verified from `file://`, network off) | not needed |
| Workbench | `…/dewmark/workbench/` | `dewmark/Open workbench.html` | not needed |
| Exam page | only for public samples, never for a real sitting | the issued file, from a Moodle download, a shared drive or USB | optional: a Stop that keeps the program's variables (it needs headers only a server can send), or a Safe Exam Browser setup |

Both teacher routes are needed: the web address is easiest and updates itself; the downloaded folder serves a college that wants nothing hosted and a teacher at home with no connection. The same page serves both, its loader fetching Python from its own address or reading `python/payload.js` from disk depending on how it was opened. **Updates never interrupt:** the studio says "A new version of dewmark is ready. It will be used next time you open the studio" and never reloads mid-edit; `/dewmark/v/<version>/` keeps older releases.

---

## 6. Versioning

Five things carry a version, and each has one job.

| What | Where it is written | Rule |
|---|---|---|
| **Exam format** | `format: 1` in the `exam` block | A new optional key or question type does not change it; a changed meaning does. The builder reads the current and previous format, and the studio offers **Upgrade this file** as a before-and-after diff to accept. An unknown format or type is refused, never guessed. |
| **dewmark release** | Git tags `v0.x.y`; `/dewmark/v/<version>/` | 0.x while formats may change; 1.0 when the exam, submission and record formats are declared frozen (the ROADMAP's rule: freeze before a real sitting). |
| **Runtime inside a built page** | `<meta name="dewmark" content="dewmark 0.4.0; format 1; runtime sha256:…; paper 7KQ-4MD; sitting 2026-10-20 Group A">`, repeated in the embedded data | A built page carries its whole runtime and never updates itself, and is never rebuilt for the same sitting. A mid-term runtime fix means reissuing: new fingerprint, same names lock, and the workbench accepts both fingerprints for that sitting. |
| **Submission, scheme, marking record** | `format: "dewmark-answers/1"`, `"dewmark-scheme/1"`, `"dewmark-record/1"` | The workbench reads every version ever issued, tested against synthetic fixtures per version in `tests/fixtures/`. |
| **Names lock** | `names.lock.json` in the paper folder | See below. |

**The names lock** turns "stable names are a contract" into a builder check. It is written at first issue:

```json
{
  "format": "dewmark-names/1",
  "exam_code": "pdp-5n2927-sample",
  "versions": {
    "2026.10.01.1": {
      "sittings": [{"name": "2026-10-20 Group A", "paper": "7KQ-4MD"}],
      "names": {
        "q1.a": {"type": "short-written-answer", "marks": 3},
        "q1.c": {"type": "python-code",          "marks": 3},
        "q4.a": {"type": "labelled-boxes",       "marks": 6}
      }
    }
  }
}
```

After that, a build that removes, renames or retypes a locked name, or changes its marks, stops, unless the paper's `version` has changed; then the lock records the new version beside the old, and each sitting keeps its own scheme. The message is in the builder's usual voice:

> **q1.c was worth 3 marks when this paper was sat on 2026-10-20; the file now gives it 4.** Answers and marks from that sitting are stored under q1.c. If this is a new version of the paper, give it a new `version` and press Issue; the old sitting keeps its own record. If it was a mistake, change it back.

Adding a name is always allowed. dewlab learnt the same rule about cell ids the hard way; here the lock file remembers it, not the teacher.

**The fingerprint** is a sha256 checksum over the exam file and everything it embeds, shown as six characters (`7KQ-4MD`). `version` says which revision the teacher meant; the fingerprint proves which one a student sat. Browser save keys include exam code, variant, fingerprint and sitting, which closes bug B for good (detail in `student-flow.md`). **One place for pins:** `pins.json` holds the Pyodide version and every wheel's checksum, read by the builder, the studio, the packaging tool and CI.

---

## 7. What ships first, and what waits

Each step can ship on its own and has a test that shows it worked.

1. **The move** (section 1). *Done when* dewmark's CI is green, Pages serves the samples and workbench, and dewlab's old address redirects.
2. **Stop losing answers.** Fix bugs A and B; add storage keys with variant and fingerprint; add the fingerprint and the names lock to the builder; keep the marking record out of the submissions folder. *Done when* new rehearsals reproduce each bug and pass, and those rehearsals run in CI.
3. **Studio, first version, for written papers.** The pure builder core; the Python worker; the `builder-in-browser` CI job; home, editor, live check, student preview, Sit it, and Issue writing the issued folder (or a zip when File System Access is missing); the downloaded folder; the service worker. *Done when* a teacher who has never used a terminal writes, checks and issues the mixed sample's twin, watched by Josh, without help.
4. **Python in the room.** The exam engine (worker, `input()`, Stop, time limit), the three Python deliveries, and `room-check.html`, together with `student-flow.md`'s start screens. *Done when* a PDP practice paper converted to dewmark is sat on the college PCs with the network cable out.
5. **The workbench grows up.** Moodle zips, a received log, `marks.xlsx`, a combined graded-paper print, per-student HTML feedback, archive. *Done when* a mock marking session's exports are read cold by a colleague and match the QQI results template.
6. **Converters.** PDP to dewmark first, then Word and PDF through the assistant or its paste fallback. *Done when* all four PDP papers convert and pass the check, apart from their marking schemes, which are flagged as drafts.
7. **Later, when asked for:** a guided form editor, per-student PDFs, a learning-outcomes sheet and verification pack, a Safe Exam Browser profile, the room server.

---

## 8. Decisions for Josh

1. **Licence** (blocks step 1). Recommendation: PolyForm Noncommercial 1.0.0 for code, and CC BY-NC-SA 4.0 for documents and samples. The alternatives are dewlab's own terms, or EUPL/MIT for the widest use.
2. **The parked branch** (blocks step 1). Recommendation: keep the reports and `design/`; move the callback and the engine probe into `dev/`; drop `shots/`, the other probes, `PARKED.md` and the workflow scripts.
3. **The two recreated real papers** (blocks step 1). Confirm that neither will be reused as a live exam.
4. **The redirect target** (step 1). Recommendation: the workbench, because that is what the old address showed.
5. **Where papers live** (step 3's guide). Recommendation: teachers' own college storage in the paper-folder layout, and a private `dewmark-papers` repository for Josh's paper sources. Submissions never go on GitHub.
6. **One builder, two front doors** (blocks step 3). Recommendation: yes, the studio runs the Python builder in the browser.
7. **Default Python delivery for exams** (step 4). Recommendation: inside the file, with the folder beside it for heavy packages, and the internet for practice only.
8. **Browser support** (step 3). Recommendation: Chrome and Edge fully supported; Firefox and Safari "works, with downloads instead of saving to a folder". Test them at step 4.
9. **The college results template** (step 5). Josh to supply the column order the college's QA office expects.

---

## Appendix: the probes

All in `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/design-round/architecture/`. That is scratch space, so anything worth keeping should be copied into `dev/probes/` during step 1.

- `studio-probe/studio-probe.html`, `serve_probe.py`, `run_probe.py`, `compare_with_cpython.py`: the builder in Pyodide over http. Serve with `python3 serve_probe.py 8791 0`, run `python3 run_probe.py http://127.0.0.1:8791/studio-probe.html > pyodide-result.txt`, then `python3 compare_with_cpython.py` (20 of 20 identical).
- `studio-probe/wheels/`: the three wheels. The PyYAML wheel's sha256 matches Pyodide's lock file.
- `onefile-probe/make_onefile.py`, `run_offline.py`: Python inside one file (`onefile.html`, `onefile-core.html`) and beside it (`kit/exam.html` with `kit/python/payload.js`), opened from `file://` with the browser offline.
- `studio-file-probe/studio.html` with `python/payload.js` (regenerated by `make_studio_file_probe.py`): the builder running from a double-clicked page with the network off (`python3 onefile-probe/run_offline.py file://$PWD/studio-file-probe/studio.html`).
