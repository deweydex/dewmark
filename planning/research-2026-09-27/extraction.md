# Moving `dewlab/dewmark` into `deweydex/dewmark`: mechanics report

Everything below was rehearsed in `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/extraction/`. I did not edit, commit or push anything in either repo. The Git work used `--no-local` clones, and the GitHub calls only read.

## 0. Something to settle first: the 2027 paper is already on a public branch

While I was working, a commit showed up on `claude/affectionate-knuth-q7gs9j`. That branch exists in `/home/user/dewmark` and on GitHub. The commit is `54c28922`, dated 2026-09-27 12:12 UTC, and carries this session's own Claude-Session id. The public repo therefore now contains:

- `experiments/pdp-5n2927/PDP_5N2927_Exam_2027.html` and the other three PDP papers
- `planning/research-2026-09-27/probes/pdp/script-2027.js`, the 2027 paper's script extracted in full
- `shots/pdp/Exam_2027_{1,2,3}_*.png`, screenshots of the 2027 paper
- about 4.7 MB of screenshots in total, plus `PARKED.md` and probe scripts

The commit message says: *"Josh has cleared all four, the 2027 paper included, as trial runs rather than live exams."* My brief says the 2027 paper is **LIVE**. Only one of those can be true, and I can't tell which. The lead needs to confirm with Josh.

If the paper is live:
- Deleting the branch is not enough. On GitHub, a commit can still be reached by its SHA after its branch is gone, and it can be cached. Removing it properly needs a GitHub Support sensitive-data request.
- Whatever the answer, the same commit says `PARKED.md`, `shots/` and `probes/` "come out before merging". They must not reach `main`.

My extraction rehearsal was built on `7b4bf39`, dewmark's `main`, taken before `54c28922` arrived. Section 3 also shows that the import merges cleanly with the parked branch.

---

## 1. Every reference to dewmark inside dewlab, and what it becomes

`grep -rni dewmark` over dewlab, excluding `.git`, `node_modules`, `site/` and `dewmark/` itself, finds 25 lines in 8 files. A wider search for `build_exam`, `workbench` and `exam.md` found nothing new. There are no hits in `.claude/`, `.github/ISSUE_TEMPLATE/`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `CLAUDE.md`, `docs/build-explained.md` or `docs/tests-explained.md`.

| file:line | now | after the move |
|---|---|---|
| `.github/workflows/tests.yml:98-124` | a `dewmark:` job that runs `pytest dewmark/tests` and builds each `dewmark/samples/*.exam.md` | **Delete.** It moves to dewmark's own CI (section 5). If branch protection lists `dewmark` as a required check, remove it from settings too, or dewlab PRs will stall. I couldn't check this: there is no `gh` here and the MCP doesn't expose protection rules. |
| `build.py:128` | `DEWMARK_WORKBENCH = ROOT / "dewmark" / "workbench"` | Replace with `DEWMARK_HOME` (the URL) plus a `DEWMARK_REDIRECT` HTML string. |
| `build.py:7644-7646` | `copytree(DEWMARK_WORKBENCH, OUT / "dewmark")` | Write `site/dewmark/index.html` as a redirect stub. Details in section 5f. |
| `tests/build/test_site.py:637-684` | `test_the_marking_workbench_the_topic_pair_game_and_the_topic_editor_are_published…` builds a fake workbench and monkeypatches `DEWMARK_WORKBENCH` | Drop the workbench fixture. Assert the stub contains `b.DEWMARK_HOME`. Remove `workbench` from the cleanup tuple and delete the final `assert not (b.OUT / "dewmark").exists()`. Rename the test. The monkeypatch has to change in the same commit as `build.py`: `monkeypatch.setattr` raises on an attribute that no longer exists. |
| `dev/normalise_svg.py:203-204` | skips `("site/", "dewmark/")`, commented "dewmark is its own project" | Becomes `relative.startswith("site/")`. The comment loses its dewmark clause. |
| `README.md:111` | folder-table row: `dewmark/  the exam track — …` | Delete the row. Optionally add one line elsewhere: "Exams: see [dewmark](https://github.com/deweydex/dewmark)". |
| `docs/WRITING_TUTORIALS.md:801` | "that is dewmark, a separate program, for exams." | Keep the words and link the repo. |
| `DECISIONS_LOG.md:3889-3897` (entry 7.179) | prose comparing the `question` fence with "dewmark's own grammar/spec" | Leave it; it's a historical record. Add a new entry recording the move. |
| `staging/dewstack-import/planning/CONSOLIDATION_PLAN.md:443` | naming list "beside dewlab, dewmini and dewmark" | Leave. |

