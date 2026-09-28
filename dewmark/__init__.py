"""dewmark: exam files in, exam pages out.

This package is the new builder, growing step by step beside the older
`build_exam.py` (planning/PROPOSAL.md §9). Today it holds the reader for
the exam format in docs/EXAM_FORMAT.md: `dewmark.reader.read()` takes the
text of an exam file and returns what the paper contains, with a message
for every problem. It uses nothing outside Python's standard library, so
the command line and the browser (through Pyodide) run the same code.
"""

READER_VERSION = "1.0"
