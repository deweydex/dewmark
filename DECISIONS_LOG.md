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

**0.13 — The two screens before the paper, reading settings, branding, and
the list of what a paper needs.** The second of the five slices of step 4
(entry 0.12). A page now opens on *Start* (details, reading settings, what the
paper needs) and goes on to *Before you begin* (instructions, where the answer
file goes, Begin), as decision 25 sets out; the band carries the paper's
branding; every screen has an **Aa** button that opens the reading settings.

What it settles:

- *Saved work is offered only for its own number.* Decision 9 said saved work
  is offered after the number is typed. The page goes one step further and
  offers it only when the number typed is the number the work belongs to
  (ignoring capitals and spaces), so a shared computer never tells the next
  student that someone has been working on this paper. If a different number
  begins, the earlier work is set aside after a question at Begin, as before,
  never written over. A student who continues and then goes back and changes
  the details lets the saved work go: it is not loaded into the paper under
  someone else's name.
- *The save window is a button on the second screen, not part of Begin.*
  Begin used to open the browser's own save window, which is a surprise at the
  moment a student is waiting to start. Now the student chooses the place on
  the screen that says why; a student who does not is asked once at Begin. A
  browser that cannot save into a file (Firefox, Safari; decision 8) is told
  so on that screen, in plain words, and carries on.
- *Reading settings belong to the computer, not to the paper or the student's
  file.* They are kept on this computer under `dewmark:reading-settings`, so a
  student who sits several papers sets them once. They are never in the answer
  file, the PDF or the readable copy: a file handed to a marker must not say
  that its student needed large text or a font for dyslexia. The price is that
  on a shared college computer the next student finds them; the page says so
  where the settings are shown, and **Use standard settings** removes them.
  This was chosen without Josh's say-so, and he may want it the other way
  (clear them on finishing, or keep them only on a practice page); it is one
  key and one function to change.
- *One description, two drawings.* `READING` in `dewmark/build.py` says what
  each setting is, what values it may have and what it begins as. The builder
  draws the controls from it twice, on the first screen (four settings: font,
  text size, colours, ruler, with the rest under More settings) and in the
  drawer, and the page checks any stored setting against it, so a value left by
  an older page or edited by hand can never put the page in a state it cannot
  draw. Nothing is written until a student changes a setting.
- *Six colour schemes, tested.* Match my computer, Light, Cream paper, Blue
  tint, Dark and High contrast. Every colour is a variable and every size is in
  `rem`, so a scheme or a text size from 14 to 32 pixels changes the whole page.
  `tests/test_page_css.py` computes the contrast of each pair of colours the
  stylesheet puts together: text reaches 4.5 to 1 and the edge of a field and
  the focus ring 3 to 1, in every scheme. One pair failed at first (the
  orange button in Blue tint) and was fixed.
- *Two reading fonts, carried in the page.* Lexend and OpenDyslexic, about
  345 KB of a page of 445 KB, so a student's choice never depends on the
  computer. The files are copies from dewlab with a source record
  (`assets/vendor/SOURCE.json`: the dewlab commit and a checksum for each),
  and `tests/test_vendor.py` fails if one is edited by hand (decision 31). The
  page's policy gains `font-src data:` and nothing else. The italic faces are
  left out; a browser slants the upright one. The fonts' licences are those of
  the `@fontsource` packages dewlab builds them from; that record should be
  read before dewmark's own licence terms are settled.
- *The reading ruler* follows the pointer, and moves to the line being typed
  (found by laying the text out again in an invisible copy of the box).
- *Branding is text and a picture, in a fixed band.* `institution`, `college`,
  `module`, `module code`, `session` and an optional `logo` appear in the
  band, which says in words whether the page is an examination, a practice
  version or an answer key. A logo is a picture file inside the paper's folder,
  at most 150 KB, carried into the page as the other pictures are; a logo that
  is missing, remote, outside the folder, not a picture or too big stops the
  build with a message. There is no college colour (decision 12). `number
  example` is the hint under the student number.
- *The list of what a paper needs is made from the paper.* The builder lists
  the paper and its fonts, Python (and where it comes from, its packages and
  its set-up code) if the paper declares any, and the two ways of saving; a
  teacher never writes a loading screen. The page runs a check for each item
  and shows the result in words as well as colour. The two real checks today
  are whether this browser will keep anything (a small key is written and
  removed at once, which also finds a full disk) and whether it can save into
  a file. The Python rows say plainly that this page cannot run Python yet;
  step 5 puts a loader there, and a check may take time and return a promise
  of a state. A problem is shown and never stops Begin: the student can still
  read and write, and the invigilator decides.
