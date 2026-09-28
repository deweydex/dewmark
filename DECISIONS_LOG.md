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
