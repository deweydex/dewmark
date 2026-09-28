"""Rehearsals for the ways today's pages lost or mixed up answers.

Each test sits part of the mixed sample in a real browser and checks what
browser storage holds afterwards. They are the regression tests for step 2
of the plan (planning/PROPOSAL.md §9), each written to fail on the bug it
names before the fix:

- A: a reload, a closed tab, or Begin on the start screen wiped the saved
  answers that the start screen was offering to restore;
- B: the practice paper, the student paper and the answer key of one exam
  shared a single save slot, and the answer key saved at all;
- the second window: a second copy of the paper, told it "will not save",
  still wrote over the first copy's answers when it closed;
- G: the workbench counted the marking scheme and its own marking record
  as students when they sat in the submissions folder.
"""

import json
import zipfile
from pathlib import Path

WORKBENCH = Path(__file__).resolve().parent.parent.parent / "workbench" / "index.html"
ROOTS_BOX = '[data-answer="a3.roots"] input[data-box="1"]'


def open_page(context, path, accept_dialogs=False):
    page = context.new_page()
    page.errors = []
    page.on("pageerror", lambda e: page.errors.append(str(e)))
    if accept_dialogs:
        page.on("dialog", lambda d: d.accept())
    page.goto(path.resolve().as_uri())
    return page


def begin(page, name="Agnes Nitt", number="S12345"):
    page.fill('[data-detail="full name"]', name)
    page.fill('[data-detail="student number"]', number)
    page.click("#dm-begin")
    page.wait_for_selector("#dm-app:not([hidden])")


def answer_roots(page, value):
    page.fill(ROOTS_BOX, value)
    page.wait_for_timeout(200)


def stored(page):
    """Every dewmark record in this browser profile's storage, parsed."""
    return page.evaluate("""() => {
        const out = {};
        for (const key of Object.keys(localStorage)) {
            if (key.startsWith("dewmark")) {
                try { out[key] = JSON.parse(localStorage.getItem(key)); }
                catch (e) { out[key] = localStorage.getItem(key); }
            }
        }
        return out;
    }""")


def holds_roots(records, value):
    """True if some stored record has `value` in the a3.roots box."""
    return any(value in json.dumps((record or {}).get("answers", {}).get("a3.roots"))
               for record in records.values() if isinstance(record, dict))


def sit_and_leave(context, path, value):
    page = open_page(context, path)
    begin(page)
    answer_roots(page, value)
    page.close()


# --- A: the start screen must never write -------------------------------

def test_a_reload_on_the_start_screen_keeps_the_saved_answers(context, built):
    sit_and_leave(context, built["student"], "4")
    page = open_page(context, built["student"])
    page.wait_for_selector(".dm-restore-note")
    page.reload()
    page.wait_for_selector(".dm-restore-note")
    assert holds_roots(stored(page), "4")
    page.click(".dm-restore-note button")
    page.wait_for_selector("#dm-app:not([hidden])")
    assert page.input_value(ROOTS_BOX) == "4"
    assert not page.errors


def test_a_closing_the_start_screen_keeps_the_saved_answers(context, built):
    sit_and_leave(context, built["student"], "4")
    page = open_page(context, built["student"])
    page.wait_for_selector(".dm-restore-note")
    page.close(run_before_unload=True)
    check = open_page(context, built["student"])
    assert holds_roots(stored(check), "4")


def test_a_beginning_again_sets_the_saved_answers_aside_rather_than_deleting_them(
        context, built):
    sit_and_leave(context, built["student"], "4")
    page = open_page(context, built["student"], accept_dialogs=True)
    page.wait_for_selector(".dm-restore-note")
    begin(page)
    assert page.input_value(ROOTS_BOX) == ""
    answer_roots(page, "9")
    records = stored(page)
    assert holds_roots(records, "4"), "the earlier answers were deleted"
    assert holds_roots(records, "9")
    assert not page.errors


# --- B: one exam's three pages keep separate slots ---------------------

def test_b_the_practice_paper_does_not_offer_the_student_papers_work(context, built):
    sit_and_leave(context, built["student"], "4")
    practice = open_page(context, built["practice"])
    practice.wait_for_timeout(300)
    assert practice.locator(".dm-restore-note").count() == 0
    begin(practice)
    answer_roots(practice, "7")
    practice.close()
    student = open_page(context, built["student"])
    student.wait_for_selector(".dm-restore-note")
    student.click(".dm-restore-note button")
    student.wait_for_selector("#dm-app:not([hidden])")
    assert student.input_value(ROOTS_BOX) == "4"


def test_b_the_answer_key_never_saves(context, built):
    key = open_page(context, built["answer_key"])
    begin(key)
    answer_roots(key, "5")
    key.reload()
    assert stored(key) == {}


# --- the second window --------------------------------------------------

def test_a_second_window_never_writes_over_the_first(context, built):
    first = open_page(context, built["student"])
    begin(first)
    answer_roots(first, "4")
    second = open_page(context, built["student"])
    second.wait_for_timeout(500)
    assert second.is_disabled("#dm-begin")
    second.close(run_before_unload=True)
    assert holds_roots(stored(first), "4")
    assert first.input_value(ROOTS_BOX) == "4"


# --- G: the workbench reads only submissions ----------------------------

def test_g_the_workbench_counts_only_submissions_as_students(context, built, tmp_path):
    page = open_page(context, built["student"])
    begin(page)
    answer_roots(page, "4")
    page.click("#dm-finish")
    with page.expect_download() as caught:
        page.click("#dm-submit")
    submission = tmp_path / caught.value.suggested_filename
    caught.value.save_as(submission)
    assert zipfile.is_zipfile(submission)

    record = tmp_path / "dewmark_sample-mixed-2027_marking_record.json"
    record.write_text(json.dumps({"exam_code": "sample-mixed-2027", "papers": {}}))

    bench = open_page(context, WORKBENCH)
    with bench.expect_file_chooser() as chooser:
        bench.click("#load-scheme")
    chooser.value.set_files(str(built["scheme"]))
    bench.wait_for_selector("#scheme-pill.ok")
    with bench.expect_file_chooser() as chooser:
        bench.click("#load-subs")
    chooser.value.set_files([str(built["scheme"]), str(record), str(submission)])
    bench.wait_for_selector("#class-table tr.clickable")
    assert bench.locator("#class-table tr.clickable").count() == 1
    assert not bench.errors
