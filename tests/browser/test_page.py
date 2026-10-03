"""Rehearsals for the page the new builder makes (dewmark/build.py).

The bugs these guard against live in the page, not the builder, so each test
sits a paper in a real Chromium and looks at what browser storage and the
downloaded files hold afterwards. They carry the step-2 rehearsals
(tests/browser/test_saving.py) over to the new page, and cover what only the
new page has: a registry of answer kinds that each save and restore in a fixed
shape, an answer file that is checked rather than trusted, a page that
connects to nothing, the two screens before the paper, saved work offered only
once its owner's number is typed, reading settings that belong to the computer
and never to the answer file, and a list of what the paper needs.

The paper is one with every kind of box the page draws (conftest.py,
REHEARSAL_PAPER); its boxes are named for their parts, q1a to q3d. Chromium
cannot show a file-save window to a test, so a page gets a stand-in for
window.showSaveFilePicker that keeps what is written in memory (FAKE_PICKER).
"""

import hashlib
import json
import re

import pytest

from dewmark.build import build_pages
from dewmark.receipt import canonical, receipt

from helpers import (  # noqa: E402
    BLOCKED_PICKER, BROKEN_STORAGE, CANCELLED_PICKER, EVERYTHING, FAKE_PICKER, KEY, NO_PICKER, READING,
    WRITING, answer_file, begin, choose_folder, downloads_of_both, fill_everything, finish_and_download,
    folder_bytes, folder_names, holds, next_screen, open_page, press_begin, resume, save_both,
    sit_and_leave, stored, type_details, wait_for, write)


# --- the two screens ----------------------------------------------------------------------------------------

def test_the_page_opens_on_the_start_screen_and_the_paper_is_not_in_view(context, pages):
    page = open_page(context, pages["student"])
    assert page.is_visible("#dm-start") and page.is_hidden("#dm-before") and page.is_hidden("#dm-app")
    assert page.is_visible("#dm-checklist") and page.is_visible(".dm-band")
    assert not page.errors


def test_next_goes_to_before_you_begin_back_returns_and_begin_enters_the_paper(context, pages):
    page = open_page(context, pages["student"])
    type_details(page)
    next_screen(page)
    assert page.is_hidden("#dm-start")
    assert page.evaluate("document.activeElement.id") == "dm-before-h"
    assert "Instructions to candidates" in page.text_content("#dm-before")
    page.click("#dm-back")
    assert page.is_visible("#dm-start") and page.input_value("#dm-name") == "Agnes Nitt"
    assert page.evaluate("document.activeElement.id") == "dm-start-h"
    next_screen(page)
    choose_folder(page)
    press_begin(page)
    assert page.is_hidden("#dm-start") and page.is_hidden("#dm-before")
    assert page.text_content("#dm-top-student") == "Agnes Nitt · S12345"
    assert not page.errors


def test_enter_in_a_field_is_next_not_a_form_sent_anywhere(context, pages):
    page = open_page(context, pages["student"])
    type_details(page)
    page.press("#dm-number", "Enter")
    page.wait_for_selector("#dm-before:not([hidden])")
    assert page.url.startswith("file:") and not page.errors


def test_each_detail_is_asked_for_in_words_before_next(context, pages):
    page = open_page(context, pages["student"])
    page.click("#dm-next")
    assert page.text_content("#dm-name-err") == "Type your full name."
    assert page.text_content("#dm-number-err") == "Type your student number."
    assert page.get_attribute("#dm-name", "aria-invalid") == "true"
    assert page.evaluate("document.activeElement.id") == "dm-name"
    assert page.is_visible("#dm-start") and page.is_hidden("#dm-before")
    page.fill("#dm-name", "A")
    assert page.is_hidden("#dm-name-err") and page.get_attribute("#dm-name", "aria-invalid") is None
    assert page.is_visible("#dm-number-err")
    assert stored(page) == {}, "the start screen wrote something"


def test_the_start_screen_writes_nothing_however_far_the_student_gets(context, pages):
    page = open_page(context, pages["student"])
    type_details(page)
    next_screen(page)
    choose_folder(page)
    page.click("#dm-back")
    page.click('[name="start-font"][value="sans"]')
    assert set(stored(page)) == {READING}, "only the reading settings may be written before Begin"


# --- the start screen must never write -------------------------------------------------------------------------

def test_a_reload_on_the_start_screen_keeps_the_saved_answers(context, pages):
    sit_and_leave(context, pages["student"], "4")
    page = open_page(context, pages["student"])
    page.reload()
    assert holds(stored(page), "q1a", "4")
    resume(page)
    assert page.input_value(WRITING) == "4"
    assert not page.errors


def test_closing_the_start_screen_keeps_the_saved_answers(context, pages):
    sit_and_leave(context, pages["student"], "4")
    page = open_page(context, pages["student"])
    page.fill("#dm-number", "S12345")
    page.close(run_before_unload=True)
    assert holds(stored(open_page(context, pages["student"])), "q1a", "4")


def test_starting_again_sets_the_saved_answers_aside_rather_than_deleting_them(context, pages):
    sit_and_leave(context, pages["student"], "4")
    page = open_page(context, pages["student"])
    page.fill("#dm-number", "S12345")
    page.fill("#dm-name", "Agnes Nitt")
    page.wait_for_selector("#dm-restore:not([hidden])")
    page.click("#dm-again")
    assert page.is_visible("#dm-again-text")
    next_screen(page)
    choose_folder(page)
    press_begin(page)
    assert page.input_value(WRITING) == ""
    write(page, "9")
    records = stored(page)
    assert holds(records, "q1a", "4"), "the earlier answers were deleted"
    assert holds(records, "q1a", "9")
    assert any(":set-aside:" in key for key in records)
    assert page.dialogs == [], "the student had already said so on the screen; no second question"
    assert not page.errors