Related dewlab commits that mention dewmark but never touched `dewmark/`, so they stay in dewlab:
- `b94ed54c` "Publish dewmark's marking workbench at /dewmark/" (2026-09-03)
- `5060f841`, `f12d973a` (test changes)
- `f5b82c5a` (the SVG exclusion)
- `8e6ee14b` (DECISIONS 7.179)
- `cc36f1d3`

**Rehearsed.** In `scratchpad/extraction/dewlab-after` I ran `git rm -r dewmark` and applied the `build.py`, test and `normalise_svg` edits above. Then:
- `pytest tests/build` passed with no failures.
- `dev/normalise_svg.py --check` exited 0.
- `build.py --clean` wrote `site/dewmark/index.html` as the redirect.
- `tests/test_tutorial_tools.py` has one failure from a missing optional module in my sandbox. It is unrelated to this change.

## 2. Links inside `dewmark/` that break or mislead after the move

I checked 68 relative links in `.md`, `.py`, `.js`, `.css` and `.html` files, leaving out the experiments' HTML. **None of them points outside `dewmark/`.** Every `../` goes from a subfolder back to dewmark's own root:
- `docs/FOR_TEACHERS.md:22-52`
- `experiments/README.md:10`
- `planning/LESSONS_FROM_THE_EXPERIMENTS.md:10`
- `planning/THE_EXAM_BUILDER.md:104`, whose `../README.md` will point at the repo README, which is still the right target

Code paths are all relative to `__file__`: `build_exam.py:97`, `tests/test_build_exam.py:14,17`, `dev/smoke_pages.py:30,40` and `dev/smoke_python_page.py:38,49`. The code needs no changes.

What does need changing is **text that assumes the `dewmark/` prefix, or assumes dewmark lives inside dewlab**:

- **Command lines with the `dewmark/` prefix.** Drop the prefix.
  - `build_exam.py:416`: the student-visible error text `'pip install -r dewmark/requirements.txt'`
  - `docs/DEVELOPMENT.md:39-50`
  - `docs/FOR_TEACHERS.md:60`
  - `docs/FOR_TEACHERS.md:116` ("Open `dewmark/workbench/index.html`"). Also add the hosted URL here.
  - `planning/THE_EXAM_BUILDER.md:16`
  - `dev/smoke_pages.py:14`, `dev/smoke_python_page.py:14`
  - the `dewmark/` roots in the layout blocks at `README.md:112` and `docs/DEVELOPMENT.md:22`
- **Claims that dewmark lives inside dewlab.** Rewrite each as "began inside dewlab" with a link.
  - `README.md:18` ("being built inside dewlab")
  - `docs/DEVELOPMENT.md:8-17` ("lives inside the dewlab repository… could be lifted into its own repository"). This becomes simply true.
  - `planning/THE_EXAM_BUILDER.md:100` ("part of the dewlab repository")
- **Real dependencies on dewlab that need their own home:**
  - `planning/THE_EXAM_PAGE.md:162` relies on "the small helper program that dewlab already provides for its offline bundles". That program is dewlab's `SERVE_SCRIPT` (`build.py:~6309`) together with `dev/fetch_pyodide.py`. dewmark needs its own copy before any Python exam sits offline.
  - `planning/ROADMAP.md:80` and `planning/OPEN_QUESTIONS.md:9` say settled decisions are "recorded in the repository's decision log". That meant dewlab's `DECISIONS_LOG.md`, which has **no dewmark entries**. dewmark needs its own `DECISIONS_LOG.md`.
