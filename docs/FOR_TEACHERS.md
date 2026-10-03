# dewmark for teachers

This guide walks through running an exam with dewmark, from an exam you
already have to a marks spreadsheet. It assumes no programming
knowledge. Where a step differs between browsers, the guide says so;
Chrome and Edge support everything below, and the differences on other
browsers are noted where they occur.

**The exam file is changing.** The [exam file checker](https://deweydex.github.io/dewmark/checker/)
reads a newer, simpler exam file (described in `docs/EXAM_FORMAT.md`). It
shows every problem with its line and what to do, and it can make a text for
an assistant your college allows, to reword a paper or to put a Word paper
into the new format, and then check what the assistant sends back before you
use any of it. The builder in this guide still reads the older format until the
new exam page is built, so a file that passes the checker cannot be built into
an exam yet. Use the checker to write and tidy papers now. Build only papers
in the older format.

## 1. Get your exam into a dewmark exam file

A dewmark exam lives in one plain-text file called the exam file. There
are two ways to get one.

**Convert an exam you already have.** Give your existing exam — a Word
document, a PDF, or plain text — together with its marking scheme to
the translation assistant, which produces the exam file and checks it.
You then read the result as a normal exam paper (not as a text file)
and correct anything that came through wrongly. The assistant follows
strict rules: it never invents marks, and any model answer it drafted
rather than copied is labelled as a draft until you approve it. The
full route is described in
[../planning/TRANSLATING_AN_EXISTING_EXAM.md](../planning/TRANSLATING_AN_EXISTING_EXAM.md).

**Write the exam file directly.** The file format is documented in
[../planning/THE_EXAM_FILE.md](../planning/THE_EXAM_FILE.md), and the
sample in [../samples/sample-mixed-paper.exam.md](../samples/sample-mixed-paper.exam.md)
shows a complete paper that mixes eight question types. Four further
samples show the shapes real papers take.

- [../samples/maths-for-it-5n18396.exam.md](../samples/maths-for-it-5n18396.exam.md)
  is a 120-mark mathematics paper with "answer any N" sections, a
  calculator, a formula sheet in the side panel, and diagrams in the
  questions.
- [../samples/hvit-database-practical.exam.md](../samples/hvit-database-practical.exam.md)
  is a database practical made entirely of Python code questions,
  with a database and two spreadsheets embedded.
- [../samples/sample-biology-paper.exam.md](../samples/sample-biology-paper.exam.md)
  is a science paper: fill-in-the-blank, diagram labelling, a table,
  a calculation, a sketch description, and long explanatory answers
  marked with guidance.
- [../samples/sample-essay-paper.exam.md](../samples/sample-essay-paper.exam.md)
  is a writing paper: reading questions on a passage, a choice of
  three 40-mark essay titles, and a formal letter, all marked with
  criteria grids.

Copying the sample nearest your paper and replacing its questions is
a reasonable way to start.

Every question type available to you — from multiple choice to essays
with marking criteria — is explained, with what students see and how
marking works, in
[../planning/QUESTION_TYPES_AND_MARKING.md](../planning/QUESTION_TYPES_AND_MARKING.md).

## 2. Build the exam

Building turns the exam file into the finished pages. On a computer
with Python installed, run:

```sh
python build_exam.py my-exam.md --output finished/
```

If anything in the file is wrong — marks that do not add up, a missing
picture, a question that would reveal its own answer — the builder
stops and lists every problem with the line it is on. Fix the file and
run it again. When the file is clean, the `finished/` folder holds four
things:

- `my-exam-code.student.html` — the paper your students sit;
- `my-exam-code.practice.html` — the same paper with the hints kept,
  for revision;
- `my-exam-code.answer-key.html` — the paper with model answers shown,
  for you and any second marker;
- `dewmark_my-exam-code_marking_scheme.json` — the file the marking
  workbench reads. Keep this one to yourself.

**A newer builder is being made, and is not ready for a class.** If your
paper is written in the new format ([EXAM_FORMAT.md](EXAM_FORMAT.md)),
`python -m dewmark build my-exam.exam.md -o finished/` builds the same four
files from it, and stops, writing nothing, if a page it made would show
students the marking scheme or a hint. What it makes cannot draw four kinds
of question (matching, ordering, photographs and "answer on paper"; it tells
you which), cannot run Python yet, and saves an answer file the marking
workbench cannot read yet ([ANSWER_FILE.md](ANSWER_FILE.md)). Use it to try the
new format, and use `build_exam.py` for a real sitting.

What a student sees on the newer page: a band at the top that says in words
whether this is an examination, a practice version or an answer key, with the
paper's title, `institution`, `college`, `module`, `module code`, `session`,
the time allowed and a `logo` if you give one (a picture file beside the exam
file, 150 KB at most). Then two screens. On the first, the student types a name
and a student number, chooses how the page looks, and sees a list of what the
paper needs. On the second, they read your instructions, choose a folder
for their files, and press Begin. If the computer holds saved work for the
number the student types, the page offers it, and offers it only for that
number. The student's reading settings (font, text size, colours, a reading
ruler) stay on that computer and are not in the answer file you receive. On a
shared computer the next student finds them, so the page says so and offers
**Use standard settings**. The **Aa** button at the top right opens the same
settings on every screen.

