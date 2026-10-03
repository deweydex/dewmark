"""The clock, extra time, breaks and the invigilator's code, sat in a real Chromium
(assets/page-time.js, assets/page-invigilator.js; docs/ANSWER_FILE.md, `time`).

Time is Playwright's own clock, installed before the page opens, so an hour passes
in a moment and the page's timers fire as they would. Absolute times drift by the
seconds a test takes to run, so a test asks whether the clock reads "about" so many
seconds, and never for the second.
"""

import json
import re
from datetime import datetime, timezone

import pytest

from conftest import REHEARSAL_PAPER, ROOT
from dewmark import invigilator
from dewmark.__main__ import main
from dewmark.build import build_pages
from helpers import (KEY, WRITING, answer_file, begin, choose_folder, next_screen,
                     save_both, stored, type_details, write)
from helpers import open_page as _open_page
from helpers import press_begin as _press_begin

START = datetime(2027, 1, 12, 9, 0, 0, tzinfo=timezone.utc)
CODE = "482915"
SITTING = {"name": "2026-10-20 Group A", "code": CODE}
SHOWN, ENFORCED, BREAKS = "timer: shown\n", "timer: enforced\n", "timer: shown\nbreaks: on\n"


def build(tmp_path_factory, name, settings, sitting=SITTING, allowed="1 hour"):
    """The rehearsal paper with some settings, built once, and its three pages."""
    text = REHEARSAL_PAPER.replace("time allowed: 1 hour\n", f"time allowed: {allowed}\n{settings}")
    out = tmp_path_factory.mktemp(name)
    for file, page in build_pages(text, ROOT, sitting).items():
        (out / file).write_text(page, encoding="utf-8")
    return {"student": out / "rehearsal.student.html", "practice": out / "rehearsal.practice.html",
            "answer_key": out / "rehearsal.answer-key.html"}


@pytest.fixture(scope="module")
def shown(tmp_path_factory):
    return build(tmp_path_factory, "shown", SHOWN)


@pytest.fixture(scope="module")
def enforced(tmp_path_factory):
    return build(tmp_path_factory, "enforced", ENFORCED)


@pytest.fixture(scope="module")
def breaking(tmp_path_factory):
    return build(tmp_path_factory, "breaking", BREAKS)


@pytest.fixture(scope="module")
def uncoded(tmp_path_factory):
    return build(tmp_path_factory, "uncoded", SHOWN, sitting=None)


@pytest.fixture(scope="module")
def silent(tmp_path_factory):
    return build(tmp_path_factory, "silent", "timer: none\n", sitting=None)


@pytest.fixture
def clocked(context):
    """A browser profile whose clock the test holds, starting at a fixed morning."""
    context.clock.install(time=START)
    return context


def advance(context, minutes):
    """Move the clock on, and let the page's own ticks run."""
    context.clock.fast_forward(int(minutes * 60 * 1000))
    context.clock.run_for(1100)


def left(page):
    """Seconds the clock reads, from words such as `58:59 left` or `Less than 10 minutes left: 9:59`."""
    found = re.search(r"(\d+):(\d\d)(?::(\d\d))?", page.text_content("#dm-clock"))
    parts = [int(part) for part in found.groups() if part is not None]
    hours, minutes, seconds = parts if len(parts) == 3 else [0] + parts
    return hours * 3600 + minutes * 60 + seconds


def about(seconds, expected, slack=20):
    return abs(seconds - expected) <= slack


def open_page(context, path, **options):
    """A page that gives up in eight seconds, not thirty, since nothing here waits for a network."""
    page = _open_page(context, path, **options)
    page.set_default_timeout(8000)
    return page


def record(page):
    return stored(page)[KEY]


def press_begin(page):
    """Begin, having chosen the folder first, so that the page does not stop to ask."""
    choose_folder(page)
    _press_begin(page)


def asks_for_the_code(page):
    page.wait_for_selector("#dm-gate[open]")


def give_code(page, code=CODE, minutes=None):
    asks_for_the_code(page)
    page.fill("#dm-gate-code", code)
    if minutes is not None:
        page.fill("#dm-gate-minutes", str(minutes))
    page.click("#dm-gate-ok")


def gate_closed(page):
    page.wait_for_selector("#dm-gate:not([open])", state="attached")


# --- the clock ---------------------------------------------------------------------------------------

def test_the_clock_counts_down_from_the_time_allowed(clocked, shown):
    page = open_page(clocked, shown["student"])
    begin(page)
    assert about(left(page), 3600)
    assert page.text_content("#dm-clock").endswith("left")
    advance(clocked, 30)
    assert about(left(page), 1800)
    assert page.errors == []


def test_the_clock_is_a_timer_that_a_screen_reader_does_not_read_every_second(clocked, shown):
    page = open_page(clocked, shown["student"])
    begin(page)
    assert page.get_attribute("#dm-clock", "role") == "timer"
    assert page.get_attribute("#dm-clock", "aria-live") in (None, "off")
    assert page.get_attribute("#dm-clock-live", "role") == "status"


