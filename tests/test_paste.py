"""Tests for the paste route (dewmark/package.py, dewmark/reply.py,
docs/EXAM_FORMAT.md §4.10).

The package is what a teacher gives an assistant; the reply check is what
stands between an assistant's reply and the teacher's paper. The tests
that matter most make a reply that goes wrong in one way, a setting, a
number, a line of code, a scheme slipped in, and check that it is refused;
and make a fake assistant reword every prose line of the four real PDP
papers, to check that the check can read real papers.
"""

import re
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dewmark.__main__ import main  # noqa: E402
from dewmark.package import (MODES, NOTES_BEGIN, NOTES_END, PAPER_BEGIN,  # noqa: E402
                             PAPER_END, build_package, follow_up,
                             scan_for_student_data, split_halves)
from dewmark import reply as reply_module  # noqa: E402
from dewmark.reader import read  # noqa: E402
from dewmark.reply import check_reply, extract_reply  # noqa: E402

DATA = ROOT / "dewmark" / "data"
SPECIMEN = (DATA / "specimen.exam.md").read_text(encoding="utf-8")
PDP = sorted((ROOT / "samples" / "pdp-5n2927").glob("*.exam.md"))

ABOUT = {"code": "word-paper", "kind": "practice", "title": "Word Paper",
         "module": "Introduction to Computing", "module code": "5N0000",
         "total marks": "10", "time allowed": "1 hour"}

WORD_PAPER = """\
Instructions
Answer both questions.

1. Variables (6 marks)
(a) State what this code prints: print(4 * 2.5) [2]
(b) Explain why the name 2nd_place is not allowed in Python. [4]

2. Lists (4 marks)
Write a list of three colours.
"""


def wrap(paper, notes=""):
    reply = f"{PAPER_BEGIN}\n{paper}\n{PAPER_END}\n"
    if notes:
        reply += f"{NOTES_BEGIN}\n{notes}\n{NOTES_END}\n"
    return reply


def codes(result, level="problem"):
    return [m.code for m in result["messages"] if m.level == level]


def reword(text, old, new):
    assert old in text, old
    return text.replace(old, new, 1)


# --- the package --------------------------------------------------------------

def test_the_five_modes_are_decision_19s():
    assert list(MODES) == ["copy", "tidy", "plain", "udl", "invite"]
    assert len({m.task for m in MODES.values()}) == 5
    assert [k for k, m in MODES.items() if not m.words] == ["copy"]


def test_a_package_holds_the_notice_the_rules_the_format_and_the_paper():
    made = build_package("tidy", SPECIMEN, made_on="2026-09-29")
    text = made["text"]
    assert text.startswith("THIS CONTAINS YOUR EXAM PAPER. IT CONTAINS NO STUDENT INFORMATION.")
    assert "Paste it only into an assistant your college allows for exam material." in text
    assert "THE RULES FOR YOUR REPLY" in text and "THE DEWMARK EXAM FILE ON ONE PAGE" in text
    assert text.count(PAPER_BEGIN) >= 1 and text.rstrip().endswith(PAPER_END)
    assert made["findings"] == [] and made["problems"] == []


def test_the_marking_scheme_and_the_reference_cards_never_go_in_the_package():
    text = SPECIMEN.replace("# Marking scheme", "# Reference\n\n## Card\n\nCARD-TEXT\n\n"
                            "# Marking scheme")
    made = build_package("tidy", text)
    for secret in ("Answer: 8", "a sum on something that is not a number", "CARD-TEXT",
                   "float / decimal number"):
        assert secret not in made["text"]
    assert made["left_out"] is True
    assert "Read this code." in made["text"]


def test_a_marking_scheme_line_inside_a_fence_does_not_end_the_paper():
    text = "---\ndewmark: 1\n---\n\n```text\n# Marking scheme\n```\n\nAfter.\n"
    paper, rest = split_halves(text)
    assert rest == "" and "After." in paper


def test_split_halves_joins_back_exactly():
    paper, rest = split_halves(SPECIMEN)
    assert paper + "\n" + rest == SPECIMEN
    assert rest.startswith("# Marking scheme")