Every page built from one paper shows the same **Paper ID**, such as `7KQ-4MD`,
on the second screen, and writes it into the answer file. Read it out to check
that every student has the same copy of the paper; `python -m dewmark fingerprint
my-exam.exam.md` prints it. Work saved on another version of a paper is not put
into a new version: the page keeps it aside and starts the student again.

On the screen before the paper, a student in Chrome or Edge chooses a folder (a
folder on a USB stick, say), and the page saves their answer file into it as they
work. On the finish sheet, one press saves the answer file and a **PDF** of their
answers into the same folder, reads both back, and shows a **receipt**, such as
`7F3A 92C1`, and a card for you with their name, number, paper, Paper ID, answers
and the time. In another browser the page downloads both files and says it cannot
look inside them. `python -m dewmark receipt FILE` checks a handed-in answer file
against its receipt, and says if the file was changed after it was saved.

The PDF (`docs/PDF_FILE.md`) has each part's heading and the answer as typed, with
the student's name, number and the exam code on every page and the Paper ID and
receipt at the foot. The page makes it with no network. **Print or save as PDF**
(and Ctrl+P) gives the browser's own version, with the same header and footer and
the whole of every answer, in Chrome and Edge; Firefox and Safari print the paper
without a header or footer, so for a student who uses one, hand in the page's PDF. A student whose answer
holds a character the PDF's fonts lack (Arabic or Chinese, say) is told which, and
offered the browser's own print window instead.

**The clock, extra time and breaks.** `timer` in the exam file is `none`, `shown` or
`enforced`, and `breaks` is `on` or `off` ([EXAM_FORMAT.md](EXAM_FORMAT.md) §4.9). With
`shown`, the page has a clock at the top that a student can hide with one click.
It tells the student once, in words, at ten minutes. At zero nothing stops them:
you tell them. A student with extra time types the minutes on the second screen,
and the confirmation card shows them, so you can check against your list. With
`enforced`, the page saves at zero, the answer boxes stop taking changes, and the
finish sheet opens, where the student can still save and hand in. You add time
with the **invigilator's code**, and time you add to a paper that has closed
counts from the moment you add it. Extra time for a student with an enforced
clock is only ever added with the code, on the second screen before Begin or on
the finish sheet. With `breaks: on`, a student presses **Take a break**: the
page hides the paper, stops the clock, and records when the break began and
ended; the confirmation card counts the breaks. The practice page shows the clock
and never closes the paper. Closing the page does not stop the clock, only a
break does. The answer file records the rule, the extra time and who gave it,
the breaks, and any time a closed paper waited for you
([ANSWER_FILE.md](ANSWER_FILE.md), *Time*).

**The invigilator's code** is made when you build the pages for a sitting:

```sh
python -m dewmark build my-exam.exam.md -o finished/ --sitting "2026-10-20 Group A"
```

