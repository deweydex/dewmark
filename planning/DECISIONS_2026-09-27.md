# Decisions, 27 September 2026

Josh's answers to the questions raised by the four designs in
`planning/research-2026-09-27/design/`. Where Josh's answer differs from
the design's recommendation, the design gives way.

## The move and the repository

1. **Licence: dewlab's own terms.** Copy dewlab's `LICENSE.md` as it
   stands, including its "get in touch first" rule.
2. **Working material: drop all research from main.** Once the exam
   format and `planning/PROPOSAL.md` are written, main keeps those two
   documents (and the mockups they link). The research reports, designs,
   screenshots, probes, workflow scripts and `PARKED.md` come out; git
   history keeps them. This cleanup waits until the design run no longer
   needs the files on disk.
3. **The two recreated real papers in `experiments/`** (maths 5N18396 and
   the HVIT database exam) will not be reused as live exams. They stay
   public as samples.
4. **dewlab's old `/dewmark/` address redirects to dewmark's home page**,
   not to the workbench.

## Architecture

5. **One builder, two front doors.** The Python builder runs on the
   command line for Josh and CI, and unchanged inside a browser studio
   for teachers.
6. **Papers live on college storage** in the paper-folder layout, and
   Josh's paper sources also go in a private `dewmark-papers`
   repository. Submissions never go on GitHub.
7. **Python delivery: both options.** A paper can carry Python inside the
   file (offline, with a folder beside it for heavy packages), or load it
   from the internet. The teacher chooses per paper.
8. **Browsers:** Chrome and Edge fully supported; Firefox and Safari
   work, with downloads in place of saving to a chosen folder.

## The student's sitting

9. **One combined start screen.** Name, number and reading settings
   share a single screen, not two steps. Saved work is still offered only
   after the student's number is typed.
10. **Hand-in always includes a PDF.** Moodle does not handle `.html`
    uploads reliably for teachers, so every submission includes a PDF.
    The data file beside it may be `.html` (easier to check by eye,
    preferred where possible), `.json`, or both; that choice is
    incidental.
11. **Timer: the teacher's option.** A paper may have no timer, a timer
    that is shown, or a timer that is enforced. In every case the
    student can hide it with one click. **Breaks** are a separate teacher
    option, off by default; when on, the page offers a clean way to take
    and end a break.
12. **Branding:** text keys (institution, college, module and code,
    paper, session) plus an optional logo; a fixed band marks
    EXAMINATION or PRACTICE; no college colour yet.

## Question types and marking

13. **Assisted, never automatic.** Rules the teacher wrote (a key, a
    tolerance, a code test) propose marks on closed types and give
    evidence on the rest; the marker confirms every mark. Q15 is reopened
    on these terms.
14. **Practice self-check only after the paper is finished.** A practice
    paper may show its answers, but only once the student has finished
    the whole paper, never question by question.
15. **Maths input: all three routes.** Plain text with a typeset "reads
    as" line and a symbol palette; a visual maths editor (MathLive); and
    photographs of handwritten working. The paper chooses which it
    offers. Paper sheets stay available for long working.
16. **Hidden code tests** live in the marking scheme and run in the
    workbench, and may also run in practice pages so students see which
    pass. They never run in an exam paper.

## The assistant

17. **No mark suggestions.** The assistant does not suggest marks on any
    paper. A separate document should investigate how mark suggestion
    could be done and what it would take (evidence, regulation, design),
    as a study, not a feature.
18. **Endpoints: local and approved cloud.** dewmark may call a local
    address or a cloud endpoint the teacher configures; it is the
    teacher's responsibility to know what is acceptable.
19. **Conversion offers several modes:** copy without composing; tidy
    the wording; check that the language is accessible; make the paper
    more UDL-friendly; and rephrase commands as invitations. The teacher
    picks, and sees every change.
20. **The paste route ships now.** With no model connected, the studio
    prepares a package (a sample or idealised exam file for the subject,
    the format's markdown guide, and the teacher's exam) to give to any
    assistant, and checks the reply. It contains no student data. It is
    also a small exercise in AI literacy.
