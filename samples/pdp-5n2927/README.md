# The PDP 5N2927 papers in the new exam format

These four files are the hand-built PDP pages in `experiments/pdp-5n2927/`,
converted to the exam format in `docs/EXAM_FORMAT.md` by
`dewmark/convert_pdp.py`. They are written, not hand-edited: to change
one, change the converter and run

    python -m dewmark.convert_pdp samples/pdp-5n2927 experiments/pdp-5n2927/*.html

A test fails if these files drift from what the converter writes.

Each has a marking scheme of `(draft)` entries, one per marked part, to be
filled in. `python -m dewmark check` reads them with no problems. No page is
built from them yet: the older builder reads only the older format, and the
exam page that reads this one is step 4 of the plan.
