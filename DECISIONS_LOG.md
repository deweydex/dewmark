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
saved work, which is what the names lock (entry 0.8) enforces.

**0.8 — The names lock.** `dewmark/lock.py` holds an issued paper's
names still (`docs/EXAM_FORMAT.md` §4.4). The first issue of a version
records every part and box with its kind, marks, printed label and title,
and the text of every option and match item; after that, renumbering,
removing, re-marking or retyping a locked part or box, changing an
option's text or the number of gaps in a box, and changing the paper's
`code` are refused until `version` changes. A caption fix keeps the
stored name, and moving whole questions warns. `tests/test_lock.py` makes
each change to a small issued paper.

Where it goes beyond or departs from the format's text:

- *One lock file per folder, holding each paper under its code.* The
  proposal draws `names.lock.json` in a folder of one paper, and
  `architecture.md` §6 sketches one paper to a file. The four PDP papers
  share one folder, so a teacher's folder may well hold several; each
  paper's entry also records its file name, which is how a changed
  `code` is caught.
- *How a renumbered part is recognised* is not in the format: by its
  title, now under another number, or, when the title changed too, by a
  new number standing in its place among the parts. A question
  renumbered with its parts is reported once.
- *Adding an option to a locked box is refused*, although it misplaces
  no stored answer: students chose from a different set.
- *Until the studio's Issue button (step 7), a command writes the lock*:
  `python -m dewmark lock FILE --sitting NAME`. It refuses a paper with
  problems but not one with `(draft)` scheme entries, since the scheme
  is not locked. The date recorded is the day of locking.
- *A lock written by another reader version warns rather than refuses.*
  The names are compared with the lock either way, so a reader change
  that moved a name is still caught as a change.

*Changing it:* the lock file's shape, `dewmark-names/1`, is a contract
from the first real issue; a lock written for a sat paper must stay
readable by every later dewmark.

**0.9 — The paste route: a package to give an assistant, and a check of
its reply.** `dewmark/package.py` builds the text a teacher gives any
assistant the college allows, and `dewmark/reply.py` checks what comes
back (decisions 19 and 20; `docs/EXAM_FORMAT.md` §4.10). The five modes are
decision 19's: `copy` (a Word paper into the format, changing no word),
`tidy`, `plain` (accessible language), `udl` and `invite` (commands as
invitations). The last four change wording only, and a reply is refused,
not flagged, if it changes a setting, a heading's number, marks or "any
N", a line of an answer box or listing, a number, a formula or a picture's
file name, or carries a scheme. Every change of wording that passes is
shown for the teacher to take or leave, one by one; leaving all of them
gives the teacher's file back byte for byte. `tests/test_paste.py` makes
each kind of bad reply, and has a fake assistant reword the four real PDP
papers.

Where it departs from, or settles, what the plan left open:

- *A whole reply is refused, never part of one.* A reply with a good
  rewording and a changed number could otherwise be half accepted into a
  paper that no longer matches what the assistant was asked to keep. The
  teacher sees every reason at once, in one round.
- *Wording inside an answer box is out of reach for now.* The options of
  a `choice`, the sentences of `blanks` and the lines of `boxes` are
  fixed, because the scheme's keys, the stored answers and the names lock
  are all tied to them. A tidy of an option's spelling has to be made by
  hand until a mode can promise to keep letters, item numbers and gap
  counts.
- *`copy` warns about words and refuses only a lost number.* §4.10 says
  the studio can check a copy "by matching paragraphs"; the check matches
  words in order, ignoring "marks", "Question" and "Section", which a
  conversion adds. A number missing from the reply entirely is refused
  (`reply-number-lost`); one that appears fewer times is a warning,
  because a Word paper often marks a question twice and a paper in this
  format marks it once.
- *`copy` adds a marking scheme of `(draft)` entries to what it returns*,
  one for each part with marks of its own, as the PDP converter does, so
  an exam that has none does not fail on that alone and the teacher has a
  list of what to write.