- **Fine as they are:**
  - "dewlab visual language" in `planning/APPEARANCE_AND_READABILITY.md:12-16`
  - `assets/exam-page.css:2` ("repeat the dewlab palette")
  - `build_exam.py:15`
  - The only external URL is the Pyodide CDN at `assets/exam-page.js:715` (`cdn.jsdelivr.net/pyodide/v0.27.4`).
- **Two small factual drifts to fix during the move:**
  - `README.md` says "three exams were built by hand". `experiments/README.md` says "two", and the parked PDP papers would make it more.
  - `experiments/README.md` says "only faults were fixed". PR #181 later removed 37 comment lines from each `mit-5n18396-maths.*.html`, so that sentence is no longer accurate. Either say so, or restore those two files from `25f5ce5a`.

## 3. Rehearsal: history-preserving extraction

**Source.** dewlab's `main` and the checked-out branch are the same commit, `a6d2c6d4`. There are 848 commits and the history is complete.

**Plain filter:**
```
git clone --no-local /home/user/dewlab dewlab-filtered
git filter-repo --subdirectory-filter dewmark
```
This finished in 0.2 s, giving 10 commits and a 254 KiB pack. The resulting log:
```
*   f00bfe3 Remove long/decorative comment blocks; condense maintainer docs (#181)
*   807a7eb Merge pull request #111 from deweydex/claude/dewmark-exam-tool-specs-w0ggew
|\  * 89eae18 dewmark: a biology paper and an essay paper join the samples
*   77ba38d Merge pull request #109 from deweydex/claude/dewmark-exam-tool-specs-w0ggew
|\  * f816fa8 dewmark: typeset mathematics, a calculator panel, and a stricter marking-block check
* 20be0cd dewmark: build Python code questions and recreate both real exams as samples
* f544379 Add working drafts of the exam builder, the exam page, and the workbench
* 7ba107f Rewrite the dewmark documents to stand alone, around one question-type catalogue
* 0122472 Add the corrected exam experiments to dewmark as prior art
* 4ad9a96 Add dewmark: specifications for the exam track
```
The alternative `--path dewmark/ --path-rename dewmark/:` produces a **byte-identical tree** (I diffed the `ls-tree` output). filter-repo also removes `origin` on its own, which is a useful safety net.

**Recommended variant** (`scratchpad/extraction/dewmark-history`, callback in `scratchpad/extraction/callback.py`):
```
git clone --no-local --single-branch --branch main <dewlab> dewmark-history
git filter-repo --subdirectory-filter dewmark --prune-degenerate always \
  --commit-callback "$(cat callback.py)"
```
The callback does two things:
1. It rewrites a subject-line `(#N)` and `Merge pull request #N` to `deweydex/dewlab#N`. Without this, GitHub would link `#181` to dewmark's own issue #181.
2. It adds a trailer `Imported-from: deweydex/dewlab@<original sha>` to the existing trailer block, so `Co-Authored-By` is still recognised.

The rewrite is deliberately limited to the subject line. A naive whole-message regex also rewrote "resolved one item (#21)" in #181's body, and that #21 is an OPEN_QUESTIONS item, not a PR. `--prune-degenerate always` drops the #109 and #111 merges and leaves 8 linear commits. dewlab's #96 and #101 merges were already dropped by default.

Result:
```
7505538 Joshua Aaron | Remove long/decorative comment blocks; condense maintainer docs (deweydex/dewlab#181) | deweydex/dewlab@87e465f654d6
86ad5c1 Claude | dewmark: a biology paper and an essay paper join the samples      | …@538660c64a11
… (6 more, oldest e5db6c1 "Add dewmark: specifications…" | …@2f23c03d1e7c)
```

**`--follow`:** no file was ever renamed *into* `dewmark/`. All 40 current files were created under it. The only structural churn was inside dewmark: `e997ef1a` deleted six planning docs (`COMPOSER`, `EXAM_RUNNER`, `GRADING_WORKBENCH`, `SOURCE_FORMAT`, `STYLE_AND_READABILITY`, `SUBMISSION_FORMAT`) and added the new `THE_*` set. Git sees these as rewrites even at `-M30`, not renames. So in both the original and the filtered repo:
- `git log --follow planning/THE_EXAM_FILE.md` stops at the rewrite commit.
- `build_exam.py` → 4 commits.
- `workbench/index.html` → 3 commits.
- `experiments/mit-5n18396-maths.student.html` → 2 commits.