def test_a_copy_package_holds_the_specimen_the_settings_and_the_word_paper():
    made = build_package("copy", WORD_PAPER, ABOUT)
    text = made["text"]
    assert made["problems"] == []
    assert "THE SPECIMEN" in text and "code: specimen-short" in text
    assert "THE SETTINGS (use exactly these)" in text and "code: word-paper" in text
    assert "(as written in Word)" in text and "State what this code prints" in text
    assert "Copy every word of the paper as written." in text


def test_a_copy_package_says_which_details_are_missing():
    made = build_package("copy", WORD_PAPER, {"code": "x"})
    assert any("\"title\" is missing" in p for p in made["problems"])
    assert build_package("copy", WORD_PAPER, dict(ABOUT, colour="red"))["problems"] == [
        "\"colour\" is not a setting dewmark knows."]


def test_an_unknown_mode_is_an_error():
    with pytest.raises(ValueError):
        build_package("shorten", SPECIMEN)


def test_the_cheat_sheet_in_the_package_is_the_one_in_the_format_document():
    doc = (ROOT / "docs" / "EXAM_FORMAT.md").read_text(encoding="utf-8")
    section = doc[doc.index("## 8. The teacher's cheat sheet"):doc.index("## 9. Migration")]
    sheet = re.search(r"^````\n(.*?)\n````$", section, re.S | re.M).group(1)
    assert (DATA / "cheat-sheet.txt").read_text(encoding="utf-8") == sheet + "\n"


def test_the_specimen_reads_with_no_problems_and_no_warnings():
    paper = read(SPECIMEN)
    assert not paper["messages"] and paper["total"] == 20


@pytest.mark.parametrize("text, what", [
    ("Write to jo.bloggs@college.ie for help.", "an e-mail address"),
    ("Candidate 1234567T sat this.", "a PPS number"),
    ("Student number: 20261234", "a student number"),
    ("Ring +353 1 234 5678 now.", "a phone number"),
    ("The id was 20261234.", "a long number"),
])
def test_the_scan_finds_what_may_be_student_information(text, what):
    found = scan_for_student_data(text)
    assert [f["what"] for f in found] == [what] and found[0]["line"] == 1


def test_the_scan_leaves_an_ordinary_paper_alone():
    assert scan_for_student_data(SPECIMEN) == []
    for path in PDP:
        assert scan_for_student_data(path.read_text(encoding="utf-8")) == [], path.name
    assert scan_for_student_data("Take 4.5 cm, 99999 is too large? 3.14159 pi, 1,000,000.5.") == []


@pytest.mark.parametrize("line", ["a" * 200000, "a." * 100000, "1 " * 100000, "x@" * 50000,
                                  "9" * 200000])
def test_the_scan_takes_a_long_pasted_line_in_its_stride(line):
    started = time.time()
    scan_for_student_data(line)
    assert time.time() - started < 5


def test_the_scan_still_finds_an_address_far_along_a_long_line():
    line = "word " * 5000 + "write to jo@college.ie please " + "word " * 5000
    assert [f["what"] for f in scan_for_student_data(line)] == ["an e-mail address"]


def test_a_package_reports_what_the_scan_finds():
    text = SPECIMEN.replace("Read this code.", "Read this code, from jo@college.ie.")
    assert [f["what"] for f in build_package("tidy", text)["findings"]] == ["an e-mail address"]


def test_follow_up_puts_each_problem_in_words_for_the_assistant():
    result = check_reply(SPECIMEN, wrap(reword(SPECIMEN, "(3 marks)", "(4 marks)")), "tidy")
    text = follow_up(result["messages"], "tidy")
    assert "Fix only these" in text and PAPER_BEGIN in text
    assert "heading" in text and text.count("\n- ") == len(result["messages"])


# --- finding the paper in a reply -----------------------------------------------

def test_the_paper_is_what_lies_between_the_markers_and_notes_are_kept_apart():
    paper, notes, messages = extract_reply(
        "Sure!\n" + wrap("---\nx: 1\n---\nText", "Changed one word.") + "Hope that helps.")
    assert paper == "---\nx: 1\n---\nText"
    assert notes == "Changed one word." and not messages