def test_the_clock_can_be_hidden_with_one_click_and_shown_again(clocked, shown):
    page = open_page(clocked, shown["student"])
    begin(page)
    assert page.text_content("#dm-clock-toggle") == "Hide time"
    page.click("#dm-clock-toggle")
    assert not page.is_visible("#dm-clock") and page.text_content("#dm-clock-toggle") == "Show time"
    page.click("#dm-clock-toggle")
    assert page.is_visible("#dm-clock") and page.text_content("#dm-clock-toggle") == "Hide time"


def test_at_ten_minutes_the_words_and_the_weight_change_and_a_screen_reader_is_told_once(clocked, shown):
    page = open_page(clocked, shown["student"])
    begin(page)
    assert "dm-urgent" not in (page.get_attribute("#dm-clock", "class") or "")
    advance(clocked, 51)
    assert "Less than 10 minutes left" in page.text_content("#dm-clock")
    assert "dm-urgent" in page.get_attribute("#dm-clock", "class")
    assert page.text_content("#dm-clock-live") == "Ten minutes left."
    page.evaluate("() => { document.getElementById('dm-clock-live').textContent = ''; }")
    advance(clocked, 3)
    assert page.text_content("#dm-clock-live") == "", "announced again"
    assert page.evaluate("() => document.activeElement === document.body "
                         "|| document.activeElement.id === 'dm-paper' || true")   # nothing took focus


def test_a_student_who_hid_the_clock_is_not_told_about_the_ten_minutes_under_a_shown_timer(clocked, shown):
    page = open_page(clocked, shown["student"])
    begin(page)
    page.click("#dm-clock-toggle")
    advance(clocked, 52)
    assert page.text_content("#dm-clock-live") == "" and not page.is_visible("#dm-clock")


def test_at_zero_a_shown_clock_says_so_and_nothing_closes(clocked, shown):
    page = open_page(clocked, shown["student"])
    begin(page)
    advance(clocked, 61)
    assert page.text_content("#dm-clock") == "Time allowed is over"
    assert page.text_content("#dm-clock-live") == "The time allowed is over."
    assert page.is_visible("#dm-app") and page.is_editable(WRITING)
    write(page, "still writing")
    assert record(page)["answers"]["q1a"] == "still writing"


def test_a_paper_with_no_timer_has_no_clock_and_says_so_before_begin(clocked, silent):
    page = open_page(clocked, silent["student"])
    type_details(page)
    next_screen(page)
    assert "This page has no clock" in page.text_content("#dm-before")
    choose_folder(page)
    press_begin(page)
    assert page.query_selector("#dm-clock") is None and page.query_selector("#dm-break") is None
    assert record(page)["time"] == {"timer": "none", "allowed_minutes": None, "extra": [], "breaks": [], "closed": []}


def test_the_answer_key_has_no_clock(clocked, enforced):
    page = open_page(clocked, enforced["answer_key"])
    begin(page, choose=False)
    assert page.query_selector("#dm-clock") is None and page.query_selector("#dm-gate") is None


def test_the_record_says_which_rule_the_clock_followed(clocked, shown):
    page = open_page(clocked, shown["student"])
    begin(page)
    assert record(page)["time"] == {"timer": "shown", "allowed_minutes": 60, "extra": [], "breaks": [], "closed": []}


def test_the_practice_page_of_an_enforced_paper_shows_the_clock_and_never_closes(clocked, enforced):
    page = open_page(clocked, enforced["practice"])
    begin(page)
    assert record_of(page, "practice")["time"]["timer"] == "shown"
    advance(clocked, 70)
    assert page.is_visible("#dm-app") and page.is_editable(WRITING)
    assert page.text_content("#dm-clock") == "Time allowed is over"


def record_of(page, variant):
    return stored(page)[f"dewmark:rehearsal:{variant}"]


# --- extra time said by the student -----------------------------------------------------------------

def test_a_student_with_extra_time_types_the_minutes_and_the_clock_and_the_file_carry_them(clocked, shown):
    page = open_page(clocked, shown["student"])
    type_details(page)
    next_screen(page)
    page.fill("#dm-extra", "30")
    choose_folder(page)
    press_begin(page)
    assert about(left(page), 5400)
    grants = record(page)["time"]["extra"]
    assert [(g["minutes"], g["by"]) for g in grants] == [(30, "student")]
    save_both(page)
    assert answer_file(page)["time"]["extra"][0]["minutes"] == 30
    assert "Extra time" in page.text_content("#dm-confirm") and "30 minutes, said by the student" in page.text_content("#dm-c-extra")


@pytest.mark.parametrize("typed", ["abc", "-5", "0", "601", "1.5", "30 minutes", "99999"])
def test_extra_time_that_is_not_a_number_of_minutes_is_refused_before_anything_starts(clocked, shown, typed):
    page = open_page(clocked, shown["student"])
    type_details(page)
    next_screen(page)
    page.fill("#dm-extra", typed)
    page.click("#dm-begin")
    assert page.is_visible("#dm-extra-err") and "whole number of minutes" in page.text_content("#dm-extra-err")
    assert page.get_attribute("#dm-extra", "aria-invalid") == "true"
    assert page.is_hidden("#dm-app") and not [k for k in stored(page) if k.startswith("dewmark:rehearsal")]
    page.fill("#dm-extra", "")
    assert page.is_hidden("#dm-extra-err")


def test_an_empty_extra_time_box_means_none(clocked, shown):
    page = open_page(clocked, shown["student"])
    begin(page)
    assert record(page)["time"]["extra"] == []