The deleted docs remain in history, for example `git log -- planning/SOURCE_FORMAT.md`.

**Merging into dewmark** (`scratchpad/extraction/dewmark-clone`):
```
git checkout -b import-from-dewlab origin/main        # 7b4bf39
git fetch ../dewmark-history main:dewlab-history
git merge --allow-unrelated-histories dewlab-history
# CONFLICT (add/add): README.md  — "A Project on making assessments with code" vs the full README
git checkout --theirs README.md && git add README.md && git commit
```
Take the incoming README as a whole. The one-line tagline is already the GitHub repo description.

The resulting tree:
```
README.md  requirements.txt  build_exam.py
assets/(2)  dev/(2)  docs/(2)  experiments/(5)  planning/(11)  samples/(5 .exam.md)
samples/data/(3)  samples/pictures/(5)  tests/(1)  workbench/(1)
```
That is 40 files. `pytest tests` gives **18 passed**, and all 5 samples build 15 pages plus 5 marking schemes.

I then merged `import-from-dewlab` into the parked branch `54c2892`. It merged **cleanly**, because the two share no paths.

## 4. Commits that touched dewmark, and which also touched other paths

There are eight commits on `main`. `a2d68ef6` sits only on `origin/claude/remove-block-comments-liquhk` and is the pre-squash form of #181. No remote branch holds unmerged dewmark work: the two other branches that show up are only merges bringing `main` in.