def test_markers_in_bold_are_still_markers():
    paper, _, _ = extract_reply(f"**{PAPER_BEGIN}**\n---\na: b\n---\n**{PAPER_END}**")
    assert paper == "---\na: b\n---"


def test_a_code_fence_around_the_paper_is_taken_off():
    body = SPECIMEN.strip("\n")
    for reply in ("```markdown\n" + body + "\n```", wrap("```\n" + body + "\n```")):
        paper, _, _ = extract_reply(reply)
        assert paper == body


def test_chat_above_the_settings_is_dropped_with_a_warning():
    paper, _, messages = extract_reply("Here is your paper:\n\n---\na: b\n---\nText")
    assert paper.startswith("---") and [m.code for m in messages] == ["reply-preamble"]


def test_a_reply_with_no_end_marker_warns_that_it_may_be_cut_off():
    _, _, messages = extract_reply(f"{PAPER_BEGIN}\n---\na: b\n---\nText")
    assert [m.code for m in messages] == ["reply-no-end"]


# --- a wording mode's reply -------------------------------------------------------

def test_a_reply_that_changes_nothing_is_accepted_unchanged():
    result = check_reply(SPECIMEN, wrap(SPECIMEN.split("# Marking scheme")[0].rstrip("\n")), "tidy")
    assert result["ok"] and result["hunks"] == []
    assert result["text"] == SPECIMEN


def test_a_reply_needs_no_markers_and_may_come_in_a_fence():
    head = SPECIMEN.split("# Marking scheme")[0]
    for reply in (head, "```markdown\n" + head.strip("\n") + "\n```", "Here:\n\n" + head):
        assert check_reply(SPECIMEN, reply, "tidy")["ok"]


def test_a_change_of_wording_is_a_hunk_with_its_place_and_can_be_taken_or_left():
    head = SPECIMEN.split("# Marking scheme")[0]
    reply = wrap(reword(head, "Read this code.", "Read this code carefully.").rstrip("\n"))
    result = check_reply(SPECIMEN, reply, "tidy")
    assert result["ok"] and len(result["hunks"]) == 1
    hunk = result["hunks"][0]
    assert hunk["before"] == ["Read this code."] and hunk["after"] == ["Read this code carefully."]
    assert hunk["where"] == "1(a): A variable" and hunk["line"] == 25 and hunk["accepted"]
    assert "Read this code carefully." in result["text"]
    left = check_reply(SPECIMEN, reply, "tidy", accept=[])
    assert left["text"] == SPECIMEN and not left["hunks"][0]["accepted"]
    assert left["ok"]


def test_each_change_can_be_taken_or_left_on_its_own():
    head = SPECIMEN.split("# Marking scheme")[0]
    head = reword(head, "Read this code.", "Read this code carefully.")
    head = reword(head, "Complete the sentences.", "Fill in the sentences.")
    reply = wrap(head.rstrip("\n"))
    result = check_reply(SPECIMEN, reply, "tidy")
    assert [h["id"] for h in result["hunks"]] == [1, 2]
    only_second = check_reply(SPECIMEN, reply, "tidy", accept=[2])
    assert "Fill in the sentences." in only_second["text"]
    assert "Read this code." in only_second["text"]
    assert [h["accepted"] for h in only_second["hunks"]] == [False, True]


def test_a_heading_title_may_change_and_shows_as_a_heading_change():
    head = SPECIMEN.split("# Marking scheme")[0]
    result = check_reply(SPECIMEN, wrap(reword(head, "1(a): A variable (3 marks)",
                                               "1(a): What a variable holds (3 marks)")), "tidy")
    assert result["ok"] and [h["kind"] for h in result["hunks"]] == ["heading"]