def test_work_for_another_number_is_set_aside_not_overwritten_when_someone_else_begins(context, pages):
    sit_and_leave(context, pages["student"], "4", number="S12345")
    page = open_page(context, pages["student"], accept_dialogs=True)
    begin(page, name="Tiffany Aching", number="S99999")
    write(page, "7")
    records = stored(page)
    assert holds(records, "q1a", "4") and holds(records, "q1a", "7")
    assert any(":set-aside:" in key for key in records)
    assert page.dialogs and "saved work" in page.dialogs[0]


def test_declining_the_question_about_another_students_work_changes_nothing(context, pages):
    sit_and_leave(context, pages["student"], "4", number="S12345")
    page = open_page(context, pages["student"], accept_dialogs=False)
    type_details(page, "Tiffany Aching", "S99999")
    next_screen(page)
    choose_folder(page)
    page.click("#dm-begin")
    page.wait_for_timeout(300)
    assert page.is_hidden("#dm-app") and page.is_visible("#dm-before")
    records = stored(page)
    assert holds(records, "q1a", "4") and not any(":set-aside:" in key for key in records)


# --- saved work is offered once its owner's number is typed ----------------------------------------------------------------

def test_saved_work_is_not_offered_before_a_number_is_typed_or_to_another_number(context, pages):
    sit_and_leave(context, pages["student"], "4", number="S12345")
    page = open_page(context, pages["student"])
    assert page.is_hidden("#dm-restore")
    assert "answers" not in page.text_content("#dm-start").replace("Reading settings", "")
    page.fill("#dm-number", "S99999")
    assert page.is_hidden("#dm-restore")
    page.fill("#dm-number", "s1234")
    assert page.is_hidden("#dm-restore")


def test_saved_work_is_offered_for_its_own_number_in_any_capitals_with_its_count_and_time(context, pages):
    sit_and_leave(context, pages["student"], "4", number="S12345")
    page = open_page(context, pages["student"])
    page.fill("#dm-number", "  s12345 ")
    page.wait_for_selector("#dm-restore:not([hidden])")
    text = page.text_content("#dm-restore-text")
    assert "1 answer," in text and "last saved" in text
    page.fill("#dm-number", "S9")
    assert page.is_hidden("#dm-restore")


def test_this_is_not_my_number_clears_the_number_and_the_offer(context, pages):
    sit_and_leave(context, pages["student"], "4")
    page = open_page(context, pages["student"])
    page.fill("#dm-number", "S12345")
    page.wait_for_selector("#dm-restore:not([hidden])")
    page.click("#dm-not-me")
    assert page.input_value("#dm-number") == "" and page.is_hidden("#dm-restore")
    assert page.evaluate("document.activeElement.id") == "dm-number"


def test_next_asks_for_a_choice_while_saved_work_is_on_offer(context, pages):
    sit_and_leave(context, pages["student"], "4")
    page = open_page(context, pages["student"])
    type_details(page)
    page.wait_for_selector("#dm-restore:not([hidden])")
    page.click("#dm-next")
    assert "Choose Continue my work or Start again first." in page.text_content("#dm-restore-err")
    assert page.is_visible("#dm-start") and page.is_hidden("#dm-before")


def test_continuing_keeps_the_spelling_of_the_name_the_work_was_saved_under(context, pages):
    sit_and_leave(context, pages["student"], "4")
    page = open_page(context, pages["student"])
    page.fill("#dm-name", "agnes nitt")
    page.fill("#dm-number", "S12345")
    page.wait_for_selector("#dm-restore:not([hidden])")
    page.click("#dm-continue")
    page.wait_for_selector("#dm-before:not([hidden])")
    assert "Your work is ready to continue: 1 answer, saved" in page.text_content("#dm-resume-line")
    assert page.input_value("#dm-name") == "Agnes Nitt"


def test_changing_the_number_after_continuing_lets_the_saved_work_go(context, pages):
    sit_and_leave(context, pages["student"], "4")
    page = open_page(context, pages["student"])
    page.fill("#dm-name", "Agnes Nitt")
    page.fill("#dm-number", "S12345")
    page.wait_for_selector("#dm-restore:not([hidden])")
    page.click("#dm-continue")
    page.wait_for_selector("#dm-before:not([hidden])")
    page.click("#dm-back")
    page.fill("#dm-number", "S77777")
    next_screen(page)
    assert page.is_hidden("#dm-resume-line")
    choose_folder(page)
    page.click("#dm-begin")
    page.wait_for_timeout(300)
    assert page.is_hidden("#dm-app"), "another student's saved work must raise the question"
    assert page.dialogs and "saved work" in page.dialogs[0]


def test_correcting_the_name_after_continuing_keeps_the_work_and_the_corrected_name(context, pages):
    sit_and_leave(context, pages["student"], "4")
    page = open_page(context, pages["student"])
    page.fill("#dm-name", "Agnes Nitt")
    page.fill("#dm-number", "S12345")
    page.wait_for_selector("#dm-restore:not([hidden])")
    page.click("#dm-continue")
    page.wait_for_selector("#dm-before:not([hidden])")
    page.click("#dm-back")
    page.fill("#dm-name", "Agnes Nitt-Smith")
    next_screen(page)
    assert page.is_visible("#dm-resume-line")
    choose_folder(page)
    press_begin(page)
    assert page.input_value(WRITING) == "4"
    assert stored(page)[KEY]["student"] == {"full name": "Agnes Nitt-Smith", "student number": "S12345"}
    assert page.dialogs == []


# --- one paper's pages keep separate slots ---------------------------------------------------------------------