- *The student-information scan asks; it never refuses.* A paper has
  numbers of its own (a mark, a year, a formula), so a long number or a
  PPS-shaped one is a question for the teacher. The package itself can
  hold no submission, since dewmark holds none at this step.
- *Drafting model answers and schemes stays in step 9.* The scheme is
  never put in a package, and the assistant is told not to write one.
- *One short specimen paper stands in for every subject.* `copy` sends
  `dewmark/data/specimen.exam.md`, which has a coding question and a
  short-answer one; biology and maths specimens arrive with the subject
  waves of step 8. The cheat sheet is `docs/EXAM_FORMAT.md` §8, kept in
  `dewmark/data/cheat-sheet.txt` and checked against it by a test.

The words that ask an assistant to change wording (each mode's task text
in `package.py`) follow the voice section of dewlab's style guide: plain
words, no idioms, and a question's verb kept so its demand does not
change; they are addressed to an assistant, and the paper's students see
only what a teacher accepts. *Changing it:* the two pairs of marker lines
(`=== BEGIN PAPER ===`, `=== BEGIN NOTES ===` and their ends) join a
package to the check of its reply; changing them only affects packages
already handed to an assistant.

**0.10 — The checker page.** `checker/index.html` puts the reader and the
paste route in front of a teacher: paste or open an exam file and read each
problem with its line, what is wrong and what to do; click a problem to land
on its line; or have an assistant reword or convert a paper and take or
leave each change it made (planning/PROPOSAL.md §4, stages 2 to 4 of the
journey). The page runs the reader unchanged in Pyodide through
`dewmark/web.py`, which takes text and returns JSON, and `dev/build_site.py`
writes the page with the reader's own source files in a data block, so it
cannot check with other code than the command line runs.
`tests/browser/test_checker.py` is the probe the plan asked for from the
first commit: in Chromium it compares what the browser and the command line
return, string for string, over the specimen and the four PDP papers.

What it settles:

- *Python comes from jsDelivr, not from this repository.* The page needs a
  connection the first time, at the same Pyodide version the exam page pins
  (0.27.4); a failed load says so and offers to try again. Vendoring about
  10 MB of runtime would let the checker work offline, and is left to the
  studio (step 7) unless asked for sooner.
- *The content security policy includes `'unsafe-eval'`*, because Pyodide
  does not start without it (tried: the page stays on "Loading Python").
  What protects the paper is the rest of the policy: `connect-src` is
  jsDelivr alone, `form-action` and `default-src` are `'none'`, and
  `img-src` is `data:`. A policy does not stop the page's own script from
  navigating away, so the rehearsal also lists every request the page makes
  and fails on anything but a GET for the file or the CDN.
- *Nothing is saved.* A paper before it is sat is secret, and the checker
  may be open on a shared college computer, so it writes nothing to browser
  storage or cookies (a rehearsal checks) and a closed tab forgets the paper.
  **Save this file** downloads it.
- *A reply is checked against the paper the package was made from*, held in
  the page, not against whatever the editor holds by then, so editing the
  file between the two cannot make a good reply look like a bad one.
- *A package with something that may be student information waits for a
  tick* before it can be copied or saved, so the question is answered, not
  scrolled past.
- *The reader now says "Question 1", not "1",* where a message means a
  question: "Question 1's parts add up to 13 marks". The most common message
  on the page read "1's parts add up…". Names and the lock's labels are
  unchanged.
- *The check runs on the page's own thread, 400 ms after typing stops.* The
  plan says a background worker; a worker waits until a paper is long enough
  to make the page hesitate, which the 4,000-line limit keeps from being
  long.

*Changing it:* the JSON that `dewmark/web.py` returns is the contract between
the page and the reader. They ship in one file, so a built page cannot hold
one without the other.