def test_a_paragraph_may_be_added_or_taken_out():
    added = reword(HEAD, "```answer 1(a)\n```\n\n", "```answer 1(a)\n```\n\nTake your time.\n\n")
    result = check_reply(SPECIMEN, wrap(added), "tidy")
    assert result["ok"] and result["hunks"][0]["before"] == []
    assert result["hunks"][0]["after"] == ["Take your time."]
    assert "Take your time." in result["text"]
    assert check_reply(SPECIMEN, wrap(added), "tidy", accept=[])["text"] == SPECIMEN
    removed = check_reply(SPECIMEN, wrap(reword(HEAD, "Read this code.\n\n", "")), "tidy")
    assert removed["ok"] and removed["hunks"][0]["after"] == []
    assert "Read this code." not in removed["text"]


def test_a_numbered_list_may_become_bullets():
    head = SPECIMEN.split("# Marking scheme")[0]
    bullets = reword(reword(head, "1. Answer **all**", "- Answer **all**"),
                     "2. Your work saves", "- Your work saves")
    assert check_reply(SPECIMEN, wrap(bullets), "udl")["ok"]


HEAD = SPECIMEN.split("# Marking scheme")[0]


@pytest.mark.parametrize("code, old, new", [
    ("reply-settings-changed", "total marks: 20", "total marks: 30"),
    ("reply-settings-changed", "code: specimen-short", "code: specimen-two"),
    ("reply-heading-changed", "1(a): A variable (3 marks)", "1(a): A variable (4 marks)"),
    ("reply-heading-changed", "### 1(b): Choosing", "### 1(c): Choosing"),
    ("reply-heading-changed", "# Section A: Short", "# Section B: Short"),
    ("reply-box-changed", "price = 4", "price = 5"),
    ("reply-box-changed", "```answer 1(a)", "```essay 1(a)"),
    ("reply-box-changed", "B. total_cost", "B. cost_total"),
    ("reply-box-changed", "# Write your function here", "# Write your answer here"),
    ("reply-number-changed", "with the value 21", "with the value 12"),
    ("reply-formula-changed", "called `double`", "called `twice`"),
])
def test_a_reply_that_changes_anything_but_wording_is_refused(code, old, new):
    result = check_reply(SPECIMEN, wrap(reword(HEAD, old, new)), "tidy")
    assert not result["ok"] and result["text"] is None
    assert code in codes(result)
    message = next(m for m in result["messages"] if m.code == code)
    assert message.what and message.fix and message.where == "the reply"


def test_a_fence_line_or_a_box_taken_out_or_put_in_is_refused():
    gone = reword(HEAD, "```answer 1(a)\n```\n", "")
    assert "reply-box-changed" in codes(check_reply(SPECIMEN, wrap(gone), "tidy"))
    extra = reword(HEAD, "Read this code.", "Read this code.\n\n```answer 1(a): extra\n```")
    assert "reply-box-changed" in codes(check_reply(SPECIMEN, wrap(extra), "tidy"))


def test_a_new_heading_with_marks_is_refused_and_one_without_marks_is_words():
    new = reword(HEAD, "Read this code.", "### 1(z): New part (2 marks)\n\nRead this code.")
    assert "reply-heading-changed" in codes(check_reply(SPECIMEN, wrap(new), "tidy"))
    plain = reword(HEAD, "Read this code.", "#### Look closely\n\nRead this code.")
    assert check_reply(SPECIMEN, wrap(plain), "tidy")["ok"]


def test_a_reply_with_a_marking_scheme_is_refused():
    with_scheme = wrap(HEAD + "# Marking scheme\n\n### 1(a)\n\nAnswer: 8\n")
    result = check_reply(SPECIMEN, with_scheme, "tidy")
    assert "reply-has-scheme" in codes(result) and not result["ok"]
    assert result["text"] is None


def test_a_number_in_a_heading_title_or_a_picture_name_is_protected():
    text = SPECIMEN.replace("Read this code.", "See ![a chart](pictures/chart-1.svg) and read this code.")
    head = text.split("# Marking scheme")[0]
    changed = reword(head, "pictures/chart-1.svg", "pictures/chart-2.svg")
    assert "reply-formula-changed" in codes(check_reply(text, wrap(changed), "tidy"))
    reworded = reword(head, "a chart", "a bar chart of sales")
    assert check_reply(text, wrap(reworded), "tidy")["ok"]