def test_the_practice_page_does_not_offer_the_student_pages_work(context, pages):
    sit_and_leave(context, pages["student"], "4")
    practice = open_page(context, pages["practice"])
    practice.fill("#dm-number", "S12345")
    practice.wait_for_timeout(300)
    assert practice.is_hidden("#dm-restore")
    begin(practice)
    write(practice, "7")
    practice.close()
    student = open_page(context, pages["student"])
    resume(student)
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
    assert second.is_disabled("#dm-next") and second.is_disabled("#dm-load-file")
    type_details(second)
    second.press("#dm-number", "Enter")
    second.wait_for_timeout(200)
    assert second.is_hidden("#dm-before"), "Enter must not get past a disabled Next"
    second.close(run_before_unload=True)
    assert holds(stored(first), "q1a", "4")
    assert first.input_value(WRITING) == "4"


# --- where the files go -----------------------------------------------------------------------------------------------

def test_a_chosen_folder_gets_the_answer_file_as_the_student_works(context, pages):
    page = open_page(context, pages["student"])
    begin(page)
    write(page, "alpha")
    wait_for(page, "Object.keys(window.__folder).some((n) => window.__folder[n].length > 0)")
    assert folder_names(page) == ["dewmark_rehearsal_s12345_agnes-nitt.json"]
    record = answer_file(page)
    assert record["answers"] == {"q1a": "alpha"} and record["student"]["student number"] == "S12345"
    assert "File ✓" in page.text_content("#dm-save-file")


def test_the_status_names_the_folder_and_the_file_that_were_chosen(context, pages):
    page = open_page(context, pages["student"])
    type_details(page)
    next_screen(page)
    page.click("#dm-choose-folder")
    wait_for(page, "document.getElementById('dm-file-status').textContent.length > 0")
    status = page.text_content("#dm-file-status")
    assert "answers-folder" in status and "dewmark_rehearsal_s12345_agnes-nitt.json" in status
    assert "puts your PDF there when you finish" in status
    assert page.text_content("#dm-choose-folder").startswith("Choose a different folder")


def test_a_browser_that_cannot_save_into_a_folder_says_so_and_still_begins(context, pages):
    page = open_page(context, pages["student"], picker=NO_PICKER)
    type_details(page)
    next_screen(page)
    assert page.is_hidden("#dm-choose-folder")
    assert "downloads files instead of saving into a folder" in page.text_content("#dm-file-status")
    press_begin(page)
    assert page.dialogs == [] and "File saving is off" in page.text_content("#dm-save-file")


def test_a_student_who_cancels_the_folder_window_is_told_and_may_begin(context, pages):
    page = open_page(context, pages["student"], picker=CANCELLED_PICKER)
    type_details(page)
    next_screen(page)
    page.click("#dm-choose-folder")
    wait_for(page, "document.getElementById('dm-file-status').textContent.length > 0")
    assert "No folder was chosen" in page.text_content("#dm-file-status")
    press_begin(page)
    assert page.dialogs == []


def test_a_folder_the_browser_refuses_is_explained_with_where_to_try_instead(context, pages):
    page = open_page(context, pages["student"], picker=BLOCKED_PICKER)
    type_details(page)
    next_screen(page)
    page.click("#dm-choose-folder")
    wait_for(page, "document.getElementById('dm-file-status').textContent.length > 0")
    status = page.text_content("#dm-file-status")
    assert "did not let the page use that folder" in status and "USB stick" in status and "Documents" in status
    press_begin(page)
    assert page.dialogs == []


def test_begin_without_choosing_a_folder_asks_once_and_the_student_may_go_back_and_choose(context, pages):
    page = open_page(context, pages["student"], accept_dialogs=False)
    type_details(page)
    next_screen(page)
    page.click("#dm-begin")
    page.wait_for_timeout(300)
    assert page.is_hidden("#dm-app") and "You have not chosen a folder for your files" in page.dialogs[0]
    accepting = open_page(context, pages["practice"], accept_dialogs=True)
    type_details(accepting)
    next_screen(accepting)
    press_begin(accepting)
    assert "You have not chosen" in accepting.dialogs[0]


def test_changing_the_name_after_choosing_the_folder_saves_into_the_file_for_the_new_name(context, pages):
    page = open_page(context, pages["student"])
    type_details(page, "Agnes Nitt", "S12345")
    next_screen(page)
    choose_folder(page)
    page.click("#dm-back")
    page.fill("#dm-name", "Tiffany Aching")
    next_screen(page)
    press_begin(page)
    write(page, "x")
    wait_for(page, "Object.keys(window.__folder).some((n) => n.includes('tiffany') && window.__folder[n].length > 0)")
    assert any("tiffany-aching" in name for name in folder_names(page))
    assert json.loads(folder_bytes(page, next(n for n in folder_names(page) if "tiffany" in n)))["student"][
        "full name"] == "Tiffany Aching"


# --- every kind saves in its shape and comes back --------------------------------------------------------------

def test_every_kind_is_saved_in_its_own_shape(context, pages):
    page = open_page(context, pages["student"])
    begin(page)
    fill_everything(page)
    record = stored(page)[KEY]
    assert record["answers"] == EVERYTHING
    assert record["format"] == "dewmark-answers/1"
    code = record["exam"].pop("fingerprint")
    assert re.fullmatch(r"[0-9A-HJKMNP-TV-Z]{3}-[0-9A-HJKMNP-TV-Z]{3}", code)
    assert record["exam"] == {"code": "rehearsal", "version": "1", "title": "Rehearsal Paper"}
    assert record["page"] == "student"
    assert record["student"] == {"full name": "Agnes Nitt", "student number": "S12345"}
    assert record["started_at"] and record["saved_at"]
    assert record["finished_at"] is None and record["receipt"] is None
    assert not page.errors


def test_every_kind_comes_back_after_a_reload(context, pages):
    page = open_page(context, pages["student"])
    begin(page)
    fill_everything(page)
    page.reload()
    resume(page)
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
    assert page.evaluate("document.activeElement.id") == "dm-finish-h"
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
    save_both(page)
    assert sorted(folder_names(page)) == ["dewmark_rehearsal_s12345_agnes-nitt.json",
                                          "dewmark_rehearsal_s12345_agnes-nitt.pdf"]
    record = answer_file(page)
    assert record["answers"] == EVERYTHING and record["finished_at"]
    assert record["student"] == {"full name": "Agnes Nitt", "student number": "S12345"}
    assert stored(page)[KEY]["finished_at"] == record["finished_at"]


