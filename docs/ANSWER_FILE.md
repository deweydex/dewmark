# The answer file

What a student's work is, as the new exam page (`dewmark/build.py`, with
`assets/page.js`) keeps it: in the browser as the paper is sat, and as the file
the student saves and hands in. It is one JSON file, `dewmark-answers/1`.

The page saves it three ways, which hold the same record: in this browser, in
a folder the student chose when they began (Chrome and Edge only), where it
is written as they work, and, whenever the student asks, as a download. Nothing is sent anywhere. A built page's
policy allows it to connect to nothing at all.

## What is in it

```json
{
  "format": "dewmark-answers/1",
  "exam": { "code": "specimen-short", "version": "1", "title": "Specimen Paper",
            "fingerprint": "1WV-H2V", "sitting": "2027-01-12 Group A" },
  "page": "student",
  "student": { "full name": "Agnes Nitt", "student number": "S12345" },
  "started_at": "2027-01-12T09:02:11.403Z",
  "saved_at": "2027-01-12T10:01:52.918Z",
  "finished_at": "2027-01-12T10:01:52.918Z",
  "receipt": "2337 B2A0",
  "time": {
    "timer": "enforced",
    "allowed_minutes": 120,
    "extra": [{ "minutes": 15, "by": "invigilator", "at": "2027-01-12T10:58:40.120Z" }],
    "breaks": [{ "start": "2027-01-12T09:40:02.331Z", "end": "2027-01-12T09:46:10.007Z" }],
    "closed": [{ "start": "2027-01-12T11:02:11.403Z", "end": "2027-01-12T11:07:30.840Z" }]
  },
  "answers": {
    "q1a": "8",
    "q1b": ["B"],
    "q1c": { "code": "price = 4\nprint(price * 2)" },
    "q2a": ["float", ""],
    "q2b": "A list is a row of values kept in order."
  }
}
```

| Field | Meaning |
|---|---|
| `format` | Always `dewmark-answers/1` for this shape. A page refuses a file with any other. |
| `exam` | The paper's `code`, `version` and `title` from its settings, its `fingerprint` (the Paper ID, below) and, when the pages were built for a sitting (`build --sitting`), that `sitting`; the key is absent otherwise. A page refuses a file whose `code`, `version` or `sitting` is not its own: a teacher raises the version when names or marks change, and the answers may not fit, and work from another sitting is another day's work. |
| `page` | Which page the work was done on: `student` or `practice`. A page refuses work from a page of the other kind. The answer key saves nothing. |
| `student` | What the start screen asked: `full name` and `student number`. |
| `started_at`, `saved_at` | When the student pressed Begin, and when the page last saved. UTC, to the millisecond. |
| `finished_at` | When the student pressed *Save my answer file and PDF* on the finish sheet. `null` until then, and `null` again if the student changes an answer afterwards. |
| `receipt` | The receipt of the record (below). `null` until the student saves at the finish sheet, and `null` again if they change an answer afterwards. |
| `time` | What the page recorded about time (below): the rule the clock followed, extra time and who gave it, breaks, and pauses while an enforced paper was closed. |
| `answers` | One entry for each answer box that has something in it, keyed by the box's permanent name. |

## Time

`time` is always present and always has this shape, so a reader never has to ask
whether a field exists. It is part of the record, so the receipt covers it: a
student, or anyone, who changes the minutes in a file changes the receipt.

| Field | Meaning |
|---|---|
| `timer` | The rule the page followed: `none`, `shown` or `enforced` (`docs/EXAM_FORMAT.md`, `timer`). A practice page of an enforced paper says `shown`: it never closes the paper. |
| `allowed_minutes` | The time allowed, in whole minutes, from `time allowed`; `null` when `timer` is `none`. |
| `extra` | The minutes added to the time allowed, one entry for each grant: `minutes` (1 to 600), `by` (`student` when the student typed it on the *Before you begin* screen, which a clock that only shows allows; `invigilator` when it was added with the invigilator's code, which is the only way under an enforced clock) and `at` (when). The student's own entry is replaced each time they change the box; the invigilator's entries only grow. |
| `breaks` | Each break the student took, `start` and `end`, when `breaks: on`. A break that is not yet ended has `end: null`: the page was closed on a break, and the clock is still stopped. |
| `closed` | The time an enforced paper spent closed, once the invigilator added time and it opened again: `start` is the moment the time ran out and `end` the moment it reopened. |

**How the clock reads it.** The time left is the moment `started_at`, plus
`allowed_minutes`, plus the `extra` minutes, plus the length of every break and
closed pause, less now. So minutes added to a paper that closed twenty minutes
ago are minutes the student can use, counted from when it reopens, and a record
carries everything a reader needs to say when the time was up. Closing the page
does not stop the clock; only a break does.

**What is not in it.** An enforced paper that is closed when the student saves
has nothing added to it for being closed: a closed paper is the clock's answer
(no time left), found again whenever the page opens. Only the `closed` pause is
written, and only when time is added.

**What it can and cannot prove.** The invigilator, in the room, is the check on
extra time and breaks, and the confirmation card shows both so that the card can
be held against the college's list. A student with developer tools can write
what they like into a file, and a receipt does not prevent it (it is not a
signature). The page's own rules (that extra time under an enforced clock needs
the code) stop accidents and casual attempts, and that is all they claim.