def test_every_refusal_is_listed_not_just_the_first():
    bad = reword(reword(HEAD, "total marks: 20", "total marks: 21"), "price = 4", "price = 5")
    assert {"reply-settings-changed", "reply-box-changed"} <= set(codes(check_reply(SPECIMEN, wrap(bad), "tidy")))


def test_a_changed_number_is_listed_beside_a_changed_line_of_an_answer_box():
    bad = reword(reword(HEAD, "with the value 21", "with the value 12"), "price = 4", "price = 5")
    result = check_reply(SPECIMEN, wrap(bad), "tidy")
    assert {"reply-box-changed", "reply-number-changed"} <= set(codes(result))
    assert not result["ok"] and result["hunks"] == [] and result["text"] is None


def test_a_box_taken_out_does_not_hide_a_changed_number_after_it():
    bad = reword(reword(HEAD, "```answer 1(a)\n```\n", ""), "with the value 21", "with the value 12")
    assert {"reply-box-changed", "reply-number-changed"} <= set(codes(check_reply(SPECIMEN, wrap(bad), "tidy")))


def test_an_empty_reply_and_a_reply_of_only_chat_are_refused():
    assert codes(check_reply(SPECIMEN, "", "tidy")) == ["reply-empty"]
    assert not check_reply(SPECIMEN, "I can't help with that.", "tidy")["ok"]


def test_a_reply_cannot_add_a_problem_the_paper_did_not_have():
    # Break the sum by changing a mark the check should already have caught.
    result = check_reply(SPECIMEN, wrap(reword(HEAD, "(12 marks)", "(13 marks)")), "tidy")
    assert not result["ok"] and "reply-heading-changed" in codes(result)


def test_a_papers_own_problems_are_not_blamed_on_the_reply():
    broken = reword(SPECIMEN, "total marks: 20", "total marks: 19")
    head = broken.split("# Marking scheme")[0]
    result = check_reply(broken, wrap(reword(head, "Read this code.", "Read this code twice.")), "tidy")
    assert result["ok"] and "total-marks" not in codes(result)


def test_the_marking_scheme_and_the_reference_come_back_exactly_as_they_were():
    text = SPECIMEN.replace("# Marking scheme", "# Reference\n\n## Card\n\nCARD-TEXT\n\n# Marking scheme")
    head, rest = split_halves(text)
    reply = wrap(reword(head, "Read this code.", "Read this code twice.").rstrip("\n"))
    result = check_reply(text, reply, "invite")
    assert result["ok"] and result["text"].endswith(rest)
    assert "CARD-TEXT" in result["text"] and "Answer: 8" in result["text"]


def test_the_assistants_notes_are_kept_for_the_teacher():
    result = check_reply(SPECIMEN, wrap(HEAD.rstrip("\n"), "Changed nothing."), "plain")
    assert result["notes"] == "Changed nothing."


def test_the_modes_that_change_wording_share_one_check():
    reply = wrap(reword(HEAD, "Read this code.", "Look at this code.").rstrip("\n"))
    for mode in ("tidy", "plain", "udl", "invite"):
        assert check_reply(SPECIMEN, reply, mode)["ok"]
    with pytest.raises(ValueError):
        check_reply(SPECIMEN, reply, "shorten")


def test_a_reply_or_paper_too_long_to_compare_is_refused_at_once():
    long_paper = HEAD + "More words.\n" * reply_module.MAX_LINES
    started = time.time()
    result = check_reply(SPECIMEN, wrap(long_paper), "tidy")
    assert codes(result) == ["reply-too-long"] and time.time() - started < 5


def test_a_copy_too_long_to_compare_word_by_word_says_so_and_still_checks_numbers(monkeypatch):
    monkeypatch.setattr(reply_module, "MAX_WORDS", 10)
    result = check_reply(WORD_PAPER, wrap(reword(COPIED, "4 * 2.5", "4 * 2.6").rstrip("\n")),
                         "copy", ABOUT)
    assert "reply-words-not-compared" in codes(result, "warning")
    assert codes(result) == ["reply-number-lost"] and result["kept"] is None


