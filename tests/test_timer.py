"""The builder's half of the timer slice: how the time allowed is read, what the
timer setting means on each page, the invigilator's code that the build issues,
and the words the screens use. What the page does with the clock, breaks and the
code is rehearsed in a browser (tests/browser/test_time.py).
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

from dewmark import invigilator  # noqa: E402
from dewmark.__main__ import main  # noqa: E402
from dewmark.build import BuildError, build_pages, page_model, timer_block  # noqa: E402
from dewmark.reader import read  # noqa: E402
from dewmark.settings import parse_minutes  # noqa: E402

HEADER = """\
---
dewmark: 1
code: time-test
kind: exam
title: Time Test
module: Testing
module code: 5N0000
total marks: 4
time allowed: {allowed}
{extra}---
"""
BODY = "## Question 1: Q (4 marks)\n\n```answer\n```\n\n# Marking scheme\n### 1 (draft)\n"
SITTING = {"name": "2026-10-20 Group A", "code": "482915"}


def paper(extra="", allowed="1 hour"):
    return HEADER.format(extra=extra, allowed=allowed) + BODY


def pages(extra="", sitting=None, allowed="1 hour"):
    return build_pages(paper(extra, allowed), ROOT, sitting)


def student(extra="", sitting=None):
    return pages(extra, sitting)["time-test.student.html"]


def model_of(page):
    import json
    return json.loads(re.search(r'id="dewmark-page-model">(.*?)</script>', page, re.S).group(1))


# --- reading the time allowed ---------------------------------------------------------------------

@pytest.mark.parametrize("text, minutes", [
    ("90", 90), ("90 minutes", 90), ("45m", 45), ("1 hour", 60), ("2 HOURS", 120),
    ("1.5 hours", 90), ("1.25 hours", 75), ("2h30", 150), ("2h 30", 150), ("2 hours 30", 150),
    ("2 hours 30 minutes", 150), ("1 hour and 30 minutes", 90), ("1 hr, 15 mins", 75),
])
def test_a_time_is_read_into_whole_minutes(text, minutes):
    assert parse_minutes(text) == minutes


@pytest.mark.parametrize("text", [
    "", "open book", "two hours", "0", "0 minutes", "25 hours", "3 days", "1 hour 1 hour",
    "2 30", "30 minutes 15", "-5", "1e3",
])
def test_words_that_are_not_a_time_are_not_read(text):
    assert parse_minutes(text) is None


def messages_for(extra="", allowed="1 hour"):
    return read(paper(extra, allowed))["messages"]


def test_the_timer_defaults_to_shown_when_the_time_can_be_counted():
    assert read(paper())["settings"]["timer"] == "shown"
    assert read(paper(allowed="2 hours 30 minutes"))["settings"]["timer"] == "shown"


def test_a_time_that_cannot_be_counted_leaves_the_timer_off_with_a_warning():
    found = read(paper(allowed="Open book"))
    assert found["settings"]["timer"] == "none"
    assert [m.code for m in found["messages"].warnings] == ["timer-needs-a-time"]
    assert "2 hours 30 minutes" in str(found["messages"].warnings[0])


def test_a_timer_that_is_asked_for_needs_a_time_that_can_be_counted():
    for mode in ("shown", "enforced"):
        found = read(paper(f"timer: {mode}\n", allowed="Open book"))
        assert [m.code for m in found["messages"].problems] == ["timer-needs-a-time"]
    assert not read(paper("timer: none\n", allowed="Open book"))["messages"].problems


# --- what the timer means on each page ------------------------------------------------------------

@pytest.mark.parametrize("timer, variant, mode", [
    ("none", "student", "none"), ("shown", "student", "shown"), ("enforced", "student", "enforced"),
    ("enforced", "practice", "shown"), ("shown", "practice", "shown"), ("none", "practice", "none"),
    ("shown", "answer-key", "none"), ("enforced", "answer-key", "none"),
])
def test_the_answer_key_has_no_clock_and_a_practice_page_never_closes_the_paper(timer, variant, mode):
    block = timer_block(read(paper(f"timer: {timer}\n"))["settings"], variant)
    assert block["mode"] == mode
    assert block["minutes"] == (60 if mode != "none" else None)


def test_breaks_are_off_unless_the_paper_asks_and_never_on_the_answer_key():
    settings = read(paper("breaks: on\n"))["settings"]
    assert [timer_block(settings, v)["breaks"] for v in ("student", "practice", "answer-key")] == [True, True, False]
    assert not timer_block(read(paper())["settings"], "student")["breaks"]


def test_the_model_carries_the_timer_and_a_hash_of_the_code_and_never_the_code():
    made = pages("timer: enforced\n", SITTING)
    for variant in ("student", "practice"):
        model = model_of(made[f"time-test.{variant}.html"])
        assert model["timer"] == {"mode": "enforced" if variant == "student" else "shown",
                                  "minutes": 60, "breaks": False}
        assert model["invigilator"] == {"check": invigilator.check("time-test", "482915"),
                                        "sitting": "2026-10-20 Group A"}
    assert model_of(made["time-test.answer-key.html"])["invigilator"] is None
    for text in made.values():
        assert "482915" not in text and "482 915" not in text


def test_a_page_built_without_a_sitting_has_no_code_and_no_window_to_ask_for_one():
    page = student()
    assert model_of(page)["invigilator"] is None
    assert 'id="dm-gate"' not in page and 'id="dm-open-work"' not in page and 'id="dm-work"' not in page


def test_a_page_built_with_a_sitting_has_the_windows_and_the_link_for_invigilators():
    page = student(sitting=SITTING)
    assert 'id="dm-gate"' in page and 'id="dm-work"' in page and 'id="dm-open-work"' in page
    assert "Saved work on this computer (for invigilators)" in page


def test_an_enforced_paper_cannot_be_built_without_a_sitting():
    with pytest.raises(BuildError) as caught:
        pages("timer: enforced\n")
    text = " ".join(caught.value.messages)
    assert "invigilator's code" in text and "--sitting" in text and "--code" in text
    assert pages("timer: enforced\n", SITTING)


def test_the_mutation_test_still_holds_with_a_code_in_the_page():
    """The code is an input of the build, not a random choice made in it."""
    assert pages("timer: enforced\n", SITTING) == pages("timer: enforced\n", SITTING)


# --- the words on the screens ------------------------------------------------------------------------

def before_of(page):
    return re.search(r'<section id="dm-before".*?</section>', page, re.S).group(0)


def test_a_shown_clock_asks_for_extra_time_and_says_the_page_will_not_stop_the_student():
    before = before_of(student("timer: shown\n"))
    assert 'id="dm-extra"' in before and 'id="dm-add-extra"' not in before
    assert "When the time is over, the page does not stop you. Your invigilator will tell you." in before
    assert "You can hide it with one click" in before and "Your invigilator will check it." in before


def test_an_enforced_clock_says_the_paper_will_close_and_gives_extra_time_to_the_invigilator():
    before = before_of(student("timer: enforced\n", SITTING))
    assert 'id="dm-extra"' not in before and 'id="dm-add-extra"' in before and 'id="dm-extra-line"' in before
    assert "the page saves your work and closes your paper" in before
    assert "Your invigilator can give you more time." in before


def test_a_paper_with_no_timer_says_there_is_no_clock():
    before = before_of(student("timer: none\n"))
    assert "This page has no clock. Your invigilator keeps the time." in before
    assert 'id="dm-extra"' not in before and 'id="dm-clock"' not in student("timer: none\n")


def test_the_practice_page_does_not_send_a_student_to_an_invigilator():
    before = before_of(pages("timer: enforced\n", SITTING)["time-test.practice.html"])
    assert 'id="dm-extra"' in before and 'id="dm-add-extra"' not in before
    assert "Your invigilator will check it" not in before and "Your invigilator will tell you" not in before


def test_breaks_are_explained_only_when_they_are_on():
    assert "Take a break" in before_of(student("breaks: on\n"))
    assert "Take a break" not in before_of(student())
    assert 'id="dm-breaking"' in student("breaks: on\n") and 'id="dm-breaking"' not in student()
    assert 'id="dm-break"' in student("breaks: on\n") and 'id="dm-break"' not in student()


def test_the_top_bar_has_a_clock_and_a_button_to_hide_it_unless_the_paper_has_no_timer():
    page = student("timer: shown\n")
    assert 'id="dm-clock"' in page and 'role="timer"' in page and 'id="dm-clock-toggle"' in page
    assert 'id="dm-clock-live"' in page and 'role="status"' in page
    assert 'id="dm-clock"' not in student("timer: none\n")


def test_the_answer_key_has_no_clock_and_no_break_button_whatever_the_paper_says():
    key = pages("timer: enforced\nbreaks: on\n", SITTING)["time-test.answer-key.html"]
    assert 'id="dm-clock"' not in key and 'id="dm-break"' not in key and 'id="dm-gate"' not in key
    assert "This page has no clock" not in before_of(key)


def test_only_an_enforced_student_page_has_the_invigilators_add_time_button_on_the_finish_sheet():
    assert 'id="dm-add-time"' in student("timer: enforced\n", SITTING)
    assert 'id="dm-add-time"' not in student("timer: shown\n", SITTING)
    assert 'id="dm-add-time"' not in pages("timer: enforced\n", SITTING)["time-test.practice.html"]


def test_the_confirmation_card_has_rows_for_extra_time_and_breaks_that_start_hidden():
    page = student("timer: shown\n")
    assert re.search(r'id="dm-c-extra-row" hidden', page) and re.search(r'id="dm-c-breaks-row" hidden', page)


# --- the invigilator's code ---------------------------------------------------------------------------

def test_a_code_is_digits_made_from_the_systems_source_and_written_in_threes():
    codes = {invigilator.issue() for _ in range(50)}
    assert all(re.fullmatch(r"\d{6}", code) for code in codes) and len(codes) > 40
    assert invigilator.pretty("482915") == "482 915" and invigilator.pretty("4821") == "482 1"


def test_spaces_and_hyphens_in_a_typed_code_do_not_count():
    assert invigilator.normalise("482 915") == invigilator.normalise("482-915") == "482915"
    assert invigilator.check("x", "482 915") == invigilator.check("x", "482915")


@pytest.mark.parametrize("given, ok", [("482915", True), ("4821", True), ("12345678", True), ("482 915", True),
                                       ("123", False), ("123456789", False), ("", False), ("48x915", False)])
def test_a_code_the_teacher_gives_is_four_to_eight_digits(given, ok):
    assert invigilator.valid(given) is ok


def test_the_check_is_frozen_and_depends_on_the_paper_and_the_code():
    """A change here changes every page already built: it is a decision, not a repair."""
    assert invigilator.check("rehearsal", "482915") == "207e8ff89b625ba7"
    assert invigilator.check("rehearsal", "482916") != invigilator.check("rehearsal", "482915")
    assert invigilator.check("another", "482915") != invigilator.check("rehearsal", "482915")
    assert len(invigilator.check("x", "1234")) == 16


# --- the command ----------------------------------------------------------------------------------------

@pytest.fixture
def exam(tmp_path):
    path = tmp_path / "time-test.exam.md"
    path.write_text(paper("timer: enforced\n"), encoding="utf-8")
    return path


def test_build_with_a_sitting_issues_a_code_and_prints_it_once(exam, tmp_path, capsys):
    out = tmp_path / "out"
    assert main(["build", str(exam), "-o", str(out), "--sitting", "2026-10-20 Group A"]) == 0
    printed = capsys.readouterr().out
    shown = re.search(r'for "2026-10-20 Group A" is (\d{3} \d{3})\.', printed)
    assert shown, printed
    digits = shown.group(1).replace(" ", "")
    assert f"--code {digits}" in printed
    for file in out.iterdir():
        assert digits not in file.read_text(encoding="utf-8") and shown.group(1) not in file.read_text(encoding="utf-8")
    page = (out / "time-test.student.html").read_text(encoding="utf-8")
    assert model_of(page)["invigilator"]["check"] == invigilator.check("time-test", digits)


def test_build_with_a_code_of_the_teachers_own_builds_pages_that_accept_it(exam, tmp_path, capsys):
    assert main(["build", str(exam), "-o", str(tmp_path / "out"), "--sitting", "Group A", "--code", "482 915"]) == 0
    page = (tmp_path / "out" / "time-test.student.html").read_text(encoding="utf-8")
    assert model_of(page)["invigilator"] == {"check": invigilator.check("time-test", "482915"), "sitting": "Group A"}
    assert "is 482 915." in capsys.readouterr().out


def test_two_builds_for_two_sittings_have_two_codes(exam, tmp_path, capsys):
    checks = []
    for number in range(2):
        out = tmp_path / f"out{number}"
        main(["build", str(exam), "-o", str(out), "--sitting", f"Group {number}"])
        checks.append(model_of((out / "time-test.student.html").read_text(encoding="utf-8"))["invigilator"]["check"])
    assert checks[0] != checks[1]


def test_build_refuses_a_code_that_is_not_digits(exam, tmp_path, capsys):
    assert main(["build", str(exam), "-o", str(tmp_path / "out"), "--code", "12"]) == 2
    assert "4 to 8 digits" in capsys.readouterr().out
    assert not (tmp_path / "out").exists()


def test_build_without_a_sitting_refuses_an_enforced_paper_and_says_what_to_add(exam, tmp_path, capsys):
    assert main(["build", str(exam), "-o", str(tmp_path / "out")]) == 1
    printed = capsys.readouterr().out
    assert "not built" in printed and "--sitting" in printed
    assert not (tmp_path / "out").exists()


def test_build_without_an_output_folder_checks_and_prints_no_code(exam, capsys):
    assert main(["build", str(exam), "--sitting", "Group A"]) == 0
    printed = capsys.readouterr().out
    assert "no files written" in printed and "invigilator's code" not in printed


def test_a_paper_that_does_not_need_a_code_says_its_pages_have_none(tmp_path, capsys):
    path = tmp_path / "time-test.exam.md"
    path.write_text(paper("timer: shown\n"), encoding="utf-8")
    assert main(["build", str(path), "-o", str(tmp_path / "out")]) == 0
    assert "no invigilator's code" in capsys.readouterr().out


def test_a_flag_with_no_value_is_not_taken_for_an_exam_file(exam, capsys):
    assert main(["build", str(exam), "--sitting"]) == 2
    assert "needs" in capsys.readouterr().out