def test_an_answer_file_loads_into_a_fresh_browser_and_the_work_is_back(
        context, browser, pages, tmp_path):
    page = open_page(context, pages["student"])
    begin(page)
    fill_everything(page)
    save_both(page)
    file = tmp_path / "handed-in.json"
    file.write_text(json.dumps(answer_file(page)))

    other = browser.new_context(accept_downloads=True)
    try:
        fresh = open_page(other, pages["student"])
        with fresh.expect_file_chooser() as chooser:
            fresh.click("#dm-load-file")
        chooser.value.set_files(str(file))
        fresh.wait_for_selector("#dm-before:not([hidden])")
        assert "Your work is ready to continue: 9 answers" in fresh.text_content("#dm-resume-line")
        choose_folder(fresh)
        press_begin(fresh)
        assert fresh.input_value('[data-answer="q1b"] textarea') == "x = 2"
        assert fresh.is_checked('[data-answer="q3a"] input[value="C"]')
        assert stored(fresh)[KEY]["answers"] == EVERYTHING
        assert fresh.text_content("#dm-top-student") == "Agnes Nitt · S12345"
        assert not fresh.errors
    finally:
        other.close()


def test_choosing_a_file_over_different_work_in_the_browser_keeps_the_browsers_work_aside(
        context, pages, tmp_path):
    other = open_page(context, pages["student"])
    begin(other, name="Tiffany Aching", number="S99999")
    write(other, "browser work")
    other.close()
    file = tmp_path / "file.json"
    file.write_text(json.dumps(good_record(
        student={"full name": "Agnes Nitt", "student number": "S12345"},
        answers={"q1a": "file work"})))
    page = open_page(context, pages["student"], accept_dialogs=True)
    load(page, file)
    page.wait_for_selector("#dm-before:not([hidden])")
    assert page.dialogs and "This browser also holds saved work" in page.dialogs[0]
    records = stored(page)
    assert holds(records, "q1a", "browser work") and any(":set-aside:" in key for key in records)
    choose_folder(page)
    press_begin(page)
    assert page.input_value(WRITING) == "file work"
    assert stored(page)[KEY]["answers"] == {"q1a": "file work"}
    aside = [v for k, v in stored(page).items() if ":set-aside:" in k]
    assert aside and aside[0]["answers"] == {"q1a": "browser work"}


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
def test_a_file_that_is_not_an_answer_file_for_this_paper_is_refused_in_words(
        context, pages, tmp_path, name, content):
    file = tmp_path / name
    file.write_text(content)
    page = open_page(context, pages["student"])
    load(page, file)
    assert "Nothing has changed." in page.text_content("#dm-file-msg")
    assert page.is_hidden("#dm-before") and page.is_visible("#dm-start")
    assert stored(page) == {} and not page.errors and page.dialogs == []


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
    page.wait_for_selector("#dm-before:not([hidden])")
    choose_folder(page)
    press_begin(page)
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
    assert html.count("<script") == 0
    assert "<textarea" not in html and "<input" not in html and "<select" not in html
    assert "&lt;/textarea&gt;&lt;script&gt;window.hacked=1&lt;/script&gt;" in html
    assert "x = 2" in html and "print(2)" in html and "stem" in html and "leaves" in html
    assert "Agnes Nitt" in html and "Readable copy of a dewmark answer file" in html
    assert "@font-face" not in html, "the reading fonts are not carried into a copy"
    for furniture in ('id="dm-drawer"', 'id="dm-scrim"', 'id="dm-aa"', 'id="dm-start"',
                      'id="dm-before"', 'id="dm-ruler"', 'id="dm-finish-screen"'):
        assert furniture not in html, furniture

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
    page.add_init_script(FAKE_PICKER)
    page.goto(pages["student"].resolve().as_uri())
    begin(page)
    fill_everything(page)
    page.evaluate("""() => {
        fetch("https://example.invalid/steal").catch(() => {});
        const img = new Image(); img.src = "https://example.invalid/pixel.png";
        new FontFace("x", "url(https://example.invalid/f.woff2)").load().catch(() => {});
        const form = document.createElement("form");
        form.action = "https://example.invalid/post"; form.method = "post";
        document.body.appendChild(form);
        try { form.submit(); } catch (e) {}
    }""")
    page.wait_for_timeout(500)
    # Chromium names a blocked picture as a request that failed; none finished.
    assert [u for u in reached if not u.startswith("file:")] == []
    assert {"connect-src", "img-src", "form-action", "font-src"} <= set(violations)


def test_none_of_the_three_screens_scrolls_sideways_even_at_the_largest_text(context, pages):
    page = context.new_page()
    page.add_init_script(FAKE_PICKER)
    page.set_viewport_size({"width": 1024, "height": 768})
    page.goto(pages["student"].resolve().as_uri())
    page.eval_on_selector('#dm-start [data-setting="size"]',
                          "(el) => { el.value = 32; el.dispatchEvent(new Event('input', {bubbles: true})); }")
    fits = "document.documentElement.scrollWidth <= window.innerWidth"
    assert page.evaluate(fits), "the start screen"
    type_details(page)
    next_screen(page)
    assert page.evaluate(fits), "before you begin"
    choose_folder(page)
    press_begin(page)
    assert page.evaluate(fits), "the paper"


# --- reading settings -----------------------------------------------------------------------------------------------

def body_style(page, prop):
    return page.evaluate(f"getComputedStyle(document.body).{prop}")


def test_nothing_is_written_for_reading_settings_until_one_is_changed(context, pages):
    page = open_page(context, pages["student"])
    type_details(page)
    next_screen(page)
    assert stored(page) == {}
    assert page.evaluate("document.documentElement.getAttribute('data-scheme')") is None