# --- the four PDP papers, reworded by a fake assistant --------------------------------

def fake_assistant(paper):
    """Reword the plain sentences outside every fence, the way a tidy might:
    a sentence of only letters, spaces and commas gets a few words added."""
    out, fence = [], None
    for line in paper.split("\n"):
        if fence:
            if set(line.strip()) == {fence[0]} and len(line.strip()) >= len(fence):
                fence = None
            out.append(line)
            continue
        opener = re.match(r"^(`{3,}|~{3,})", line)
        if opener:
            fence = opener.group(1)
            out.append(line)
        elif re.match(r"^[A-Za-z][A-Za-z ,']*[.:?]$", line):
            out.append(line + " Take your time.")
        else:
            out.append(line)
    return "\n".join(out)


@pytest.mark.parametrize("path", PDP, ids=lambda p: p.name)
@pytest.mark.parametrize("mode", ["tidy", "invite"])
def test_a_fake_assistant_rewording_a_real_paper_is_accepted(path, mode):
    original = path.read_text(encoding="utf-8")
    head, rest = split_halves(original)
    result = check_reply(original, wrap(fake_assistant(head).rstrip("\n")), mode)
    assert result["ok"], [str(m) for m in result["messages"] if m.level == "problem"]
    assert result["hunks"], "the fake assistant should have changed something"
    assert result["text"].endswith(rest)
    after = read(result["text"])
    assert after["total"] == read(original)["total"]
    assert list(after["boxes"]) == list(read(original)["boxes"])
    assert after["messages"].codes() == read(original)["messages"].codes()
    assert check_reply(original, wrap(fake_assistant(head).rstrip("\n")), mode,
                       accept=[])["text"] == original


@pytest.mark.parametrize("path", PDP, ids=lambda p: p.name)
def test_a_fake_assistant_that_changes_a_digit_in_a_real_paper_is_refused(path):
    original = path.read_text(encoding="utf-8")
    head, _ = split_halves(original)
    lines, fence, changed = head.split("\n"), None, False
    body = lines.index("---", 1) + 1          # leave the settings alone
    for index, line in enumerate(lines):
        if index < body:
            continue
        if fence:
            if set(line.strip()) == {fence[0]} and len(line.strip()) >= len(fence):
                fence = None
            continue
        m = re.match(r"^(`{3,}|~{3,})", line)
        if m:
            fence = m.group(1)
        elif not line.startswith("#") and not line.startswith("---") and re.search(r"\d", line) \
                and not re.match(r"^\s*\d+[.)]\s", line) and ":" not in line[:12]:
            lines[index] = re.sub(r"\d", lambda d: str((int(d.group(0)) + 1) % 10), line, count=1)
            changed = True
            break
    assert changed
    result = check_reply(original, wrap("\n".join(lines).rstrip("\n")), "tidy")
    assert not result["ok"]
    assert set(codes(result)) & {"reply-number-changed", "reply-formula-changed"}


# --- copy without composing ---------------------------------------------------------

COPIED = """\
---
dewmark: 1
code: word-paper
kind: practice
title: Word Paper
module: Introduction to Computing
module code: 5N0000
total marks: 10
time allowed: 1 hour
---

## Instructions

Answer both questions.

## Question 1: Variables (6 marks)

### 1(a): State what this code prints: print(4 * 2.5) (2 marks)

```answer 1(a)
```

### 1(b): Explain why the name 2nd_place is not allowed in Python. (4 marks)

```answer 1(b)
```

## Question 2: Lists (4 marks)

Write a list of three colours.

```answer 2
```
"""


def test_a_faithful_copy_is_accepted_with_a_scheme_of_drafts_to_fill():
    result = check_reply(WORD_PAPER, wrap(COPIED.rstrip("\n"), "Unsure about 1(a)."), "copy", ABOUT)
    assert result["ok"], [str(m) for m in result["messages"]]
    assert result["kept"] > 0.95 and result["hunks"] == []
    assert result["notes"] == "Unsure about 1(a)."
    final = read(result["text"])
    assert final["messages"].problems == [] and final["total"] == 10
    assert final["scheme"]["drafts"] == ["q1a", "q1b", "q2"]
    assert "### 1(a) (draft)" in result["text"]


