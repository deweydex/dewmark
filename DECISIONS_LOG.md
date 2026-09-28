# Decisions log

Numbered decisions, each with what was decided, why, and what changing it
would cost. Code comments and documents cite entries by number. When an
open question in `planning/OPEN_QUESTIONS.md` is settled, the answer goes
into the relevant design document and the decision is recorded here.

The design round of September 2026 produced 33 decisions, recorded in full
in `planning/DECISIONS_2026-09-27.md`, with the reasoning in
`planning/PROPOSAL.md`. The entries below record the ones that shape the
repository itself; the rest take entry numbers here as the steps that
depend on them land.

---

**0.1 — dewmark leaves dewlab, with its history.** dewmark was built as
the folder `dewmark/` inside deweydex/dewlab (first commit 2f23c03d,
2026-08-31; last change 87e465f6, dewlab#181). In September 2026 it moved
here. The history was extracted from dewlab's `main` at f22d0d4f with
`git filter-repo --subdirectory-filter dewmark --prune-degenerate always`
and the commit callback kept in `dev/history/dewlab-import-callback.py`,
giving eight linear commits whose tree is byte-identical to dewlab's
folder. Each imported commit carries an `Imported-from:
deweydex/dewlab@<sha>` trailer, and pull-request numbers in subjects read
`deweydex/dewlab#N`, so GitHub links them to the repository they belong
to. The move changed no behaviour: the only edits were command lines that
lost their `dewmark/` prefix, sentences that said dewmark lives inside
dewlab, and the new root files. dewlab keeps a redirect at its old
`/dewmark/` address to this repository's home page (decision 4 of
2026-09-27). The pull request that brings the history in must be merged
with a merge commit: a squash or rebase would flatten or rewrite the
imported commits. *Changing it:* the move is one-way; reversing it would
mean another extraction.

**0.2 — The licence is dewlab's own terms**, adapted to name this
repository (`LICENSE.md`; decision 1 of 2026-09-27): personal use and
adaptation with credit, classroom use after getting in touch, no
commercial use. The standard alternatives considered, PolyForm
Noncommercial with CC BY-NC-SA and EUPL or MIT with CC BY, are set out in
`planning/PROPOSAL.md`. *Changing it:* easy while J. S. Aaron is the only
copyright holder; harder once anyone else's contribution is accepted.

**0.3 — What dewmark takes from dewlab is copied, never linked**
(decision 31). A copied file records the dewlab commit it came from and
its checksum, and a CI check refuses a copy edited by hand. An exam must
never depend on dewlab's site being up or unchanged. *Changing it:*
linking would save duplication and make every sat paper hostage to
dewlab's next change.

**0.4 — Real papers and submissions are never committed.** The repository
is public. Real exam content is secret before it is sat, and submissions
are personal data always. `.gitignore` keeps out `private/`, `*.zip` and
`dewmark_*` (the prefix of submission and marking-record names). The four
PDP 5N2927 papers in `experiments/pdp-5n2927/` are trial runs Josh has
cleared for the repository and the site (decision of 2026-09-27), and the
two recreated real papers in `samples/` will not be reused as live exams
(decision 3). *Changing it:* not an option for real papers.

**0.5 — The research behind the design round is kept in history, not on
`main`** (decision 2). The seven research reports, four designs, three
format proposals, the review, screenshots and probe scripts were removed
from `main` once `planning/PROPOSAL.md` and `docs/EXAM_FORMAT.md` existed.
They remain in history at commit `b3823f91799f` (the last commit that
holds them), and the proposal's links point there. A tag,
`design-round-2026-09`, can be added to that commit from any clone with
push rights.

**0.6 — Step 2: the page writes only once the student is in, and each
page of an exam keeps its own saved work.** The code audit found four
ways the drafts lost or mixed up answers, and a browser rehearsal in
`tests/browser/test_saving.py` now reproduces each (every one failed
before the fix):

- *A reload, a closed tab, or Begin on the start screen wiped the
  saved work being offered for restore*, because the unload handler and
  the first save wrote the start screen's blank state. Now nothing is
  written until Begin or Continue (`canWrite`), and Begin with saved
  work present asks first and copies the earlier work to
  `dewmark:<exam code>:<page>:set-aside:<time>` before starting afresh:
  set aside, never deleted.
- *The student paper, the practice paper and the answer key shared one
  save slot* (`dewmark:<exam code>`), so a practice attempt was offered
  as the student's exam work. Each page now has its own
  (`dewmark:<exam code>:<page>`), the saved record names its page, and
  the answer key saves nothing at all. Work in the old shared slot is
  no longer offered; no class had sat a dewmark paper.
- *A second window, told it "will not save", still wrote over the first
  window's work when it closed.* It now never writes.
- *The workbench counted the marking scheme and its own marking record
  as students* when they sat in the submissions folder, and it saves the
  record into that folder itself. It now skips any file that is not a
  submission, by name and by content, and says which it skipped.

With the shared slot gone, the site publishes each sample's practice
version and answer key again. *Changing it:* the per-page key is part of
the saved-data contract from now on; renaming it strands saved work.

**0.7 — The reader for the new exam format, and where it departs from the
format's text.** Step 3 begins with `dewmark/reader.py`, which reads a
file in the format of `docs/EXAM_FORMAT.md` into its settings, sections,
questions, parts, answer boxes with their permanent names, and marking
scheme, with a coded message for every problem. It grew from the format
judge's prototype (`unified.py`, kept in history with the research) and
is tested with the judge's hostile cases (`tests/test_reader.py`). The
four PDP papers convert with `dewmark/convert_pdp.py` and read with no
problems; the converted files are in `samples/pdp-5n2927/`, each with a
marking-scheme skeleton of `(draft)` entries to fill.

Two departures from the format's text:

- *Structure is read line by line, not with markdown-it-py.* §4.1 says
  one CommonMark reader in pure Python reads the file. The reader follows
  CommonMark's fence rules (a fence closes on a line of at least as many
  of its own character, so four backticks hold a three-backtick listing)
  but reads headings, fences and scheme lines itself, with only Python's
  standard library, so nothing need be installed for the studio to run it
  in the browser. A CommonMark renderer is still the plan for turning
  prose into the page, in step 4.
- *A key for a word bank or a drop-down needs one choosable answer, not
  all.* §5(c) says "every keyed label in 5(d) is in its bank", but its own
  key for 5(d) accepts "vacuole / large vacuole / permanent vacuole"
  against a bank offering only "vacuole". The reader refuses a key none of
  whose alternatives a student could choose, and leaves harmless extra
  alternatives alone.

*Changing it:* the names this reader makes (`dewmark/numbers.py`) become
the keys saved answers are stored under once a paper in this format is
sat; changing how a printed number becomes a name after that strands
saved work, which is what the names lock, next, will enforce.

