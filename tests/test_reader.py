"""Tests for the reader of the exam format (dewmark/reader.py,
docs/EXAM_FORMAT.md).

Most tests write a small paper and check which message codes come back.
The hostile cases from the format judgement (§1 of the format document)
are here as tests, so a regression that turns a typo back into a leak
fails the build. The specimen paper and the four converted PDP papers are
read in full.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dewmark.convert_pdp import _maths, convert  # noqa: E402
from dewmark.reader import read  # noqa: E402
from dewmark.scheme import read_key  # noqa: E402

HEADER = """\
---
dewmark: 1
code: t-2027
kind: {kind}
title: T
module: M
module code: 5N0000
total marks: {total}
time allowed: 1 hour
{extra}---
"""


def paper(body, scheme=None, kind="exam", total=10, extra=""):
    text = HEADER.format(kind=kind, total=total, extra=extra) + body
    if scheme is not None:
        text += "\n# Marking scheme\n" + scheme
    return read(text)


def problems(result):
    return [m.code for m in result["messages"].problems]


def warnings(result):
    return [m.code for m in result["messages"].warnings]


# --- a clean paper ---------------------------------------------------------

def test_the_specimen_paper_reads_with_no_problems():
    result = read((ROOT / "tests" / "fixtures" / "specimen.exam.md").read_text())
    assert problems(result) == []
    assert result["total"] == 96
    assert len(result["boxes"]) == 24
    assert result["scheme"]["drafts"] == ["q1b.ii"]
    assert {"q1b.i.your-function", "q1b.i.your-tests", "q2a.working", "q2a.answer",
            "q4.working", "q6.plan", "q1.rough-work"} <= set(result["boxes"])
    assert result["boxes"]["q6.plan"]["unmarked"]
    assert result["scheme"]["entries"]["q6"]["method"] == "criteria"
    assert result["scheme"]["entries"]["q1a"]["method"] == "points"


@pytest.mark.parametrize("page", sorted((ROOT / "experiments" / "pdp-5n2927").glob("*.html")))
def test_every_pdp_paper_converts_and_reads_with_no_problems(page, tmp_path):
    text, _ = convert(page.read_text(encoding="utf-8"), "paper", tmp_path / "pictures")
    result = read(text)
    assert problems(result) == [], [str(m) for m in result["messages"]]
    assert result["total"] == 60
    assert len([u for u in result["units"].values() if u["level"] == 2]) == 4
    assert result["scheme"]["drafts"]


def test_the_converted_pdp_papers_in_samples_are_current():
    for page in sorted((ROOT / "experiments" / "pdp-5n2927").glob("*.html")):
        stem = page.name.lower().removesuffix(".html").replace("_", "-")
        text, _ = convert(page.read_text(encoding="utf-8"), stem)
        committed = ROOT / "samples" / "pdp-5n2927" / f"{stem}.exam.md"
        assert committed.read_text(encoding="utf-8") == text, (
            f"{committed} is out of date: run python -m dewmark.convert_pdp "
            "samples/pdp-5n2927 experiments/pdp-5n2927/*.html")


def test_pdp_names_follow_the_printed_numbers():
    page = ROOT / "experiments" / "pdp-5n2927" / "PDP_5N2927_Sample_Exam.html"
    result = read(convert(page.read_text(encoding="utf-8"), "sample")[0])
    assert {"q1a.i", "q1a.ii", "q1a.iii", "q1b", "q1b.test-your-names"} <= set(result["boxes"])
    assert result["boxes"]["q1b.test-your-names"]["unmarked"]


def test_html_maths_in_the_pdp_pages_becomes_one_formula():
    assert _maths("(iv) 4π<i>r</i>²") == "(iv) $4\\pi r^2$"
    formula = ('<i>V</i> = <span class="frac"><span>4</span><span>3</span></span>π<i>r</i>³')
    assert _maths(formula) == "$V = \\frac{4}{3}\\pi r^3$"


# --- settings --------------------------------------------------------------

def test_values_are_text_until_a_known_key_converts_them():
    result = paper("## Question 1: Q (10 marks)\n```answer\n```\n", "",
                   extra="version: 1.10\nnumber example: 0123\n")
    assert result["settings"]["version"] == "1.10"
    assert result["settings"]["number example"] == "0123"


def test_an_unknown_setting_is_refused_with_the_nearest_match():
    result = paper("## Question 1: Q (10 marks)\n```answer\n```\n", "", extra="timr: shown\n")
    message = next(m for m in result["messages"] if m.code == "unknown-setting")
    assert "timer" in message.fix


def test_a_repeated_setting_and_a_value_outside_its_list_are_refused():
    result = paper("## Question 1: Q (10 marks)\n```answer\n```\n", "",
                   extra="timer: hidden\nbreaks: on\nbreaks: off\n")
    assert "setting-value" in problems(result)
    assert "repeated-setting" in problems(result)


def test_switches_accept_yes_no_and_true_false():
    result = paper("## Question 1: Q (10 marks)\n```answer\n```\n", "",
                   extra="breaks: Yes\ncode completion: TRUE\n")
    assert result["settings"]["breaks"] == "on"
    assert result["settings"]["code completion"] == "on"


def test_an_exam_cannot_show_answers_or_run_practice_tests():
    result = paper("## Question 1: Q (10 marks)\n```answer\n```\n", "",
                   extra="show answers: after finishing\n")
    assert "exam-shows-answers" in problems(result)


def test_an_exam_needs_its_module_code():
    text = HEADER.format(kind="exam", total=10, extra="").replace("module code: 5N0000\n", "")
    result = read(text + "## Question 1: Q (10 marks)\n```answer\n```\n# Marking scheme\n")
    assert "missing-setting" in problems(result)


# --- the hostile cases (docs/EXAM_FORMAT.md §1) -----------------------------

def test_1_python_is_a_listing_and_python_exec_a_cell():
    result = paper("## Question 1: Code (10 marks)\n```python\nprint(2 * 3)\n```\n"
                   "```answer\n```\n", "### 1\nAnswer: 6\n")
    assert problems(result) == []
    assert [b["kind"] for b in result["boxes"].values()] == ["answer"]


def test_2_two_boxes_with_the_same_label_are_refused():
    result = paper("## Question 1: Q (10 marks)\n### 1(a): A (10 marks)\n"
                   "```answer 1(a): working\n```\n```answer 1(a): working\n```\n", "")
    assert "duplicate-name" in problems(result)


def test_4_answer_any_two_reads_from_the_section_heading():
    body = ("# Section B: Answer any two of Questions 1 to 3 (10 marks)\n"
            "## Question 1: A (5 marks)\n```answer\n```\n"
            "## Question 2: B (5 marks)\n```answer\n```\n"
            "## Question 3: C (5 marks)\n### (a) x (2 marks)\n```answer\n```\n"
            "### (b) y (3 marks)\n```answer\n```\n")
    result = paper(body, "")
    assert problems(result) == []
    assert result["total"] == 10
    assert "q3a" in result["boxes"]


def test_4_any_n_needs_equal_marks_and_enough_questions():
    body = ("# Section B: Answer any two (10 marks)\n"
            "## Question 1: A (5 marks)\n```answer\n```\n"
            "## Question 2: B (4 marks)\n```answer\n```\n")
    assert "any-unequal" in problems(paper(body, ""))


def test_6_marks_that_do_not_add_up_are_reported_once():
    result = paper("## Question 1: Q (10 marks)\n### 1(a): A (6 marks)\n```answer\n```\n"
                   "### 1(b): B (5 marks)\n```answer\n```\n", "")
    assert problems(result).count("marks-sum") == 1
    assert "total-marks" not in problems(result)


def test_7_keys_are_text_so_0123_stays_0123():
    assert read_key("0123") == [{"text": "0123"}]
    assert read_key("1.10") == [{"text": "1.10"}]
    assert read_key("No") == [{"text": "No"}]


def test_8a_scheme_text_above_the_line_is_refused():
    result = paper("## Question 1: Q (10 marks)\n```answer\nModel answer: denatured\n```\n"
                   "Model answer: denatured.\n- 2 marks: a point\n", "")
    assert problems(result).count("scheme-above-line") == 3


def test_8b_starter_text_that_gives_the_answer_away_is_refused():
    result = paper("## Question 1: Q (10 marks)\n```answer\nThe enzyme is denatured by heat.\n```\n",
                   "### 1\nModel answer: The enzyme is denatured by heat.\n")
    assert "starter-is-answer" in problems(result)


@pytest.mark.parametrize("heading", ["# Solutions", "# Mark answers", "# Answer key", "# Scheme"])
def test_8c_a_lookalike_scheme_heading_is_refused(heading):
    result = read(HEADER.format(kind="exam", total=10, extra="")
                  + f"## Question 1: Q (10 marks)\n```answer\n```\n{heading}\n### 1\n")
    assert "scheme-lookalike" in problems(result)
    assert "no-scheme" in problems(result)


@pytest.mark.parametrize("line", ["# Marking scheme", "# Mark scheme", "# MARKING SCHEME:",
                                  "# marking Scheme"])
def test_8c_the_ways_of_writing_the_dividing_line_are_accepted(line):
    result = read(HEADER.format(kind="exam", total=10, extra="")
                  + f"## Question 1: Q (10 marks)\n```answer\n```\n{line}\n### 1\n"
                  "- 10 marks: SECRET\n")
    assert problems(result) == []
    assert all("SECRET" not in b["body"] for b in result["boxes"].values())
    assert result["scheme"]["entries"]["q1"]["points"][0]["text"] == "SECRET"


def test_9_numbers_in_word_styles_are_read_and_curly_quotes_tidied():
    body = ("## Question 1 – Functions (10 marks)\n### 1.(a) Parts (5 marks)\n```choice\n"
            "A. Yes\nB. No\n```\n### Q1 b) More (5 marks)\n```answer\n```\n")
    result = paper(body, "### 1(a)\nAnswer: “B”\n")
    assert problems(result) == []
    assert {"q1a", "q1b"} == set(result["boxes"])


def test_10_a_table_under_the_question_is_shared_and_needs_no_syntax():
    body = ("## Question 1: Enzymes (6 marks)\n| T | 10 |\n|---|---|\n| t | 5 |\n"
            "### 1(a): A (3 marks)\n```answer\n```\n```material Figure 1\n![a figure](f.svg)\n```\n"
            "### 1(b): B (3 marks)\n```answer\n```\n")
    assert problems(paper(body, "", total=6)) == []


def test_11_an_option_holding_code_needs_four_backticks():
    fine = ("## Question 1: Q (10 marks)\n````choice\nA. `print(1)`\nB.\n   ```python\n"
            "   while True:\n       pass\n   ```\n````\n")
    assert problems(paper(fine, "### 1\nAnswer: B\n")) == []
    early = fine.replace("````", "```")
    assert "fence-closed-early" in problems(paper(early, ""))


def test_12_a_number_with_units_and_tolerance_and_two_answer_lines():
    assert read_key("4.88 ± 0.01 m") == [{"number": 4.88, "written": "4.88", "tolerance": 0.01,
                                          "percent": False, "unit": "m"}]
    assert read_key("12.4 to 12.6 cm")[0]["low"] == 12.4
    assert read_key("0.50 ± 0.005 per minute (2 d.p.)")[0]["dp"] == 2
    assert read_key("3/8") == [{"text": "3/8"}]
    assert len(read_key("vacuole / large vacuole")) == 2
    result = paper("## Question 1: Q (10 marks)\n```boxes\nHeight = ____ m\n```\n",
                   "### 1\nAnswer: 4.88 m ± 0.01\nAnswer: 488 cm\n")
    assert "two-answer-lines" in problems(result)


def test_12_a_key_whose_decimals_contradict_its_precision_is_refused():
    result = paper("## Question 1: Q (10 marks)\n```boxes\nRate = ____\n```\n",
                   "### 1\nAnswer: 0.5 ± 0.005 (2 d.p.)\n- 10 marks: x\n")
    message = next(m for m in result["messages"] if m.code == "key-precision")
    assert "0.50" in message.fix


def test_13_a_misspelt_fence_is_refused_and_never_shown():
    result = paper("## Question 1: Q (10 marks)\n```anwser\n```\n```pyhton exec 1: x\n```\n", "")
    fixes = [m.fix for m in result["messages"] if m.code == "unknown-kind"]
    assert fixes == ["Did you mean ```answer?", "Did you mean ```python exec?"]
    assert result["boxes"] == {}


def test_14_a_heading_without_marks_inside_a_part_is_text():
    result = paper("## Question 1: Q (10 marks)\n### 1(a): A (10 marks)\n#### Table 1\n"
                   "some table\n```answer\n```\n", "")
    assert problems(result) == []
    assert result["boxes"]["q1a"]["unit"] == "q1a"


def test_16_word_style_marks_in_the_scheme_are_warned_with_the_rewrite():
    result = paper("## Question 1: Q (10 marks)\n```answer\n```\n",
                   "### 1\nAward 2 marks for x\n(3) for y\n- 2m: z\n")
    assert warnings(result).count("guidance-looks-like-points") == 3


def test_an_exam_with_no_marking_scheme_is_refused():
    assert "no-scheme" in problems(paper("## Question 1: Q (10 marks)\n```answer\n```\n"))


def test_a_practice_paper_may_have_no_scheme():
    result = paper("## Question 1: Q (10 marks)\n```answer\n```\n", kind="practice")
    assert "no-scheme" not in problems(result)


def test_a_fence_with_no_word_is_refused():
    assert "fence-without-kind" in problems(paper("## Question 1: Q (10 marks)\n```\nx\n```\n", ""))


def test_a_repeated_title_heading_is_refused():
    result = paper("# Programming: Written Examination\n## Question 1: Q (10 marks)\n"
                   "```answer\n```\n", "")
    assert "heading-not-section" in problems(result)


def test_a_box_between_a_question_and_its_parts_has_no_marks():
    body = ("## Question 1: Q (10 marks)\n```answer\n```\n### 1(a): A (10 marks)\n"
            "```answer\n```\n")
    assert "box-outside-parts" in problems(paper(body, ""))
    rough = body.replace("```answer\n```\n### 1(a)", "```answer (not marked)\n```\n### 1(a)")
    assert "box-outside-parts" not in problems(paper(rough, ""))


# --- the marker's half ------------------------------------------------------

def test_an_entry_for_a_part_the_paper_lacks_is_refused():
    result = paper("## Question 1: Q (10 marks)\n### 1(a): A (4 marks)\n```answer\n```\n"
                   "### 1(c): B (6 marks)\n```answer\n```\n", "### 1(b)\n- 6 marks: x\n")
    assert "scheme-unknown-part" in problems(result)


def test_criteria_must_add_up_and_their_bands_must_cover_every_mark():
    scheme = ("### 1\n- **Argument** (6 marks)\n  - 4 to 6: good\n  - 0 to 3: poor\n"
              "- **Clarity** (3 marks)\n  - 2 to 3: clear\n  - 0 to 0: unclear\n")
    result = paper("## Question 1: Essay (10 marks)\n```essay\n```\n", scheme)
    codes = problems(result)
    assert "criteria-sum" in codes
    assert "criteria-bands" in codes
    message = next(m for m in result["messages"] if m.code == "criteria-sum")
    assert "add up to 9, but it is worth 10" in message.what


def test_points_and_criteria_may_not_be_mixed():
    scheme = "### 1\n- 5 marks: x\n- **Argument** (10 marks)\n  - 0 to 10: all\n"
    assert "mixed-methods" in problems(paper("## Question 1: Q (10 marks)\n```answer\n```\n", scheme))


def test_points_must_reach_the_parts_marks_and_may_go_beyond():
    body = "## Question 1: Q (4 marks)\n```answer\n```\n"
    assert "points-short" in problems(paper(body, "### 1\n- 1 mark: a\n- 2 marks: b\n", total=4))
    assert problems(paper(body, "### 1\n- 2 marks: a\n- 3 marks: b\n", total=4)) == []


def test_a_choice_key_must_name_an_option_and_its_check_phrase_must_match():
    body = ("## Question 1: Q (10 marks)\n```choice\nA. for n in range(5)\n"
            "B. for n in range(1, 6)\n```\n")
    assert problems(paper(body, "### 1\nAnswer: B (range(1, 6))\n")) == []
    assert "key-not-option" in problems(paper(body, "### 1\nAnswer: E\n"))
    swapped = paper(body, "### 1\nAnswer: A (range(1, 6))\n")
    message = next(m for m in swapped["messages"] if m.code == "key-check-phrase")
    assert "Option B contains" in message.what


def test_answers_must_match_the_boxes_one_for_one():
    body = "## Question 1: Q (10 marks)\n```boxes\n1 ____\n2 ____\n```\n"
    assert "answers-count" in problems(paper(body, "### 1\nAnswers:\n1. cell wall\n"))
    assert problems(paper(body, "### 1\nAnswers:\n1. cell wall\n2. vacuole\n")) == []


def test_a_key_for_a_word_bank_must_be_a_choice_the_student_can_make():
    body = ("## Question 1: Q (10 marks)\n```boxes\n1 ____\nChoose from: nucleus / vacuole\n```\n")
    assert problems(paper(body, "### 1\nAnswers:\n1. vacuole / large vacuole\n")) == []
    assert "key-not-option" in problems(paper(body, "### 1\nAnswers:\n1. chloroplast\n"))


def test_outcomes_are_checked_against_the_papers_list():
    result = paper("## Question 1: Q (10 marks)\n```answer\n```\n",
                   "## Question 1\nOutcomes: 2, 9\n", extra="outcomes: 1, 2, 3\n")
    assert "outcome-unknown" in problems(result)


def test_drafts_are_listed():
    result = paper("## Question 1: Q (10 marks)\n```answer\n```\n", "### 1 (draft)\n")
    assert result["scheme"]["drafts"] == ["q1"]


def test_every_message_says_where_what_and_carries_a_code():
    result = paper("## Question 1: Q (10 marks)\n### 1(a): A (6 marks)\n```answer\n```\n"
                   "### 1(b): B (5 marks)\n```anwser\n```\n", "### 9\n")
    for message in result["messages"]:
        assert message.code and message.line and message.what