The command prints six digits, such as `482 915`. Write them on the sitting card
and keep them out of the folder students receive: no file holds them, and the
pages hold only a short hash. A new sitting gets a new code. To build the same pages
again so that they accept the same code, add `--code 482915`; you may also choose
a code of your own, of four to eight digits. A paper with `timer: enforced` cannot
be built without one. The code does four things: it adds time to a closed paper,
it lets a student start again under an enforced clock (which does not give a
new clock), it lets a student continue work saved under a different name, and it
opens **Saved work on this computer (for invigilators)** on the first screen,
which lists the work the computer holds for this paper (by the student's
initials and the last digits of the number, never the whole name), lets you save
any of it as a file, and lets you continue from it. Nothing the page does deletes
saved work. The code guards against accidents, not against a student who knows
how to read a page's source: it is a hash of a short number. You are in the room,
as at a paper exam, and the card and the file are there to check afterwards.
The page waits 30 seconds after three wrong codes.

Work saved in another sitting is never offered back to a student: each sitting's
pages know their sitting, and the answer file records it.

Before the real sitting, open the student page and sit the paper
yourself. Reading your own exam as a student finds more problems than
any automatic check.

## 3. Distribute the paper and run the sitting

Give students the single student file through whatever you already use
— a Moodle assignment, a shared folder, or a USB stick. The page works
offline: a student can double-click the file with no internet
connection and sit the whole exam. (The exception is exams containing
Python programming tasks: the first time the page runs code it
downloads the Python system, about thirty megabytes, so those exams
need either an internet connection or a copy of the Python system
served from a machine in the room. Rehearse this on the room's own
computers before a real sitting.)

When a student opens the page they type their name and student number
and press Begin. On Chrome and Edge the page then asks them to choose
where their answer file is kept — their home folder or a USB stick —
and saves into it automatically as they work; on other browsers they
use the "Save a copy" button regularly instead. The page also saves
into the browser itself after every change, so a crash or an
accidental close loses nothing: reopening the page offers to continue
from the saved work. A student who presses Begin to start again is
asked first, and their earlier work is kept on the computer rather
than deleted. The practice version and the student paper keep their
saved work apart, so a practice attempt is never offered in the real
paper, and the answer key saves nothing.

When a student presses "Finish exam", the page shows them anything
still empty, confirms their details, and downloads one file named after
the exam and the student, for example
`dewmark_sample-mixed-2027_s12345_nitt-agnes.zip`. They upload that
file to the assignment you named. If you grant extra time, they keep
working and download again; you mark the newest file.

If a student's computer fails before they finish, their answer file —
the one chosen at Begin — can be handed in directly. The marking
workbench accepts it and tells you it arrived without the finish step.

## 4. Mark the exam

Download all the submissions into one folder. Open the workbench at
<https://deweydex.github.io/dewmark/workbench/>, or open
`workbench/index.html` from a downloaded copy, in Chrome or Edge; load the marking
scheme file from step 2, and open the submissions folder. You will see
a class list with each student's attempts and marking status.

Open a paper and work through it: each answer appears beside its model
answer and marking scheme, and you enter the marks. Points-list schemes
("any three of the following") appear as boxes you tick, and the total
stops at the limit. Essay criteria appear with their mark bands. Every
answer takes an optional feedback comment, and each paper takes a
closing comment. You can also mark one question across every student,
which many markers find keeps their standard steadier.

Your marking saves into the submissions folder as you go, so you can
stop and continue another day, or move the folder to another computer.

In sections where students chose which questions to answer, the
workbench marks everything attempted and counts the best scores toward
the total, showing you which questions counted.

## 5. Return the papers and export the marks

From any marked paper, "Graded paper" opens a printable page with the
student's answers, marks, and your feedback; print it to PDF and return
it through Moodle. "Export marks" produces two spreadsheet files that
open in Excel: the marks, one row per student with one column per
question, and a companion file explaining what every column means, for
an assessor or external authenticator. The submissions folder itself —
submissions, scheme, marking record, exports — is the complete record
of the exam, and it never left your computer.

## Before a first real sitting

- Sit the built paper yourself, start to finish, on the kind of
  computer the exam room has.
- Run one rehearsal in the room: open the page on a machine with the
  network off and check that it works.
- Agree with your quality-assurance colleagues how "answer any N"
  sections are counted; the workbench defaults to counting the best N
  and records which questions counted.
- Decide where submissions will be stored after marking; they contain
  student names, numbers, and exam answers, and your institution's
  rules for exam scripts apply to them.