| dewlab sha | subject | files | other paths |
|---|---|---|---|
| 2f23c03d | Add dewmark: specifications for the exam track | 11 | `README.md` (the folder row). The body says "A new subproject folder", which is mildly odd standalone. |
| 25f5ce5a | Add the corrected exam experiments… | 6 | none |
| e997ef1a | Rewrite the dewmark documents to stand alone… | 19 | none |
| f661c261 | Add working drafts of the exam builder… | 12 | none |
| a3a99e92 | dewmark: build Python code questions… | 20 | `.github/workflows/tests.yml` (created the CI job, which is lost from filtered history and must be recreated) |
| cbcaad71 | dewmark: typeset mathematics… | 12 | `.github/workflows/tests.yml` (added latex2mathml) |
| 538660c6 | dewmark: a biology paper and an essay paper… | 5 | none |
| 87e465f6 | Remove long/decorative comment blocks; condense maintainer docs (#181) | **101**, 8 under dewmark | ARCHITECTURE, CONTRIBUTING, DECISIONS_LOG, assets/, compose/… The ~90-line squash body describes files that don't exist in dewmark. **This is the one that reads oddly.** |

For #181, the provenance trailer is the honest fix. An optional `--message-callback` could shorten that one message to a single line pointing at dewlab#181.

## 5. What the dewmark repo needs to stand alone

**a. Licence.** dewlab's `LICENSE.md` is custom and non-OSI:
- "Copyright © 2024–present J. S. Aaron… All rights reserved"
- adapting is allowed with credit to *"dewlab… github.com/deweydex/dewlab"*
- classroom use means "get in touch first"
- no commercial use
- the terms cover "this repository and on the associated website"

Once the files move, that text no longer covers them, and a repo with no licence defaults to "no permissions granted". So dewmark needs its own `LICENSE.md`, with the credit line and repository URL renamed. Josh should make one decision here: whether "get in touch before classroom use" suits a tool whose README aims at "any teacher".

Third-party code is not vendored. Pyodide (MPL-2.0) and CodeMirror 5 (MIT) come from CDNs, and markdown, PyYAML and latex2mathml are build-time pip packages. No NOTICE file is needed yet.

**b. Content safety.**
- **`samples/data/hvit_registry.db` is synthetic.** It has 4 tables (`students` 20 rows, `courses` 10, `supervisors` 5, `labs` 4). The names come from Back to the Future ("Marty McFly", "Dr. E. L. Brown", "Temporal Engineering"), plus a few generic ones ("Irina Sokolova", "Blake Griff", "Casey Vance"). `freelist_count` is 0, so no deleted rows remain in the file.
- **Both `.xlsx` files are the same fiction.** They were generated by openpyxl on 2026-08-31.
- **Experiments.** `experiments/README.md:5-8` says these are "released past papers; committing them here breaks no rule about exam secrecy". They carry "Dublin College Dundrum" and "Aaron" branding, and they are already public in dewlab.
- **Samples.** `samples/hvit-database-practical.exam.md` and `maths-for-it-5n18396.exam.md` are recreations of those real papers, with model answers. That is fine as long as those papers are never reused. It's worth one confirming question to Josh.
- **No personal data.** There are no email addresses, and no student data beyond "student number" field labels.
- **Size.** The largest file is 112 KB and the folder is 932 KB, so there is no need for Git LFS. The parked branch's 4.7 MB of PNGs should stay off `main`.

**c. `.gitignore`** (dewlab has none of these):
- `__pycache__/`, `*.py[cod]`, `/site/`, `/out/`
- `/finished/` (the teacher guide's example output folder)
- `/dev/pyodide/`
- `/private/`: a documented place for real exams, such as a live PDP paper
- `dewmark_*`, `*.zip`: submissions are named `dewmark_<exam_code>_<number>_<name>.zip` (`exam-page.js:225-230`), which puts personal data in the filename; marking schemes and records use the same prefix

Add a `.gitattributes` copied from dewlab (`* text=auto`).

**d. Requirements.** Split `requirements.txt` in two:
- builder: `markdown`, `pyyaml`, `latex2mathml`
- `requirements-dev.txt`: `pytest`, `playwright`

That way CI and teachers don't pull in Playwright. Add a `pytest.ini` with `testpaths = tests`.

**e. CI** (`.github/workflows/tests.yml`). This is dewlab's lines 103-124 with the prefixes removed:
```yaml
on: { push: { branches: [main] }, pull_request: {}, workflow_dispatch: {} }
jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: python -m pip install -r requirements.txt pytest
      - run: python -m pytest tests -q
      - run: for exam in samples/*.exam.md; do python build_exam.py "$exam" --output /tmp/dewmark-out; done
```
The Playwright rehearsals stay manual, for the same reason given in dewlab's comment at `tests.yml:98-102`.

**f. GitHub Pages.** The repo is public with `has_pages: false`.
- Add `deploy.yml`, modelled on dewlab's: build every sample into `site/samples/`, copy `workbench/` to `site/workbench/`, and write a small `site/index.html`.
- Set Settings → Pages → Source to "GitHub Actions".
- The workbench then lives at `https://deweydex.github.io/dewmark/workbench/`.
- Because it is still `deweydex.github.io`, it is the **same browser origin as dewlab**, so localStorage is shared. The `dewmark:` key prefix avoids collisions.
- **Storage bug.** `exam-page.js:6` uses `"dewmark:" + exam_code`, and `readStoredState()` (`:232-241`) checks only `exam_code`. The `student`, `practice` and `answer_key` builds all share one `exam_code`, so a practice attempt will be offered as a restore in the real paper whenever the two share an origin. That happens on Pages, and on `file://` in Chrome and Edge. Fix this before hosting practice and student builds side by side.

**g. Should dewlab keep `/dewmark/`?** It should keep a *redirect*, not a copy.
- The address has been live since 2026-09-03, nothing links to it, and a teacher may have bookmarked it.
- Model it on the `compose/dewmini.html` redirect pattern: `location.replace(target + search + hash)` + meta refresh + `noindex`.
- I rehearsed it as a `DEWMARK_REDIRECT` string in `build.py`.
- Merge the dewlab PR only after dewmark's Pages site is live.

**h. `CLAUDE.md`,** in the shape of dewlab's:
- **Running things:** install, build a sample, pytest, the smoke scripts.
- **Rule 1:** never commit a real exam or a submission; `private/` is ignored.
- **Trap 1:** `exam_code`, question ids and `format_version` are what saved answers and marking records are keyed on, just as cell ids are in dewlab.
- **Trap 2:** the practice/student storage collision above, until it is fixed.
- **Stand-alone rule:** no imports from dewlab; the palette is copied.
- **Docs rule:** a change isn't finished until its document matches (dewlab `CONTRIBUTING.md`).
- **Student-facing strings:** these live in `build_exam.py`, `assets/exam-page.js` and `workbench/index.html`. Link to dewlab's `planning/PEDAGOGICAL_STYLE_GUIDE.md#voice` by URL.
- **Where the rest lives:** a table covering README, `docs/DEVELOPMENT.md`, `docs/FOR_TEACHERS.md` and `planning/*`.
- **Also missing:** a `DECISIONS_LOG.md` whose first entry is the move itself, citing filter-repo and the `Imported-from` trailers. `THE_EXAM_BUILDER.md:101`'s promised "companion explanation document" (`docs/build_exam-explained.md`) doesn't exist either.

## Recommended procedure

1. **Decide.** Settle the 2027 paper's status (section 0). Confirm the two real past papers won't be reused. Choose the licence wording.
2. **Tag the last dewlab state:** `git tag dewmark-last-in-dewlab a6d2c6d4` in dewlab.
3. **Extract** from a fresh clone of `github.com/deweydex/dewlab` `main` with the filter-repo command in section 3 (subdirectory filter + `--prune-degenerate always` + the commit callback). Check the result: 8 commits and a 40-file tree.
4. **Merge.** In a dewmark clone, branch `import-from-dewlab` from `origin/main` and run `git merge --allow-unrelated-histories`. Resolve `README.md` with `--theirs`.
5. **Fix up** in one follow-up commit on the same branch:
   - de-prefix the paths (section 2)
   - LICENSE, CLAUDE.md, DECISIONS_LOG.md, `.gitignore`, `.gitattributes`, `pytest.ini`
   - split the requirements
   - `tests.yml` and `deploy.yml`
   - update the README wording and the experiments count
6. **Push** the branch and open a PR. After CI is green, **merge with "Create a merge commit".** "Squash" or "Rebase and merge" would flatten or rewrite the imported history.
7. **Enable Pages** (source: Actions) and check `/dewmark/workbench/` and the sample pages.
8. **Remove from dewlab** in one PR:
   - `git rm -r dewmark`
   - the build.py redirect, the test change and the `normalise_svg` edit
   - delete the tests.yml job and remove any required-check setting that names it
   - `README.md:111`, the `WRITING_TUTORIALS.md:801` link, and a DECISIONS_LOG entry
9. **Parked branch.** Merge `main` into it (rehearsed clean), strip `PARKED.md`, `shots/` and `probes/`, and resolve the PDP question before it goes anywhere near `main`.

## What this means for dewmark

- **The move is mechanically cheap and low-risk.** dewmark was built to stand alone. It has no code dependency on dewlab, every path in its code is relative to `__file__`, and no relative link leaves the folder. The whole history comes across as 8 commits and 254 KiB, and tests and sample builds pass unchanged.
- **The real work is documentation and infrastructure,** not code:
  - about 12 lines of `dewmark/`-prefixed commands
  - four "lives inside dewlab" claims
  - a decision log that never existed
  - a licence and a CI job
  - a Pages deploy
  - a redirect in dewlab
- **Two dewlab services have to be recreated in dewmark before any offline Python exam:** the local Pyodide fetch and serve helper, and the style guide, linked or copied.
- **Three things should shape the next design work more than the move itself:**
  - The practice and real exam pages share one saved-answers slot, which breaks as soon as both are hosted.
  - A clear `private/` convention is needed for real papers, given what just landed on a public branch.
  - The licence question matters because dewmark is meant for "any teacher", not only Josh's classes.

Files to look at:
- `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/extraction/callback.py`
- `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/extraction/dewmark-history/` (the filtered repo)
- `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/extraction/dewmark-clone/` (branches `import-from-dewlab`, `parked-plus-import`)
- `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/extraction/dewlab-after/` (the dewlab removal diff, run with `git diff`)