def test_the_settings_change_the_page_at_once_and_are_kept_on_this_computer(context, pages):
    page = open_page(context, pages["student"])
    page.click('#dm-start [name="start-font"][value="lexend"]')
    assert "Lexend" in body_style(page, "fontFamily")
    page.click('#dm-start [data-step="size"][data-d="1"]')
    assert page.evaluate("getComputedStyle(document.documentElement).fontSize") == "19px"
    assert page.text_content('#dm-start [data-out="size"]') == "19"
    page.click('#dm-start [name="start-scheme"][value="dark"]')
    assert page.evaluate("document.documentElement.getAttribute('data-scheme')") == "dark"
    assert body_style(page, "backgroundColor") == "rgb(23, 28, 36)"
    page.click('#dm-start [data-setting="ruler"]')
    assert page.evaluate("document.documentElement.getAttribute('data-ruler')") == "on"
    page.click("#dm-start .dm-more summary")
    page.click('#dm-start [name="start-spacing"][value="wide"]')
    page.click('#dm-start [name="start-width"][value="84ch"]')
    page.click('#dm-start [data-setting="wrap"]')
    page.click('#dm-start [name="start-codeScheme"][value="light"]')
    assert stored(page) == {READING: {
        "font": "lexend", "size": 19, "scheme": "dark", "ruler": True, "lineHeight": 1.6,
        "spacing": "wide", "width": "84ch", "motion": False, "codeSize": 16,
        "codeScheme": "light", "wrap": True}}
    assert not page.errors


def test_the_settings_are_there_when_the_page_is_opened_again_with_a_note_and_a_way_back(context, pages):
    page = open_page(context, pages["student"])
    page.click('#dm-start [name="start-scheme"][value="cream"]')
    page.click('#dm-start [name="start-font"][value="dyslexic"]')
    page.close()
    again = open_page(context, pages["student"])
    assert again.evaluate("document.documentElement.getAttribute('data-scheme')") == "cream"
    assert "OpenDyslexic" in body_style(again, "fontFamily")
    assert again.is_checked('#dm-start [name="start-font"][value="dyslexic"]')
    assert again.is_visible("#dm-start [data-kept]")
    assert "kept on this computer" in again.text_content("#dm-start [data-kept]")
    again.click("#dm-start [data-reset]")
    assert again.evaluate("document.documentElement.getAttribute('data-scheme')") is None
    assert "OpenDyslexic" not in body_style(again, "fontFamily")
    assert stored(again) == {} and again.is_hidden("#dm-start [data-kept]")
    assert again.is_checked('#dm-start [name="start-font"][value="serif"]')


def test_reading_settings_are_never_in_the_answer_file_or_the_record(context, pages, tmp_path):
    page = open_page(context, pages["student"])
    page.click('#dm-start [name="start-font"][value="dyslexic"]')
    page.click('#dm-start [data-step="size"][data-d="1"]')
    begin(page)
    write(page, "x")
    save_both(page)
    text = json.dumps(answer_file(page))
    for word in ("dyslexic", "OpenDyslexic", "size", "scheme", "reading", "font"):
        assert word not in text, word
    assert "dyslexic" not in json.dumps(stored(page)[KEY])
    with page.expect_download() as caught:
        page.click("#dm-save-readable")
    caught.value.save_as(tmp_path / "copy.html")
    copy = (tmp_path / "copy.html").read_text()
    # The copy carries the page's stylesheet, so the word is in it; what must not be
    # there is the student's choice: no attribute on the page, no inline variable.
    assert re.search(r"<html[^>]*>", copy).group(0) == '<html lang="en-IE">'
    assert 'style="--dm' not in copy and "--dm-size:" not in copy.split("</style>")[-1]


@pytest.mark.parametrize("raw", [
    json.dumps({"size": 9999, "font": "<script>", "scheme": "javascript:", "width": "expression(1)",
                "lineHeight": "tall", "codeSize": -5, "ruler": "yes", "unknown": 1, "wrap": 1,
                "spacing": ["wide"], "codeScheme": {"x": 1}, "motion": "true"}),
    "this is not json", json.dumps([1, 2, 3]), json.dumps("a string"), "null"])
def test_stored_settings_that_are_wrong_or_hostile_become_standard_ones(context, pages, raw):
    page = open_page(context, pages["student"])
    page.evaluate("(raw) => localStorage.setItem('dewmark:reading-settings', raw)", raw)
    page.reload()
    root = "document.documentElement"
    assert page.evaluate(f"{root}.getAttribute('data-scheme')") is None
    assert page.evaluate(f"{root}.getAttribute('data-ruler')") is None
    assert page.evaluate(f"{root}.getAttribute('data-wrap')") is None
    assert page.evaluate(f"{root}.style.getPropertyValue('--dm-font-body')") == "var(--dm-ff-serif)"
    assert page.evaluate(f"{root}.style.getPropertyValue('--dm-measure')") == "68ch"
    expected = "32" if raw.startswith('{"size"') else "18"
    assert page.evaluate(f"{root}.style.getPropertyValue('--dm-size')") == expected
    assert page.evaluate("document.querySelectorAll('script').length") == 3, \
        "the page has its data, its fonts and its script, and nothing a setting could add"
    assert not page.errors


def test_match_my_computer_follows_the_computers_scheme_until_one_is_chosen(context, pages):
    page = open_page(context, pages["student"])
    page.emulate_media(color_scheme="dark")
    assert body_style(page, "backgroundColor") == "rgb(23, 28, 36)"
    page.click('#dm-start [name="start-scheme"][value="light"]')
    assert body_style(page, "backgroundColor") == "rgb(253, 252, 250)"
    page.click('#dm-start [name="start-scheme"][value=""]')
    assert body_style(page, "backgroundColor") == "rgb(23, 28, 36)"
    page.emulate_media(color_scheme="light")
    assert body_style(page, "backgroundColor") == "rgb(253, 252, 250)"