## The Paper ID and the receipt

Two short codes let a person or a program check that a file is the file it
should be. Both are made by `dewmark/receipt.py`, and the page makes the same
codes in JavaScript.

**The Paper ID** (the *fingerprint*, such as `7KQ-4MD`) identifies exactly the
paper students were given: the exam file above `# Marking scheme` with its
hints taken out, line endings and trailing spaces made the same, and a checksum
of every picture it carries. It is made when the paper is built, shown to the
student on the *Before you begin* screen and in the file's `exam.fingerprint`,
and printed by `python -m dewmark fingerprint FILE`. The marking scheme is never
in it, so correcting a key does not change it; a changed word, mark, setting or
picture does. The student page, the practice page and the answer key of one
paper share it.

**The receipt** (such as `7F3A 92C1`) identifies exactly one answer file as it
was handed in: the first eight hexadecimal digits of the SHA-256 of the record
in its canonical form, leaving out `saved_at` (which changes every time the
page saves) and `receipt` itself. The page shows it when the student saves, and
writes it into the file. `python -m dewmark receipt FILE` works it out again
and says whether the file is as it was saved; the marking workbench will do the
same. It finds a file that was changed by accident or after it was handed in. It
is not a signature: nothing in it is secret, so someone who can edit a file can
also write a receipt to match.

The **canonical form** is the record as JSON with the keys of every object in
sorted order (by code point), no spaces, and every character outside printable
ASCII written as a lower-case `\uXXXX` escape (a character above U+FFFF as two).
That is `json.dumps(record, sort_keys=True, separators=(",", ":"),
ensure_ascii=True)` in Python. A page that changes how it writes this text
changes every receipt already handed out, so `tests/test_receipt.py` freezes
a sample record's text and receipt, and `tests/browser/test_page.py` checks that
the page and Python agree on a record full of the characters most likely to
differ.

## What an answer looks like

A box that is empty, or that still holds only its starting text, is **absent**
from `answers`. It is never an empty string, so "answered" means "present", and
a box a student emptied again goes back to absent. What a box stores depends on
its kind:

| Kind | Stored as |
|---|---|
| `answer`, `maths`, `essay`, `code` | a string |
| `python exec` | `{ "code": "…" }`; the output of a run joins it when the page can run Python |
| `choice` | a list of the option letters chosen, in the order the options are printed: `["A", "C"]` |
| `boxes`, `blanks`, `table` | a list of strings, one for each place to fill, in order; a place left empty is `""` |

A name is the one `docs/EXAM_FORMAT.md` §4.4 makes from the number printed beside the box
(`q1a`, or `q1a.i` for a sub-part). Names are a contract, held still by the names lock. An answer under a name the paper no longer has is kept in the file
and ignored by the page.

## What the page does with a file it is given

An answer file comes from a disk, so it is checked, not trusted. The page
refuses a file that is not JSON, that is for another paper or another kind of
page, or whose `answers` or `student` is not an object. Of a file it accepts, it
puts each answer back with `.value`, `.checked` and `.textContent` only, never
as markup, and ignores an answer of the wrong shape for its box: a number where
a string goes, a string where a list goes, a drop-down value that is not one of
the box's choices. A student's name in a file cannot become part of the page
either.

## What is not in it

No marks and nothing from the marking scheme, and none of the student's reading
settings (font, text size, colours, ruler), which belong to the computer and
never travel in a file that a marker will open: the file holds what a student
wrote, so it is as safe to hand in as the paper was to sit. It does hold extra
time and breaks (above), because the marker and the exams office need them; it
never holds the invigilator's code or a hash of it. The PDF a student also hands in (decision 23)
is a separate file (`docs/PDF_FILE.md`) that carries the receipt and the Paper ID
on every page.

## Files and names

The download is `dewmark_<exam code>_<student number>_<name>.json`, with the
student's details lowercased and made safe for a file name. The `dewmark_`
prefix is how `.gitignore` and the repository's privacy check keep submissions
out of the public repository.

## Changing it

The format is a contract with the marking workbench from the first marking that
uses it. A field may be added without a new number; one is not renamed, changed
in shape or taken away without `dewmark-answers/2`, and the page keeps reading
`/1`, because a submission must stay readable for years. The older page
(`assets/exam-page.js`) hands in a zip, and the workbench reads only that: until
step 6 rebuilds the workbench, an answer file from the new page is read by
people and by the checks in `tests/browser/test_page.py`, not by the workbench.