- *The one rule about writing before Begin has two more exceptions, both of
  them not the student's work:* the reading settings, written only when
  changed, and the storage test, which leaves nothing behind. CLAUDE.md says
  so, and `tests/browser/test_page.py` checks that the first screen writes
  nothing else, and that a changed setting is the only thing it writes.

Moved to the next slice: *the invigilator's view of work set aside.* `docs/DEVELOPMENT.md`
said it comes with these screens. It cannot be safe without the invigilator's
code of decision 24: a list of other students' saved work that any student can
open is the leak the previous point closes. The code comes with the timer, and
the view comes with it. *Extra time* moves there too, since the answer file's
record of it and the timer's behaviour are one design. This slice shows the
time allowed and nothing more.

Not done: the keyboard-alone and NVDA walk-through the plan asks for (it needs
a person at a college computer), and a check that the drawer and screens read
well at the largest text on a phone (the rehearsals check that nothing scrolls
sideways at 1024 pixels and 420 pixels wide).

*Changing it:* a new reading setting is added in four places that must agree:
`READING`, `reading_controls` and its labels in `dewmark/build.py`, `applyReading`
in `assets/page-reading.js`, and the CSS variable or attribute it sets. The
stored settings have no format number: a setting that is unknown or invalid
becomes its default, so a new one can be added without one.
A colour added to the stylesheet goes into the pairs of `tests/test_page_css.py`
in the same commit.

**0.14 — The receipt, the Paper ID, and work from another version.** The first
part of step 4's fourth slice (the PDF, the finish sheet and the receipt). Two
short codes, made by `dewmark/receipt.py` and by the page, let a person or a
program check that a file is the file it should be: the **Paper ID**
(`7KQ-4MD`, the plan's *fingerprint*), which identifies a paper, and the
**receipt** (`7F3A 92C1`), which identifies an answer file as it was handed in.
`docs/ANSWER_FILE.md` describes both.

What it settles:

- *The Paper ID is made at build, not at issue.* The plan had the studio's Issue
  button write it (step 7). It is a plain function of the paper, so the builder
  makes it every time, `python -m dewmark fingerprint FILE` prints it, and the
  studio will show it. Nothing is stored that could go stale. It is the start of
  a SHA-256 of the exam file above `# Marking scheme` (settings, questions,
  reference cards) without its hints and with line endings and trailing spaces
  made the same, together with a checksum of every picture and the logo; six
  letters of Crockford's alphabet. The marking scheme is never in it, which
  keeps a page's bytes independent of the scheme, as the mutation test demands,
  and means that correcting a key does not change what students sat. The student
  page, the practice page and the answer key of one paper share it.
- *The receipt is a hash of the whole record.* Everything but `saved_at`
  (which changes every few seconds) and `receipt` itself: the answers, the name
  and number, the paper, the start and finish times. Eight hexadecimal digits in
  two groups of four, short enough to read down a telephone. It finds a file
  changed by accident or after it was handed in. It is **not a signature**:
  nothing in it is secret, and someone who can edit a file can write a matching
  receipt. It is evidence for the marker, not security against a determined
  student; the PDF, which the page writes at the same moment, is the second
  copy a marker can compare.
- *One canonical form, two languages.* JSON with sorted keys, no spaces, every
  character outside printable ASCII as a lower-case `\uXXXX` escape. Python's
  `ensure_ascii=True` writes exactly that; the page writes it by hand, sorting
  keys by code point as Python does (not by UTF-16 unit, which differ for
  characters above U+FFFF) and keeping a key named `__proto__` as a key. The
  page's SHA-256 is also written by hand, so the receipt does not depend on
  `crypto.subtle`, which browsers offer only to a secure context, and is worked
  out at once. `tests/test_receipt.py` freezes a sample's canonical text and
  receipt, and `tests/browser/test_page.py` checks the page's hash against
  Python's for thirteen lengths around the block boundaries, and its canonical
  text and receipt against Python's for a record of the characters most likely
  to differ (accents, `≥`, an emoji, DEL, control characters, `__proto__`).
- *Saving at the finish sheet fixes the receipt, and a later change withdraws
  it.* The page gathers the answers, sets `finished_at`, works the receipt out
  and shows it with the Paper ID and the number of answers. If the student then
  changes an answer, `finished_at` and `receipt` go back to `null` and the finish
  sheet asks for another save, so a file and a receipt never describe a paper
  that has since changed.
- *Work from another version is set aside, not restored.* The plan said so
  (§5.2) and the page now does it: saved work for another `version` is not
  offered when the number is typed, and Begin sets it aside after the usual
  question; an answer file from another version is refused in words that give
  both versions. A teacher raises the version when names or marks change, so the
  answers may not fit the boxes. Work saved on the *same* version of a paper that
  was corrected in wording (a different Paper ID) is kept and continued, with a
  sentence saying the paper was corrected; the file made at the end carries the
  Paper ID of the paper it was finished on.
- *Two commands for before the workbench exists.* `python -m dewmark receipt
  FILE...` checks each handed-in answer file against the receipt in it (exit 1
  if any fails) and `python -m dewmark fingerprint FILE` prints the Paper ID.

Not done: the receipt on every page of the PDF (there is no PDF yet), the
"Checked: the file holds 17 answers" read-back (it needs the folder the finish
sheet will write into, next), the receipt shown by the workbench (step 6), and
the sitting card with the Paper ID (the studio, step 7). The Paper ID is shown
to students as "Paper ID", because "fingerprint" is a word they would have to
be told.

*Changing it:* the material of a receipt or a fingerprint, the canonical form, or
the alphabet changes every code already handed out. A change is a decision, and
a new format number for the answer file if receipts already issued must still
verify; the frozen values in `tests/test_receipt.py` fail first.

**0.15 — The PDF the page writes.** The second part of step 4's fourth slice.
`assets/page-pdf.js` writes the PDF of decision 23 with no network, from the
paper on the page and the student's record, when the student presses **Save a
PDF**; **Print or save as PDF** opens the browser's own window as the backup.
`docs/PDF_FILE.md` describes it.

What it settles:

- *A PDF writer of our own, not a library.* The plan expected a PDF library
  (D3, "two to three weeks"). A library is hundreds of kilobytes of someone
  else's code in every page, and the page is a file a student opens from a
  disk. What the page needs is small (text, rules, a font, numbered pages),
  and the file is the one thing a marker opens, so every byte of it is code
  that can be read here. The writer is about 650 lines, writes **PDF 1.4 with a
  plain cross-reference table and no object streams**, which is what the
  PDF tools in Moodle's grader read (its annotation tool imports pages with a
  reader for that kind of file), and writes the same bytes for the same
  answers.