**0.11 — The marker's half as JSON, and the search and the mutation test
that keep it off a student page.** `dewmark/scheme_json.py` writes the
scheme as `dewmark-scheme/1` (`python -m dewmark scheme FILE -o OUT`), and
`dewmark/secrecy.py` holds layers 3 and 4 of `docs/EXAM_FORMAT.md` §4.5:
`find_leaks` searches a whole built page for the scheme's strings, and
`mutation_test` writes the scheme again in nonsense and demands the page not
change. `tests/test_secrecy.py` tries both on renderers written here, one right
and nine each leaking the scheme a different way, and shows what each layer
catches: the search finds a string wherever it is written, and the mutation
test finds the key that is too short to search for, implied by a class on an
option, or encoded.

What it settles:

- *The layers take `build(text)`, not a renderer.* No page is built from the
  new format yet (step 4), so there is nothing to run them against. A function
  from the text of an exam file to a page is all they ask, which keeps them
  from caring how step 4 renders. **Not done, and owed to step 4:** run
  `mutation_test` and `find_leaks` over every sample and stop the build on a
  leak. Until then the layers are proved on renderers made to leak, not on the
  one that will matter.
- *The search covers the whole page.* The check it replaces
  (`check_for_leaks` in `build_exam.py`) removes `<script>` and `<style>`
  before looking, so a key put in the page's data for its own script to use
  was invisible to it. Strings are looked for as written, HTML-escaped and
  JSON-escaped, ignoring capitals and spacing, and a long string by its first
  and last 30 characters too.
- *A string the paper itself shows, or shorter than eight characters, is not
  searched.* Searching for it would flag a question that quotes its own
  answer's word, or any page containing "8". The mutation test, which needs
  no list, covers both.
- *The mutation test varies a key to a different valid one.* A choice,
  match or order key moves to the next option, a drop-down to another of its
  choices, and anything a student writes becomes nonsense, so the mutated
  file still reads as the paper does; a mutation that did not would be the
  test's fault, and is reported as that, not as a leak.
- *A marking scheme as JSON is refused by CI's privacy step* wherever it is
  committed and whatever it is called (a tracked `.json` file containing
  `dewmark-scheme/`). `.gitignore` already keeps out `dewmark_*`, but
  `scheme.json` would have gone in.
- *The JSON leaves out the question's own words*, though a marker will want
  them beside the answer. What the workbench shows is for step 6's design to
  decide, and a field may be added to `dewmark-scheme/1` without a new number.

*Changing it:* `dewmark-scheme/1` is a contract with the workbench from the
first marking that uses it; a field is not renamed or taken away without a new
format number. The nonsense that `mutate` writes (`zqx0001vjk`) must never be
a word a real scheme could contain.

**0.12 — The page for written papers, first slice: a builder that refuses a
leak and a page that saves.** `python -m dewmark build FILE -o DIR` makes a
paper's student page, practice page and answer key, and its marking scheme as
JSON (`dewmark/render.py`, `dewmark/build.py`, `assets/page.js`,
`assets/page.css`; the file format is `docs/ANSWER_FILE.md`). It is the first
of five slices of step 4, in this order: this one (the page draws the kinds of
box and saves what students write); the two start screens, reading settings,
branding and the Get ready list; the timer, with its invigilator's code, and
breaks; the PDF the page writes, the finish sheet and the receipt; print
headers and footers. Josh chose to finish step 4 before Python in the room
(step 5), and said there is plenty of time before anyone sits an exam, so the
slices are ordered for being right, not for the earliest sitting.

What it settles:

- *The builder is the one door.* Every page a student receives comes through
  `build_pages`, which refuses, writing nothing, a paper with problems, a paper
  that uses a kind no page draws, and a paper whose pages give away the scheme
  or a hint. That settles the debt entry 0.11 recorded: the search and the
  mutation test now run over the real student and practice pages of the
  specimen and of the four PDP papers, in the tests and in CI. The search runs
  over the page's data block and scripts as well as its text, and the mutation
  test rebuilds the page with the scheme (and, for the student page, the hints)
  made nonsense and demands the same bytes. The practice page has the hints on
  purpose, so only the scheme is searched for in it; the answer key is the one
  page that shows the scheme and is never built for a student.