def test_reduce_motion_is_on_by_itself_when_the_computer_asks_for_it(context, pages):
    page = context.new_page()
    page.emulate_media(reduced_motion="reduce")
    page.goto(pages["student"].resolve().as_uri())
    assert page.evaluate("document.documentElement.getAttribute('data-motion')") == "reduce"
    page.click("#dm-start .dm-more summary")
    assert page.is_checked('#dm-start [data-setting="motion"]')
    assert stored(page) == {}


def test_the_drawer_opens_on_aa_traps_the_keyboard_and_closes_on_escape(context, pages):
    page = open_page(context, pages["student"])
    page.focus("#dm-aa")
    page.keyboard.press("Enter")
    assert page.is_visible("#dm-drawer") and page.evaluate("document.activeElement.id") == "dm-drawer-close"
    assert page.evaluate("document.getElementById('dm-start').inert")
    assert page.get_attribute("#dm-drawer", "role") == "dialog"
    page.click('#dm-drawer [name="drawer-font"][value="sans"]')
    assert page.is_checked('#dm-start [name="start-font"][value="sans"]'), "the two copies of a setting agree"
    page.keyboard.press("Escape")
    assert page.is_hidden("#dm-drawer") and page.evaluate("document.activeElement.id") == "dm-aa"
    assert not page.evaluate("document.getElementById('dm-start').inert")


def test_the_drawer_works_on_the_paper_and_the_finish_screen(context, pages):
    page = open_page(context, pages["student"])
    begin(page)
    page.click("#dm-aa")
    page.click('#dm-drawer [data-step="size"][data-d="1"]')
    page.click("#dm-drawer-close")
    assert page.evaluate("getComputedStyle(document.documentElement).fontSize") == "19px"
    page.click("#dm-finish")
    page.click("#dm-aa")
    assert page.is_visible("#dm-drawer")
    page.click("#dm-scrim", position={"x": 5, "y": 5})
    assert page.is_hidden("#dm-drawer")


def test_the_reading_ruler_follows_the_pointer_and_the_line_being_typed(context, pages):
    page = open_page(context, pages["student"])
    page.click('#dm-start [data-setting="ruler"]')
    assert page.evaluate("getComputedStyle(document.getElementById('dm-ruler')).display") == "block"
    page.mouse.move(300, 500)
    top = page.evaluate("document.getElementById('dm-ruler').getBoundingClientRect().top")
    height = page.evaluate("document.getElementById('dm-ruler').getBoundingClientRect().height")
    assert abs(top + height / 2 - 500) < 2 and height > 10
    page.mouse.move(300, 200)
    assert page.evaluate("document.getElementById('dm-ruler').getBoundingClientRect().top") < top
    begin(page)
    page.click(WRITING)
    page.keyboard.type("first line")
    first = page.evaluate("(() => { const r = document.getElementById('dm-ruler').getBoundingClientRect(); return r.top + r.height / 2; })()")
    page.keyboard.press("Enter")
    page.keyboard.type("second line")
    second = page.evaluate("(() => { const r = document.getElementById('dm-ruler').getBoundingClientRect(); return r.top + r.height / 2; })()")
    box = page.evaluate("(() => { const r = document.querySelector('[data-answer=q1a] textarea').getBoundingClientRect(); return [r.top, r.bottom]; })()")
    assert box[0] < first < second < box[1]
    assert second - first > 15, "the ruler moved down a line"


def test_off_the_ruler_is_hidden_and_does_not_follow(context, pages):
    page = open_page(context, pages["student"])
    assert page.evaluate("getComputedStyle(document.getElementById('dm-ruler')).display") == "none"


# --- what the paper needs --------------------------------------------------------------------------------------------

def states(page):
    return page.evaluate("""() => Object.fromEntries([...document.querySelectorAll('#dm-checklist li')]
        .map((li) => [li.dataset.need, [li.dataset.state, li.querySelector('.dm-cw').textContent]]))""")


def test_a_paper_that_needs_python_says_this_page_cannot_run_it_yet(context, pages):
    page = open_page(context, pages["student"])
    wait_for(page, "document.getElementById('dm-load-status').textContent.length > 0")
    assert states(page) == {
        "paper": ["ready", "Ready"], "fonts": ["ready", "Ready"],
        "python": ["problem", "Not ready"],
        "storage": ["ready", "Ready"], "file": ["ready", "Ready"]}
    assert "Something this paper needs is not ready. Tell your invigilator before you begin." in \
        page.text_content("#dm-load-status")
    page.close()
    press = open_page(context, pages["student"])
    type_details(press)
    next_screen(press)
    assert "not ready" in press.text_content("#dm-ready-line")


def test_a_paper_that_needs_nothing_to_load_is_ready(context, branded):
    page = open_page(context, branded["student"])
    wait_for(page, "document.getElementById('dm-load-status').textContent.length > 0")
    assert set(states(page)) == {"paper", "fonts", "storage", "file"}
    assert page.text_content("#dm-load-status") == "Everything this paper needs is ready."
    assert all(state == "ready" for state, _ in states(page).values())


def test_a_browser_that_keeps_nothing_says_so_in_the_list_and_the_student_can_still_go_on(context, branded):
    page = open_page(context, branded["student"], init=BROKEN_STORAGE)
    wait_for(page, "document.getElementById('dm-load-status').textContent.length > 0")
    assert states(page)["storage"] == ["problem", "Problem"]
    assert "Tell your invigilator" in page.text_content('#dm-checklist [data-need="storage"]')
    assert "not ready" in page.text_content("#dm-load-status")
    type_details(page)
    next_screen(page)
    assert page.is_enabled("#dm-begin")