- *Fonts are DejaVu, cut down and carried in the page.* A PDF must look the
  same on any computer and show Irish accents and mathematical symbols as typed,
  so each PDF carries its fonts. DejaVu Sans and Sans Mono (licence: Bitstream
  Vera with public-domain changes; it allows copying and embedding if the notice
  stays, and a modified font if it is not named Bitstream or Vera) are cut by
  `dev/make_pdf_fonts.py` to Latin with its European accents, Greek, Cyrillic,
  punctuation, currency, arrows and mathematical operators for Sans, and Latin
  and punctuation for Mono, with the licence beside them and a checksummed record
  (`assets/vendor/SOURCE.json`). Together they are about 180 KB, about 235 KB as
  carried in a page, which is now about 720 KB. Cyrillic, Greek and Vietnamese,
  which the plan expected to fall back to the print button, are covered; the
  cost of the whole set is under 20 KB. Bold is drawn with a thin outline, so no
  bold font is carried. A PDF carries only the fonts it uses, so a PDF with no
  code does not carry Mono.
- *What a character the fonts lack does.* A box is drawn in its place, what a
  reader copies from it is a question mark, and the student is told which
  characters could not be shown, that the answer file has them as typed, and
  that **Print or save as PDF** will show them: the plan's rule, kept.
- *The PDF holds the headings and the answers, not the question.* Decision 23
  and D3 say so: each part's printed heading and the answer as typed, with the
  question's wording left to the readable copy. A choice shows the options
  chosen with their wording, and a gap or a table shows its line with the gaps
  filled in. The wording could be added later; leaving it out keeps a PDF to the
  student's own words.
- *Every page says whose it is.* The name, student number and exam code at the
  top, "Page n of N", and the Paper ID and receipt at the foot, so a page that
  comes loose from the rest can still be matched to the answer file.
- *One finish sheet, one receipt.* Saving the answer file and saving the PDF
  both use the receipt the finish fixed (`fixReceipt`), and a second press does
  not make a new one, so the PDF's footer and the file agree. A change to an
  answer withdraws it (entry 0.14).
- *Checked by three readers.* `tests/browser/test_pdf.py` opens each PDF in
  MuPDF (no repair, no warnings; text, fonts and positions), `qpdf --check`, and
  Ghostscript (draws every page and writes the file again), and checks the
  cross-reference table entry by entry. CI installs Ghostscript and qpdf. The
  rehearsals include a sweep that puts a heading at every height a page can
  have, and was shown to fail when the heading rule was broken.

Not done: opening a PDF in a real Moodle assignment's grader (the plan asks for a
test assignment; it needs a Moodle), pictures and photographs in a PDF (step 8),
the output of a code run (step 5), and the question wording.

*Changing it:* what a PDF holds and the header and footer are what a marker is
used to; a change is a decision. A new character range is made with
`dev/make_pdf_fonts.py` and recorded in `assets/vendor/SOURCE.json`.
