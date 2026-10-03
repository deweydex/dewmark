# The PDF the page writes

Every hand-in includes a PDF (decision 10). The page writes it itself, with no
network, when the student presses **Save my answer file and PDF** on the finish sheet
(decision 23: the page writes it, with the browser's print window as the
backup). One press saves both files, into the folder the student chose or, in a
browser that cannot write into one, as two downloads; `docs/ANSWER_FILE.md` and
entry 0.16 of `DECISIONS_LOG.md` say how the page checks them. It is a plain record of what the student gave, for a marker to read in
Moodle's grader or on paper. The answer file (`docs/ANSWER_FILE.md`) is what the
marking workbench reads; the PDF is what a person reads.

## What is in it

A4 pages, in this order:

1. **The candidate and the codes.** The paper's title, institution, college,
   module and session; then the student's name and number, the paper's title, code,
   version and kind (student paper or practice version), the **Paper ID** and the
   **receipt** (`docs/ANSWER_FILE.md`), when the student started and finished
   (UTC), and how many parts have an answer.
2. **Each part, in the order of the paper.** Its printed heading as the paper
   shows it (`Question 2: A ladder (10 marks)`, `2(a) (6 marks)`), then the answer:
   - written answers, working and essays as typed, with an essay's word count;
   - code as typed, in a monospaced font with line numbers;
   - for a choice, the letter and wording of each option the student chose;
   - for gaps, boxes and tables, the line or table with each gap filled in as
     `[what they gave]`, and an empty gap as `[ ]`;
   - a part with nothing in it says `(not attempted)`;
   - a box marked `(not marked)` is labelled "Rough work: not marked".
3. **On every page**, a header with the student's name, student number and the
   exam code and "Page 3 of 5", and a footer with the Paper ID and the receipt.
   Printed pages come apart, so each one says whose it is and which paper.

The question wording is not in the PDF, and neither are the paper's listings,
pictures or reference cards: the page's readable copy holds the whole paper. Maths
is as the student typed it. There are no pictures yet (photographs come in step
8), and the output of a code run joins the PDF when pages can run Python (step 5).

## How it is made

`assets/page-pdf.js` is a small PDF writer of our own, not a library. The file is
plain PDF 1.4 with an ordinary cross-reference table and no object streams, which
is what the PDF tools in Moodle's grader read; every page and font is written
here and can be read here. `tests/browser/test_pdf.py` checks each PDF with
PyMuPDF (MuPDF), Ghostscript and qpdf, and checks the cross-reference table byte
by byte. The same answers give the same bytes: nothing in the file is random.

**Fonts.** Text is set in DejaVu Sans, and code in DejaVu Sans Mono, carried in
every page (`assets/vendor/pdf-fonts/`, about 180 KB) and written whole into each
PDF that uses them, so the PDF looks the same on any computer. They are subsets of
DejaVu 2.37 made by `dev/make_pdf_fonts.py`, with the licence beside them
(`DEJAVU-LICENSE.txt`) and a record in `assets/vendor/SOURCE.json`. Bold is the
same letters drawn with a thin outline.

**Characters.** Sans covers Latin (including the accents of Irish, Polish,
Romanian, Czech, Vietnamese and the rest of Europe), Greek, Cyrillic, general
punctuation, currency, super- and subscripts, arrows, the mathematical operators
and a few marks for ticking and pointing. Mono covers Latin and punctuation, and
a letter it lacks, such as a Greek letter in a comment, is drawn from Sans. A
character that neither has (Arabic, Chinese, an emoji) is drawn as a box, and what
a reader copies from the box is a question mark. The page then tells the student
which characters it could not show, and that the answer file has them exactly as
typed, and offers **Print or save as PDF**, which makes a PDF the way the browser
does. Control characters and invisible marks are left out.

**Layout.** Lines are wrapped at spaces, a word longer than a line is broken
between letters, and a part's heading is never left alone at the foot of a page: a
run of headings and the first two lines under them go together to the next page.
A long answer runs over as many pages as it takes.

## Changing it

The fonts' characters are listed in `dev/make_pdf_fonts.py`; adding a range means
running it, committing the new files and their record. The page's wording about
characters is in `assets/page-pdf.js`. A PDF is a record handed in, so a change
to what it holds, or the header and footer, is a change a marker will notice: say
so in `DECISIONS_LOG.md`.

Not yet tried: opening a PDF in a real Moodle assignment's grader (the plan asks for
a test assignment), and the keyboard and screen-reader walk-through of the finish
sheet.