def test_a_browser_that_downloads_instead_of_saving_into_a_folder_gets_a_note_not_a_problem(context, branded):
    page = open_page(context, branded["student"], picker=NO_PICKER)
    wait_for(page, "document.getElementById('dm-load-status').textContent.length > 0")
    assert states(page)["file"] == ["note", "Note"]
    assert "gives you two files when you finish" in page.text_content('#dm-checklist [data-need="file"]')
    assert page.text_content("#dm-load-status") == "Everything this paper needs is ready."


def test_the_storage_test_leaves_nothing_behind(context, branded):
    page = open_page(context, branded["student"])
    wait_for(page, "document.getElementById('dm-load-status').textContent.length > 0")
    assert stored(page) == {}


def test_the_answer_key_lists_nothing_about_saving(context, pages):
    page = open_page(context, pages["answer_key"])
    wait_for(page, "document.getElementById('dm-load-status').textContent.length > 0")
    assert set(states(page)) == {"paper", "fonts", "python"}


# --- the band -------------------------------------------------------------------------------------------------------

def test_the_band_carries_the_logo_and_the_names_and_says_what_kind_of_page_it_is(context, branded):
    page = open_page(context, branded["student"])
    band = page.text_content(".dm-band")
    assert "Examination" in band and "Branded Paper" in band
    assert "Dublin and Dún Laoghaire ETB · Dublin College Dundrum" in band
    assert "Testing (5N0000)" in band and "2026–2027" in band and "Time allowed: 30 minutes" in band
    assert page.evaluate("(() => { const i = document.querySelector('.dm-band-logo'); "
                         "return i.complete && i.naturalWidth > 0; })()")
    assert page.get_attribute(".dm-band-logo", "alt") == "Dublin and Dún Laoghaire ETB logo"
    practice = open_page(context, branded["practice"])
    assert "Practice version" in practice.text_content(".dm-band-kind")
    assert "As on your student card, for example D00123456." in page.text_content("#dm-number-hint")


def test_the_band_does_not_cover_the_aa_button_or_the_page_it_belongs_to(context, branded):
    page = context.new_page()
    page.set_viewport_size({"width": 420, "height": 800})
    page.add_init_script(FAKE_PICKER)
    page.goto(branded["student"].resolve().as_uri())
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    band = page.evaluate("document.querySelector('.dm-band-text').getBoundingClientRect().right")
    aa = page.evaluate("document.getElementById('dm-aa').getBoundingClientRect().left")
    assert band <= aa + 1


# --- receipts and the paper's fingerprint ---------------------------------------------------------------------------

SAMPLE_RECORD = {
    "format": "dewmark-answers/1",
    "exam": {"code": "x", "version": "1", "title": "T", "fingerprint": "7KQ-4MD"},
    "page": "student",
    "student": {"full name": "Síle Ní Bhriain", "student number": "D00123456"},
    "started_at": "2027-01-12T09:02:11.403Z",
    "saved_at": "2027-01-12T10:01:52.918Z",
    "finished_at": "2027-01-12T10:01:52.918Z",
    "answers": {"q1a": "x ≥ 5 😀\n\ttab \"q\" \\", "q1b": ["B", "A"]},
}


def test_the_pages_hash_agrees_with_pythons_for_every_length_that_matters(context, pages):
    page = open_page(context, pages["student"])
    for size in (0, 1, 3, 55, 56, 57, 63, 64, 65, 119, 120, 121, 1000, 100001):
        data = bytes((i * 37 + size) % 256 for i in range(size))
        got = page.evaluate("(bytes) => hex(sha256(Uint8Array.from(bytes)))", list(data))
        assert got == hashlib.sha256(data).hexdigest(), size


def test_the_pages_canonical_text_is_the_text_python_writes(context, pages):
    tricky = {
        "z": [1, None, True, {"b": "é", "a": "😀"}], "a": "\u007f\u0000\u001f",
        "\U0001F600": 1, "\uff5e": 2, "m": "quote \" backslash \\ tab \t newline \n",
        "q1a": "x ≥ 5", "": "", "Z": "\u2028\u2029", "__proto__": {"x": 1},
    }
    page = open_page(context, pages["student"])
    got = page.evaluate("(v) => canonicalJSON(JSON.parse(v))", json.dumps(tricky))
    assert got == canonical(json.loads(json.dumps(tricky)))


def test_the_pages_receipt_is_the_receipt_python_works_out_from_the_same_record(context, pages):
    page = open_page(context, pages["student"])
    assert page.evaluate("(r) => receiptOf(r)", SAMPLE_RECORD) == receipt(SAMPLE_RECORD) == "77FD 81FB"
    changed = {**SAMPLE_RECORD, "saved_at": "2030-01-01T00:00:00.000Z", "receipt": "0000 0000"}
    assert page.evaluate("(r) => receiptOf(r)", changed) == "77FD 81FB"


def saved_file(page, tmp_path=None):
    """Press the one button on the finish sheet; the answer file it put in the folder."""
    page.click("#dm-submit")
    page.wait_for_selector("#dm-saved:not([hidden]), #dm-problem:not([hidden])")
    return answer_file(page)


def test_saving_the_answer_file_gives_a_receipt_the_workbench_can_check_and_says_so(
        context, pages, tmp_path):
    page = open_page(context, pages["student"])
    begin(page)
    fill_everything(page)
    page.click("#dm-finish")
    record = saved_file(page)
    assert re.fullmatch(r"[0-9A-F]{4} [0-9A-F]{4}", record["receipt"])
    assert record["receipt"] == receipt(record), "Python must reach the page's receipt from the file"
    assert re.fullmatch(r"[0-9A-HJKMNP-TV-Z]{3}-[0-9A-HJKMNP-TV-Z]{3}", record["exam"]["fingerprint"])
    saved = page.text_content("#dm-saved")
    assert saved == (f"Checked: the file holds 9 answers. Receipt {record['receipt']}. The PDF has 2 pages. "
                     f"Both are in the folder answers-folder.")
    assert stored(page)[KEY]["receipt"] == record["receipt"]