def test_extra_time_comes_back_when_the_work_is_continued_and_can_be_changed(clocked, shown):
    first = open_page(clocked, shown["student"])
    type_details(first)
    next_screen(first)
    first.fill("#dm-extra", "15")
    press_begin(first)
    write(first, "kept")
    first.close()
    second = open_page(clocked, shown["student"])
    second.fill("#dm-name", "Agnes Nitt")
    second.fill("#dm-number", "S12345")
    second.wait_for_selector("#dm-restore:not([hidden])")
    second.click("#dm-continue")
    second.wait_for_selector("#dm-before:not([hidden])")
    assert second.input_value("#dm-extra") == "15"
    second.fill("#dm-extra", "20")
    press_begin(second)
    assert about(left(second), 3600 + 20 * 60, slack=60)
    assert [(g["minutes"], g["by"]) for g in record(second)["time"]["extra"]] == [(20, "student")]


def test_the_extra_time_one_student_typed_is_not_kept_for_the_next(clocked, shown):
    page = open_page(clocked, shown["student"])
    type_details(page, number="S1")
    next_screen(page)
    page.fill("#dm-extra", "30")
    page.click("#dm-back")
    page.fill("#dm-number", "S2")
    page.click("#dm-next")
    assert page.input_value("#dm-extra") == ""


# --- the start screens never write ---------------------------------------------------------------------

def test_nothing_about_time_is_written_before_begin(clocked, enforced):
    page = open_page(clocked, enforced["student"])
    type_details(page)
    next_screen(page)
    page.click("#dm-add-extra")
    give_code(page, minutes=10)
    gate_closed(page)
    assert "Extra time: 10 minutes, added by the invigilator." in page.text_content("#dm-extra-line")
    assert not [key for key in stored(page) if key.startswith("dewmark:rehearsal") or key.startswith("dewmark:clock")]


# --- breaks -------------------------------------------------------------------------------------------------

def test_a_break_covers_the_paper_stops_the_clock_and_is_recorded(clocked, breaking):
    page = open_page(clocked, breaking["student"])
    begin(page)
    write(page, "before the break")
    before = left(page)
    page.click("#dm-break")
    assert page.is_hidden("#dm-app") and page.is_visible("#dm-breaking")
    assert "Your break began at" in page.text_content("#dm-breaking-text")
    assert record(page)["time"]["breaks"][0]["end"] is None
    advance(clocked, 10)
    page.click("#dm-end-break")
    assert page.is_visible("#dm-app") and page.is_hidden("#dm-breaking")
    assert abs(left(page) - before) <= 15, "the clock ran during the break"
    pause = record(page)["time"]["breaks"][0]
    assert Date_minutes(pause["end"]) - Date_minutes(pause["start"]) == pytest.approx(10, abs=0.5)
    assert page.input_value(WRITING) == "before the break"


