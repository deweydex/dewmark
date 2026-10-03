# The answer file

What a student's work is, as the new exam page (`dewmark/build.py`, with
`assets/page.js`) keeps it: in the browser as the paper is sat, and as the file
the student saves and hands in. It is one JSON file, `dewmark-answers/1`.

The page saves it three ways, which hold the same record: in this browser, in
a file the student chose when they began (Chrome and Edge only), and, whenever
the student asks, as a download. Nothing is sent anywhere. A built page's
policy allows it to connect to nothing at all.

## What is in it

```json
{
  "format": "dewmark-answers/1",
  "exam": { "code": "specimen-short", "version": "1", "title": "Specimen Paper" },
  "page": "student",
  "student": { "full name": "Agnes Nitt", "student number": "S12345" },
  "started_at": "2027-01-12T09:02:11.403Z",
  "saved_at": "2027-01-12T10:01:52.918Z",
  "finished_at": "2027-01-12T10:01:52.918Z",
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
| `exam` | The paper's `code`, `version` and `title` from its settings. A page refuses a file whose `code` is not its own. |
| `page` | Which page the work was done on: `student` or `practice`. A page refuses work from a page of the other kind. The answer key saves nothing. |
| `student` | What the start screen asked: `full name` and `student number`. |
| `started_at`, `saved_at` | When the student pressed Begin, and when the page last saved. UTC, to the millisecond. |
| `finished_at` | When the student pressed *Save my answer file* on the finish sheet. `null` until then. |
| `answers` | One entry for each answer box that has something in it, keyed by the box's permanent name. |

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
wrote, so it is as safe to hand in as the paper was to sit. Nothing about the
timer, breaks or extra time yet. The PDF a student also hands in (decision 23)
is a separate file, and so are the receipt and the fingerprint; they come with
the PDF writer.

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