def test_the_paper_id_on_the_second_screen_is_the_one_in_the_file(context, pages, tmp_path):
    page = open_page(context, pages["student"])
    type_details(page)
    next_screen(page)
    shown = re.search(r"Paper ID ([0-9A-Z-]+)\.", page.text_content("#dm-before")).group(1)
    choose_folder(page)
    press_begin(page)
    write(page, "x")
    page.click("#dm-finish")
    assert saved_file(page, tmp_path)["exam"]["fingerprint"] == shown


def test_a_change_after_saving_withdraws_the_receipt_and_asks_for_another_save(
        context, pages, tmp_path):
    page = open_page(context, pages["student"])
    begin(page)
    write(page, "first")
    page.click("#dm-finish")
    first = saved_file(page, tmp_path)
    assert page.is_hidden("#dm-changed") and page.is_visible("#dm-saved")
    page.click("#dm-keep-working")
    page.wait_for_selector("#dm-app:not([hidden])")
    write(page, "second")
    record = stored(page)[KEY]
    assert record["finished_at"] is None and record["receipt"] is None
    page.click("#dm-finish")
    assert page.is_visible("#dm-changed") and page.is_hidden("#dm-saved")
    assert "after you saved" in page.text_content("#dm-changed")
    second = saved_file(page, tmp_path)
    assert second["receipt"] != first["receipt"] and second["receipt"] == receipt(second)
    assert page.is_hidden("#dm-changed") and page.is_visible("#dm-saved")


def test_opening_the_finish_sheet_and_leaving_it_changes_nothing(context, pages, tmp_path):
    page = open_page(context, pages["student"])
    begin(page)
    write(page, "x")
    page.click("#dm-finish")
    saved_file(page, tmp_path)
    page.click("#dm-keep-working")
    page.click("#dm-finish")
    assert page.is_hidden("#dm-changed"), "looking is not changing"
    assert stored(page)[KEY]["receipt"] is not None


def test_work_continued_on_a_corrected_paper_is_kept_and_the_student_is_told(context, pages, tmp_path):
    sit_and_leave(context, pages["student"], "4")
    from conftest import REHEARSAL_PAPER, ROOT
    corrected = REHEARSAL_PAPER.replace("Say something.", "Say something clearly.")
    out = tmp_path / "corrected"
    out.mkdir()
    for name, text in build_pages(corrected, ROOT).items():
        (out / name).write_text(text, encoding="utf-8")
    page = open_page(context, out / "rehearsal.student.html")
    page.fill("#dm-name", "Agnes Nitt")
    page.fill("#dm-number", "S12345")
    page.wait_for_selector("#dm-restore:not([hidden])")
    page.click("#dm-continue")
    page.wait_for_selector("#dm-before:not([hidden])")
    assert "The paper has been corrected since you saved this work. Your answers are kept." in \
        page.text_content("#dm-resume-line")
    choose_folder(page)
    press_begin(page)
    assert page.input_value(WRITING) == "4"
    new_id = re.search(r"Paper ID ([0-9A-Z-]+)\.", page.text_content("#dm-before")).group(1)
    assert stored(page)[KEY]["exam"]["fingerprint"] == new_id


def test_work_continued_on_the_same_paper_is_not_told_it_was_corrected(context, pages):
    sit_and_leave(context, pages["student"], "4")
    page = open_page(context, pages["student"])
    page.fill("#dm-name", "Agnes Nitt")
    page.fill("#dm-number", "S12345")
    page.wait_for_selector("#dm-restore:not([hidden])")
    page.click("#dm-continue")
    page.wait_for_selector("#dm-before:not([hidden])")
    assert "corrected" not in page.text_content("#dm-resume-line")


# --- another version of the paper ---------------------------------------------------------------------------------------

def build_version(tmp_path, version):
    from conftest import REHEARSAL_PAPER, ROOT
    text = REHEARSAL_PAPER.replace("total marks: 18\n", f"total marks: 18\nversion: {version}\n")
    out = tmp_path / f"v{version}"
    out.mkdir()
    for name, body in build_pages(text, ROOT).items():
        (out / name).write_text(body, encoding="utf-8")
    return out / "rehearsal.student.html"


def test_work_saved_on_another_version_is_not_offered_and_is_set_aside_when_someone_begins(
        context, pages, tmp_path):
    sit_and_leave(context, pages["student"], "4")
    page = open_page(context, build_version(tmp_path, 2), accept_dialogs=True)
    page.fill("#dm-number", "S12345")
    page.wait_for_timeout(300)
    assert page.is_hidden("#dm-restore"), "work from version 1 must not be put into version 2"
    begin(page)
    assert page.input_value(WRITING) == "" and page.dialogs and "saved work" in page.dialogs[0]
    records = stored(page)
    assert any(":set-aside:" in key for key in records) and holds(records, "q1a", "4")
    assert stored(page)["dewmark:rehearsal:student"]["exam"]["version"] == "2"


def test_an_answer_file_from_another_version_is_refused_in_words(context, pages, tmp_path):
    file = tmp_path / "v1.json"
    file.write_text(json.dumps(good_record(answers={"q1a": "x"})))
    page = open_page(context, build_version(tmp_path, 3))
    load(page, file)
    message = page.text_content("#dm-file-msg")
    assert "saved on version 1 of this paper" in message and "this page is version 3" in message
    assert "Nothing has changed." in message
    assert page.is_hidden("#dm-before") and stored(page) == {}


def test_an_answer_file_from_the_same_version_still_loads(context, pages, tmp_path):
    file = tmp_path / "v1.json"
    file.write_text(json.dumps(good_record(answers={"q1a": "x"})))
    page = open_page(context, pages["student"])
    load(page, file)
    page.wait_for_selector("#dm-before:not([hidden])")