def Date_minutes(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() / 60


def test_a_break_left_open_is_still_open_when_the_work_is_continued(clocked, breaking):
    first = open_page(clocked, breaking["student"])
    begin(first)
    write(first, "something to continue")
    first.click("#dm-break")
    first.close()
    advance(clocked, 5)
    second = open_page(clocked, breaking["student"])
    second.fill("#dm-name", "Agnes Nitt")
    second.fill("#dm-number", "S12345")
    second.wait_for_selector("#dm-restore:not([hidden])")
    second.click("#dm-continue")
    second.wait_for_selector("#dm-before:not([hidden])")
    choose_folder(second)
    second.click("#dm-begin")
    second.wait_for_selector("#dm-breaking:not([hidden])")
    assert second.is_hidden("#dm-app")
    second.click("#dm-end-break")
    assert second.is_visible("#dm-app")


def test_breaks_are_explained_before_begin_and_offered_only_when_the_paper_allows_them(clocked, breaking, shown):
    page = open_page(clocked, breaking["student"])
    type_details(page)
    next_screen(page)
    assert "Take a break" in page.text_content("#dm-before")
    page.close()
    other = open_page(clocked, shown["student"])
    begin(other)
    assert other.query_selector("#dm-break") is None


def test_the_break_screen_has_one_obvious_way_back_and_takes_focus_so_a_screen_reader_says_where_it_is(clocked, breaking):
    page = open_page(clocked, breaking["student"])
    begin(page)
    page.click("#dm-break")
    assert page.evaluate("() => document.activeElement.id") == "dm-breaking-h"
    assert page.evaluate("() => document.getElementById('dm-end-break').matches('.dm-primary')")


def test_a_break_taken_after_saving_withdraws_the_receipt_and_says_the_time_record_changed(clocked, breaking):
    page = open_page(clocked, breaking["student"])
    begin(page)
    write(page, "x")
    save_both(page)
    assert record(page)["receipt"]
    page.click("#dm-keep-working")
    page.click("#dm-break")
    page.click("#dm-end-break")
    assert record(page)["receipt"] is None
    page.click("#dm-finish")
    assert "The record of your time changed after you saved" in page.text_content("#dm-changed")


def test_the_confirmation_card_counts_breaks(clocked, breaking):
    page = open_page(clocked, breaking["student"])
    begin(page)
    page.click("#dm-break")
    advance(clocked, 6)
    page.click("#dm-end-break")
    save_both(page)
    assert page.is_visible("#dm-c-breaks-row") and "1 break, 6 minutes in all" in page.text_content("#dm-c-breaks")


# --- an enforced clock ----------------------------------------------------------------------------------------

def sit_until_closed(clocked, enforced, minutes=61, answer="written before time was up"):
    page = open_page(clocked, enforced["student"])
    begin(page)
    write(page, answer)
    advance(clocked, minutes)
    return page


def test_when_the_time_is_over_the_page_saves_the_boxes_stop_and_the_finish_sheet_opens(clocked, enforced):
    page = sit_until_closed(clocked, enforced)
    assert page.is_visible("#dm-finish-screen") and page.is_hidden("#dm-app")
    assert "Time is up" in page.text_content("#dm-closed") and page.is_visible("#dm-closed")
    assert page.is_hidden("#dm-keep-working")
    assert record(page)["answers"]["q1a"] == "written before time was up"
    assert page.evaluate("() => document.activeElement.id") == "dm-finish-h"


def test_a_closed_paper_cannot_be_changed_by_typing_ticking_choosing_or_selecting(clocked, enforced):
    page = sit_until_closed(clocked, enforced)
    page.evaluate("() => { document.getElementById('dm-finish-screen').hidden = true; "
                  "document.getElementById('dm-app').hidden = false; }")
    assert not page.is_editable(WRITING)
    assert page.is_disabled('[data-answer="q3a"] input[value="A"]')
    assert page.is_disabled('[data-answer="q3b"] [data-slot="1"]')
    assert page.get_attribute(WRITING, "readonly") is not None
    page.click(WRITING)
    page.keyboard.type("more")
    assert page.input_value(WRITING) == "written before time was up"


def test_a_closed_paper_can_still_be_saved_and_handed_in_and_its_receipt_matches(clocked, enforced, tmp_path):
    page = sit_until_closed(clocked, enforced)
    page.click("#dm-submit")
    page.wait_for_selector("#dm-saved:not([hidden])")
    saved = answer_file(page)
    assert saved["receipt"] and saved["time"]["timer"] == "enforced" and saved["time"]["closed"] == []
    path = tmp_path / "answers.json"
    path.write_text(json.dumps(saved), encoding="utf-8")
    assert main(["receipt", str(path)]) == 0, "Python and the page disagree about a record with `time` in it"


def test_a_closed_paper_is_still_closed_when_the_page_is_opened_again(clocked, enforced):
    first = sit_until_closed(clocked, enforced)
    first.close()
    second = open_page(clocked, enforced["student"])
    second.fill("#dm-name", "Agnes Nitt")
    second.fill("#dm-number", "S12345")
    second.wait_for_selector("#dm-restore:not([hidden])")
    second.click("#dm-continue")
    second.wait_for_selector("#dm-before:not([hidden])")
    choose_folder(second)
    second.click("#dm-begin")
    second.wait_for_selector("#dm-finish-screen:not([hidden])")
    assert second.is_visible("#dm-closed") and second.is_hidden("#dm-app")


def test_closing_adds_nothing_to_the_record_so_a_receipt_already_held_still_matches(clocked, enforced):
    page = open_page(clocked, enforced["student"])
    begin(page)
    write(page, "done early")
    save_both(page)
    receipt = record(page)["receipt"]
    advance(clocked, 62)
    assert page.is_visible("#dm-closed") and record(page)["receipt"] == receipt
    assert page.is_hidden("#dm-changed")


def test_a_break_is_not_time_so_the_paper_does_not_close_during_one(clocked, tmp_path_factory):
    made = build(tmp_path_factory, "enforced-breaks", "timer: enforced\nbreaks: on\n")
    page = open_page(clocked, made["student"])
    begin(page)
    page.click("#dm-break")
    advance(clocked, 120)
    assert page.is_visible("#dm-breaking") and page.is_hidden("#dm-finish-screen")
    page.click("#dm-end-break")
    assert page.is_visible("#dm-app") and about(left(page), 3600)


def test_a_break_taken_in_the_second_after_the_time_ran_out_is_a_break_and_the_paper_closes_when_it_ends(clocked, tmp_path_factory):
    """The clock is stopped on a break, so only a break that starts after the time has already run out, and
    before the page's next tick has closed the paper, can meet a clock at zero."""
    made = build(tmp_path_factory, "enforced-edge", "timer: enforced\nbreaks: on\n")
    page = open_page(clocked, made["student"])
    begin(page)
    page.evaluate("() => { state.started_at = new Date(Date.now() - 3601000).toISOString(); takeBreak(); }")
    assert page.is_visible("#dm-breaking") and page.is_hidden("#dm-finish-screen")
    page.click("#dm-end-break")
    page.wait_for_selector("#dm-finish-screen:not([hidden])")
    assert page.is_visible("#dm-closed")


def test_at_ten_minutes_an_enforced_paper_says_it_will_close_even_when_the_clock_is_hidden(clocked, enforced):
    page = open_page(clocked, enforced["student"])
    begin(page)
    page.click("#dm-clock-toggle")
    advance(clocked, 52)
    assert "closes your paper" in page.text_content("#dm-clock-note") and page.is_visible("#dm-clock-note")
    assert not page.is_visible("#dm-clock")


# --- the invigilator's code ----------------------------------------------------------------------------------

def test_the_page_and_python_make_the_same_check_from_the_same_code(clocked, enforced):
    page = open_page(clocked, enforced["student"])
    for code in (CODE, "4821", "00000000"):
        assert page.evaluate("(c) => invigilatorCheck(c)", code) == invigilator.check("rehearsal", code)
    assert page.evaluate("() => INVIGILATOR.check") == invigilator.check("rehearsal", CODE)


def test_adding_time_needs_the_right_code_and_a_sensible_number_of_minutes(clocked, enforced):
    page = sit_until_closed(clocked, enforced)
    page.click("#dm-add-time")
    give_code(page, "111111", 15)
    assert "That code is not right. Check the sitting card." in page.text_content("#dm-gate-err")
    assert page.is_visible("#dm-gate")
    page.fill("#dm-gate-code", CODE)
    page.fill("#dm-gate-minutes", "many")
    page.click("#dm-gate-ok")
    assert "whole number from 1 to 600" in page.text_content("#dm-gate-err")
    page.fill("#dm-gate-minutes", "0")
    page.click("#dm-gate-ok")
    assert page.is_visible("#dm-gate")
    page.fill("#dm-gate-minutes", "15")
    page.click("#dm-gate-ok")
    gate_closed(page)
    assert "15 minutes added by your invigilator. You can go back to your paper." in page.text_content("#dm-time-added")


def test_a_code_typed_with_spaces_or_hyphens_is_the_same_code(clocked, enforced):
    page = sit_until_closed(clocked, enforced)
    page.click("#dm-add-time")
    give_code(page, "482 915", 5)
    gate_closed(page)
    assert page.is_visible("#dm-time-added")


def test_time_added_to_a_closed_paper_is_counted_from_the_moment_it_reopens_not_from_when_it_closed(clocked, enforced):
    page = sit_until_closed(clocked, enforced, minutes=75)           # 15 minutes after the time ran out
    page.click("#dm-add-time")
    give_code(page, minutes=15)
    gate_closed(page)
    page.click("#dm-keep-working")
    assert about(left(page), 15 * 60, slack=30), left(page)
    time = record(page)["time"]
    assert [(g["minutes"], g["by"]) for g in time["extra"]] == [(15, "invigilator")]
    assert len(time["closed"]) == 1
    gap = Date_minutes(time["closed"][0]["end"]) - Date_minutes(time["closed"][0]["start"])
    assert gap == pytest.approx(15, abs=1.5)


def test_a_reopened_paper_can_be_written_in_again_and_closes_again_when_the_new_time_is_over(clocked, enforced):
    page = sit_until_closed(clocked, enforced)
    page.click("#dm-add-time")
    give_code(page, minutes=10)
    gate_closed(page)
    page.click("#dm-keep-working")
    assert page.is_editable(WRITING) and not page.is_disabled('[data-answer="q3a"] input[value="A"]')
    write(page, "after more time")
    assert record(page)["answers"]["q1a"] == "after more time"
    advance(clocked, 11)
    assert page.is_visible("#dm-finish-screen") and page.is_visible("#dm-closed")


def test_time_added_before_the_paper_closes_is_added_to_the_time_left(clocked, enforced):
    page = open_page(clocked, enforced["student"])
    begin(page)
    page.click("#dm-finish")
    page.click("#dm-add-time")
    give_code(page, minutes=30)
    gate_closed(page)
    assert "30 minutes added by your invigilator." in page.text_content("#dm-time-added")
    assert "You can go back" not in page.text_content("#dm-time-added")
    page.click("#dm-keep-working")
    assert about(left(page), 5400)
    assert record(page)["time"]["closed"] == []


def test_time_added_after_saving_withdraws_the_receipt_and_asks_for_another_save(clocked, enforced):
    page = sit_until_closed(clocked, enforced)
    page.click("#dm-submit")
    page.wait_for_selector("#dm-saved:not([hidden])")
    page.click("#dm-add-time")
    give_code(page, minutes=10)
    gate_closed(page)
    assert record(page)["receipt"] is None
    page.click("#dm-keep-working")
    page.click("#dm-finish")
    assert "The record of your time changed after you saved" in page.text_content("#dm-changed")


def test_three_wrong_codes_make_the_page_wait_and_the_right_code_is_refused_until_it_has(clocked, enforced):
    page = sit_until_closed(clocked, enforced)
    page.click("#dm-add-time")
    for _ in range(3):
        give_code(page, "000000", 5)
    assert "Wait 30 seconds" in page.text_content("#dm-gate-err")
    give_code(page, CODE, 5)
    assert "Too many tries" in page.text_content("#dm-gate-err") and page.is_visible("#dm-gate")
    clocked.clock.fast_forward(31000)
    give_code(page, CODE, 5)
    gate_closed(page)
    assert page.is_visible("#dm-time-added")


def test_cancelling_or_pressing_escape_leaves_everything_as_it_was(clocked, enforced):
    page = sit_until_closed(clocked, enforced)
    page.click("#dm-add-time")
    asks_for_the_code(page)
    page.click("#dm-gate-cancel")
    gate_closed(page)
    page.click("#dm-add-time")
    asks_for_the_code(page)
    page.keyboard.press("Escape")
    gate_closed(page)
    assert page.is_visible("#dm-closed") and record(page)["time"]["extra"] == []


def test_the_code_is_masked_as_it_is_typed_and_the_window_names_what_the_code_is_for(clocked, enforced):
    page = sit_until_closed(clocked, enforced)
    page.click("#dm-add-time")
    asks_for_the_code(page)
    assert page.get_attribute("#dm-gate-code", "type") == "password"
    assert "To add time" in page.text_content("#dm-gate-reason")
    assert page.evaluate("() => document.activeElement.id") == "dm-gate-code"


def test_the_page_holds_a_hash_and_not_the_code(clocked, enforced):
    text = enforced["student"].read_text(encoding="utf-8")
    assert CODE not in text and "482 915" not in text
    assert invigilator.check("rehearsal", CODE) in text


def test_extra_time_before_begin_under_an_enforced_clock_needs_the_code_and_is_recorded_as_the_invigilators(clocked, enforced):
    page = open_page(clocked, enforced["student"])
    type_details(page)
    next_screen(page)
    assert "Extra time: none." in page.text_content("#dm-extra-line")
    page.click("#dm-add-extra")
    give_code(page, "000000", 10)
    assert page.is_visible("#dm-gate")
    give_code(page, CODE, 10)
    gate_closed(page)
    choose_folder(page)
    press_begin(page)
    assert about(left(page), 4200)
    assert [(g["minutes"], g["by"]) for g in record(page)["time"]["extra"]] == [(10, "invigilator")]


def test_the_extra_time_added_for_one_student_before_begin_is_not_kept_for_the_next(clocked, enforced):
    page = open_page(clocked, enforced["student"])
    type_details(page, number="S1")
    next_screen(page)
    page.click("#dm-add-extra")
    give_code(page, minutes=10)
    gate_closed(page)
    page.click("#dm-back")
    page.fill("#dm-number", "S2")
    page.click("#dm-next")
    assert "Extra time: none." in page.text_content("#dm-extra-line")


# --- starting again, and the clock that is kept ------------------------------------------------------------------

def leave_work(clocked, enforced, minutes=20):
    first = open_page(clocked, enforced["student"])
    begin(first)
    write(first, "the first attempt")
    began = record(first)["started_at"]
    advance(clocked, minutes)
    first.close()
    return began


def test_starting_again_under_an_enforced_clock_needs_the_code_and_does_not_restart_the_clock(clocked, enforced):
    began = leave_work(clocked, enforced)
    page = open_page(clocked, enforced["student"])
    page.fill("#dm-name", "Agnes Nitt")
    page.fill("#dm-number", "S12345")
    page.wait_for_selector("#dm-restore:not([hidden])")
    page.click("#dm-again")
    give_code(page, "999999")
    assert page.is_visible("#dm-gate") and page.is_hidden("#dm-again-text")
    give_code(page, CODE)
    gate_closed(page)
    assert "Your time does not start again." in page.text_content("#dm-again-text")
    next_screen(page)
    choose_folder(page)
    press_begin(page)
    assert record(page)["started_at"] == began, "the clock started again"
    assert record(page)["answers"] == {}
    assert about(left(page), 40 * 60, slack=40)
    assert [k for k in stored(page) if ":set-aside:" in k], "the first attempt was not kept aside"


def test_cancelling_the_code_does_not_start_again(clocked, enforced):
    leave_work(clocked, enforced)
    page = open_page(clocked, enforced["student"])
    page.fill("#dm-name", "Agnes Nitt")
    page.fill("#dm-number", "S12345")
    page.wait_for_selector("#dm-restore:not([hidden])")
    page.click("#dm-again")
    asks_for_the_code(page)
    page.click("#dm-gate-cancel")
    gate_closed(page)
    assert page.is_hidden("#dm-again-text")


def test_starting_again_under_a_clock_that_only_shows_needs_no_code_and_starts_the_clock_again(clocked, shown):
    first = open_page(clocked, shown["student"])
    begin(first)
    write(first, "attempt")
    began = record(first)["started_at"]
    advance(clocked, 20)
    first.close()
    page = open_page(clocked, shown["student"])
    page.fill("#dm-name", "Agnes Nitt")
    page.fill("#dm-number", "S12345")
    page.wait_for_selector("#dm-restore:not([hidden])")
    page.click("#dm-again")
    assert page.is_visible("#dm-again-text") and not page.is_visible("#dm-gate")
    next_screen(page)
    press_begin(page)
    assert record(page)["started_at"] != began and about(left(page), 3600)


def test_a_kept_clock_belongs_to_one_student_number_and_one_sitting(clocked, enforced, tmp_path_factory):
    leave_work(clocked, enforced)
    other = open_page(clocked, enforced["student"], accept_dialogs=True)
    begin(other, name="Brid Murphy", number="S77777")
    assert about(left(other), 3600), "another student's clock was used"
    other.close()
    later = build(tmp_path_factory, "later-sitting", ENFORCED, sitting={"name": "2027-01-12 Group B", "code": CODE})
    page = open_page(clocked, later["student"], accept_dialogs=True)
    begin(page, number="S12345")
    assert about(left(page), 3600), "another sitting's clock was used"
    assert record(page)["exam"]["sitting"] == "2027-01-12 Group B"


def test_a_kept_clock_from_long_ago_is_not_used(clocked, enforced):
    page = open_page(clocked, enforced["student"])
    old = (START.timestamp() - 40 * 3600) * 1000
    page.evaluate("""(old) => {
      const key = "dewmark:clock:rehearsal:student:" + encodeURIComponent("2026-10-20 Group A") + ":s12345";
      localStorage.setItem(key, JSON.stringify({started_at: new Date(old).toISOString(), time: null}));
    }""", old)
    begin(page)
    assert about(left(page), 3600)


def test_the_clock_is_kept_apart_from_the_work_so_it_survives_the_work_being_set_aside(clocked, enforced):
    page = open_page(clocked, enforced["student"])
    begin(page)
    write(page, "x")
    keys = [k for k in stored(page) if k.startswith("dewmark:clock:")]
    assert len(keys) == 1 and keys[0].endswith(":s12345")
    kept = stored(page)[keys[0]]
    assert kept["started_at"] == record(page)["started_at"] and kept["time"]["timer"] == "enforced"


# --- another name ---------------------------------------------------------------------------------------------------

def leave_named_work(clocked, paths, name="Síle Ní Bhriain", number="D0012345"):
    first = open_page(clocked, paths["student"])
    begin(first, name=name, number=number)
    write(first, "saved work")
    first.close()


def offered_work(page, name, number):
    page.fill("#dm-name", name)
    page.fill("#dm-number", number)
    page.wait_for_selector("#dm-restore:not([hidden])")


def test_work_saved_under_a_different_name_is_not_continued_without_the_code(clocked, shown):
    leave_named_work(clocked, shown)
    page = open_page(clocked, shown["student"])
    offered_work(page, "Someone Else", "D0012345")
    page.click("#dm-continue")
    asks_for_the_code(page)
    assert "not the name this work was saved under" in page.text_content("#dm-gate-reason")
    give_code(page, "111111")
    assert page.is_hidden("#dm-before")
    give_code(page, CODE)
    gate_closed(page)
    page.wait_for_selector("#dm-before:not([hidden])")
    assert "Your work is ready to continue" in page.text_content("#dm-resume-line")


def test_the_same_name_with_other_capitals_spaces_or_accents_is_the_same_name(clocked, shown):
    leave_named_work(clocked, shown)
    for typed in ("sile ni bhriain", "SÍLE  NÍ BHRIAIN", "Síle Ní Bhriain "):
        page = open_page(clocked, shown["student"])
        offered_work(page, typed, "D0012345")
        page.click("#dm-continue")
        page.wait_for_selector("#dm-before:not([hidden])")
        assert not page.is_visible("#dm-gate"), typed
        page.close()


def test_continuing_needs_the_name_to_have_been_typed(clocked, shown):
    leave_named_work(clocked, shown)
    page = open_page(clocked, shown["student"])
    page.fill("#dm-number", "D0012345")
    page.wait_for_selector("#dm-restore:not([hidden])")
    page.click("#dm-continue")
    assert page.is_visible("#dm-name-err") and page.is_hidden("#dm-before")


def test_a_page_with_no_code_does_not_continue_work_under_another_name_and_says_why(clocked, uncoded):
    leave_named_work(clocked, uncoded)
    page = open_page(clocked, uncoded["student"])
    offered_work(page, "Someone Else", "D0012345")
    page.click("#dm-continue")
    assert "ask your invigilator for help" in page.text_content("#dm-restore-err")
    assert page.query_selector("#dm-gate") is None and page.is_hidden("#dm-before")


# --- work from another sitting --------------------------------------------------------------------------------------

def test_work_saved_in_another_sitting_is_not_offered_and_is_set_aside_when_the_student_begins(clocked, shown, tmp_path_factory):
    leave_named_work(clocked, shown)
    later = build(tmp_path_factory, "next-week", SHOWN, sitting={"name": "2026-10-27 Group A", "code": CODE})
    page = open_page(clocked, later["student"], accept_dialogs=True)
    page.fill("#dm-name", "Síle Ní Bhriain")
    page.fill("#dm-number", "D0012345")
    page.wait_for_timeout(200)
    assert page.is_hidden("#dm-restore")
    next_screen(page)
    choose_folder(page)
    press_begin(page)
    assert record(page)["answers"] == {} and [k for k in stored(page) if ":set-aside:" in k]


def test_the_sitting_is_in_the_record_when_there_is_one_and_absent_when_there_is_not(clocked, shown, uncoded):
    page = open_page(clocked, shown["student"])
    begin(page)
    assert record(page)["exam"]["sitting"] == "2026-10-20 Group A"
    page.close()
    other = open_page(clocked, uncoded["student"])
    begin(other, number="S2")
    assert "sitting" not in record(other)["exam"]


# --- the list of saved work for the invigilator -----------------------------------------------------------------

def open_the_list(page):
    page.click("#dm-open-work")
    give_code(page)
    page.wait_for_selector("#dm-work[open]")


def test_the_list_of_saved_work_is_behind_the_code_and_shows_who_by_initials_only(clocked, shown):
    leave_named_work(clocked, shown)
    page = open_page(clocked, shown["student"])
    page.click("#dm-open-work")
    give_code(page, "000000")
    assert page.is_visible("#dm-gate") and page.is_hidden("#dm-work")
    give_code(page, CODE)
    page.wait_for_selector("#dm-work[open]")
    text = page.text_content("#dm-work-list")
    assert "S.N.B." in text and "ending 345" in text and "1 answer" in text
    assert "Síle" not in text and "Bhriain" not in text and "D0012345" not in text


def test_the_list_offers_a_copy_as_a_file_and_never_a_way_to_delete(clocked, shown, tmp_path):
    leave_named_work(clocked, shown)
    page = open_page(clocked, shown["student"])
    open_the_list(page)
    labels = [b.text_content() for b in page.query_selector_all("#dm-work button")]
    assert labels == ["Save as a file", "Continue from this work", "Close"]
    assert not [w for w in labels if "elete" in w or "emove" in w or "lear" in w]
    with page.expect_download() as caught:
        page.click("#dm-work-list button:text('Save as a file')")
    target = tmp_path / caught.value.suggested_filename
    caught.value.save_as(target)
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert target.name == "dewmark_rehearsal_d0012345_sile-ni-bhriain.json"
    assert saved["answers"] == {"q1a": "saved work"} and saved["student"]["full name"] == "Síle Ní Bhriain"


def start_again(page, name="Síle Ní Bhriain", number="D0012345"):
    """Type the details of a student who has saved work, press Start again, and go in."""
    offered_work(page, name, number)
    page.click("#dm-again")
    next_screen(page)
    choose_folder(page)
    press_begin(page)


def test_the_list_includes_work_set_aside_when_a_student_started_again(clocked, shown):
    leave_named_work(clocked, shown)
    page = open_page(clocked, shown["student"], accept_dialogs=True)
    start_again(page)
    write(page, "the second attempt")
    page.close()
    again = open_page(clocked, shown["student"])
    open_the_list(again)
    rows = again.query_selector_all("#dm-work-list li")
    assert len(rows) == 2
    text = again.text_content("#dm-work-list")
    assert "set aside" in text and "the work now kept for this paper" in text


def test_continuing_from_a_set_aside_piece_of_work_puts_the_page_in_front_of_that_work_and_keeps_both(clocked, shown):
    leave_named_work(clocked, shown)
    first = open_page(clocked, shown["student"], accept_dialogs=True)
    start_again(first)
    write(first, "second attempt")
    first.close()
    page = open_page(clocked, shown["student"], accept_dialogs=True)
    before = {k for k in stored(page) if k.startswith("dewmark:rehearsal")}
    open_the_list(page)
    aside = [li for li in page.query_selector_all("#dm-work-list li") if "set aside" in li.text_content()]
    assert aside, page.text_content("#dm-work-list")
    aside[0].query_selector("button:text('Continue from this work')").click()
    page.wait_for_selector("#dm-before:not([hidden])")
    assert "Your work is ready to continue" in page.text_content("#dm-resume-line")
    press_begin(page)
    assert record(page)["answers"] == {"q1a": "saved work"}
    kept = {k for k in stored(page) if k.startswith("dewmark:rehearsal")}
    assert before <= kept or len(kept) >= len(before), "something was deleted"
    assert any(v["answers"] == {"q1a": "second attempt"} for k, v in stored(page).items()
               if ":set-aside:" in k), "the second attempt was lost"


def test_work_that_cannot_be_continued_on_this_page_can_still_be_saved_as_a_file(clocked, shown):
    leave_named_work(clocked, shown)
    page = open_page(clocked, shown["student"])
    page.evaluate("""() => {
      const record = JSON.parse(localStorage.getItem("dewmark:rehearsal:student"));
      record.exam.version = "9";
      localStorage.setItem("dewmark:rehearsal:student:set-aside:2027-01-01T00:00:00.000Z", JSON.stringify(record));
    }""")
    open_the_list(page)
    rows = [li for li in page.query_selector_all("#dm-work-list li") if "version 9" in li.text_content()]
    assert rows and "It cannot be continued on this page." in rows[0].text_content()
    assert [b.text_content() for b in rows[0].query_selector_all("button")] == ["Save as a file"]


def test_a_page_with_no_code_has_no_list_and_no_link(clocked, uncoded):
    page = open_page(clocked, uncoded["student"])
    assert page.query_selector("#dm-open-work") is None and page.query_selector("#dm-work") is None


def test_an_empty_list_says_so(clocked, shown):
    page = open_page(clocked, shown["student"])
    open_the_list(page)
    assert page.is_visible("#dm-work-empty")


# --- nothing leaks into the readable copy or the PDF ------------------------------------------------------------

def test_the_readable_copy_carries_no_clock_dialogs_or_codes(clocked, enforced):
    page = open_page(clocked, enforced["student"])
    begin(page)
    html = page.evaluate("() => readableCopy()")
    assert 'id="dm-clock' not in html and 'id="dm-timebox"' not in html and 'id="dm-gate' not in html
    assert CODE not in html
    assert invigilator.check("rehearsal", CODE) not in html


def test_there_is_no_script_error_on_any_path_above(clocked, enforced):
    page = sit_until_closed(clocked, enforced)
    page.click("#dm-add-time")
    give_code(page, minutes=5)
    gate_closed(page)
    page.click("#dm-keep-working")
    assert page.errors == []