- *A kind no page draws is refused, not drawn as a stand-in.* `match`,
  `order`, `photo` and `on-paper` stop the build, with a message that names the
  kind and says what to do instead. A page with a box a student cannot answer
  would be found in the exam room, not at the desk. They are built in step 8.
- *The page is a new file beside the old.* `assets/page.js` does not replace
  `assets/exam-page.js`: the old page's submissions are what the marking
  workbench reads, and the old builder still builds the samples and the
  papers already written. Two page scripts exist until step 6 rebuilds the
  workbench; the cost is a second thing to keep consistent, and the benefit is
  that nothing marked today is stranded.
- *The page is organised around a registry of kinds.* Each kind of box says how
  to collect an answer from its controls and how to put a saved one back, and
  nothing else, so a kind added in step 8 adds one entry. What each stores is
  fixed in `docs/ANSWER_FILE.md`. A box that is empty, or that holds only its
  starting text, is absent from the saved answers, not an empty answer, which
  is what lets "answered" mean "present" for the progress panel, the finish
  report and, later, the marks.
- *The answer file is JSON, `dewmark-answers/1`, not a zip.* The zip was the
  old page's way of carrying the readable copy and the data together. Decision
  23 makes the PDF the thing a student hands in for reading, and this file the
  thing the workbench reads, so the file need hold only the work. It carries no
  scheme and no marks. The old workbench does not read it; step 6 does.
- *The step-2 guards come over whole.* Nothing is written before Begin or
  Continue (`canWrite`); each page of a paper has its own slot,
  `dewmark:<code>:<page>`; starting again sets earlier work aside under
  `:set-aside:<time>`; a second window in the same browser steps back; the
  answer key saves nothing. `tests/browser/test_page.py` repeats each of the
  step-2 rehearsals against the new page, and the page was broken two ways (a
  start screen that writes, one slot for every page) to see them fail.
- *A built page connects to nothing.* Its content security policy is
  `default-src 'none'` with its own script and style, pictures as data
  addresses, `form-action 'none'` and `base-uri 'none'`. That holds whatever a
  paper's wording tries, and is why the page shows a link as text and an
  address, shows raw HTML as text, and takes a picture only from inside the
  paper's own folder. The rehearsal tells the page to fetch, load a picture and
  submit a form to a made-up address and checks that none gets through.
  Python in the room (step 5) will need `'unsafe-eval'` and a source for
  Pyodide's files; that is a change to this policy, made then, and written here
  then.
- *An answer file is checked, not trusted.* A file for another paper, another
  kind of page or in another shape is refused with a message. Of a file
  accepted, each answer goes back by `.value` or `.checked`, never as markup,
  and an answer of the wrong shape for its box is ignored; `__proto__` and
  markup in a name or an answer are inert. The rehearsal feeds a file of
  these.
- *The readable copy is made from the live page* (as the older page's is, and
  `docs/DEVELOPMENT.md` still lists it as the weaker construction): the page
  is cloned, each control is replaced by what the student gave, and every
  script and button is dropped. The rehearsal checks it holds no script and no
  control, and that an answer holding `</textarea><script>` stays text.
- *The site publishes the specimen's three pages* under `new/`, not the PDP
  papers (they are built by the tests and CI, and their trial runs are
  already published as they were first made) and never the scheme.
  `build.py` and `render.py` are left out of the checker page's bundle: they
  need the markdown and maths libraries, which Pyodide does not carry, and
  nothing a checker does builds a page.

Not done in this slice, and owed to the next: the start screens (the page asks
for a name and a number and says where the file will be kept, and nothing
more), reading settings, branding and the Get ready list; the timer and
breaks; the PDF, the finish sheet's receipt and print headers; Run on
`python exec`; and the accessibility checks the plan asks for (keyboard alone,
NVDA), which need a person.

*Changing it:* the page's hooks (`dm-` class names and ids, `data-answer`,
`data-kind`, `data-slot`) are what `tests/browser/test_page.py` selects by and
what the CSS and script share; a rename is a change to all three. The names in
an answer file are the paper's permanent names, and the file's shapes follow
`docs/ANSWER_FILE.md`'s rule for changing.