def test_a_copy_that_changes_a_word_is_reported_word_by_word():
    reworded = reword(COPIED, "Write a list of three colours.", "Make a list of three colours.")
    result = check_reply(WORD_PAPER, wrap(reworded.rstrip("\n")), "copy", ABOUT)
    assert result["ok"] and codes(result, "warning") == ["reply-words-changed"]
    message = next(m for m in result["messages"] if m.code == "reply-words-changed")
    assert "make" in message.what and "write" in message.what and message.line > 1
    assert result["kept"] < 1


def test_a_copy_that_loses_a_number_is_refused():
    result = check_reply(WORD_PAPER, wrap(reword(COPIED, "4 * 2.5", "4 * 2.6").rstrip("\n")),
                         "copy", ABOUT)
    assert not result["ok"] and codes(result) == ["reply-number-lost"]
    assert "2.5" in result["messages"][0].what


def test_a_copy_must_start_with_the_settings_it_was_given():
    result = check_reply(WORD_PAPER, wrap(reword(COPIED, "total marks: 10", "total marks: 12")
                                          .rstrip("\n")), "copy", ABOUT)
    assert "reply-settings-changed" in codes(result) and not result["ok"]


def test_a_copy_cannot_be_checked_without_the_papers_details():
    result = check_reply(WORD_PAPER, wrap(COPIED), "copy", {"code": "x"})
    assert codes(result) == ["reply-about-missing"] and result["text"] is None


def test_a_copys_own_problems_come_back_with_the_readers_codes():
    wrong = reword(COPIED, "(4 marks)\n", "(5 marks)\n")
    result = check_reply(WORD_PAPER, wrap(wrong.rstrip("\n")), "copy", ABOUT)
    assert result["text"] is not None and "marks-sum" in codes(result)
    assert not [c for c in codes(result) if c.startswith("reply-")]
    assert result["ok"]


# --- the command line ---------------------------------------------------------------

def test_package_and_reply_from_the_command_line(tmp_path, capsys):
    paper = tmp_path / "paper.exam.md"
    paper.write_text(SPECIMEN, encoding="utf-8")
    out = tmp_path / "package.txt"
    assert main(["package", "tidy", str(paper), "-o", str(out)]) == 0
    assert out.read_text(encoding="utf-8").startswith("THIS CONTAINS YOUR EXAM PAPER")
    reply = tmp_path / "reply.txt"
    reply.write_text(wrap(reword(HEAD, "Read this code.", "Read this code twice.").rstrip("\n"),
                          "One change."), encoding="utf-8")
    done = tmp_path / "done.exam.md"
    assert main(["reply", "tidy", str(paper), str(reply), "-o", str(done)]) == 0
    shown = capsys.readouterr().out
    assert "+ Read this code twice." in shown and "- Read this code." in shown
    assert "One change." in shown and "Accepted." in shown
    assert "Read this code twice." in done.read_text(encoding="utf-8")
    reply.write_text(wrap(reword(HEAD, "price = 4", "price = 5").rstrip("\n")), encoding="utf-8")
    assert main(["reply", "tidy", str(paper), str(reply), "-o", str(tmp_path / "no.md")]) == 1
    assert "Refused: nothing was written." in capsys.readouterr().out
    assert not (tmp_path / "no.md").exists()


def test_a_copy_package_from_the_command_line_asks_for_the_details(tmp_path, capsys):
    word = tmp_path / "word.txt"
    word.write_text(WORD_PAPER, encoding="utf-8")
    assert main(["package", "copy", str(word)]) == 1
    assert "\"title\" is missing" in capsys.readouterr().out
    args = ["package", "copy", str(word)]
    for key, value in ABOUT.items():
        args += ["--set", f"{key}: {value}"]
    assert main(args) == 0
    assert "code: word-paper" in capsys.readouterr().out
