"""Rehearsals for the checker page (checker/index.html).

The page runs the reader inside Pyodide, so the first thing to prove is that
the browser gives the answers the command line gives. The rest is what a
teacher does with it: check a file, jump to a problem, make a package, take
or leave an assistant's changes. And what it must never do: save the paper,
or send it anywhere. Python comes from a CDN, which is the one request the
page makes.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dewmark import web  # noqa: E402
from dewmark.package import PAPER_BEGIN, PAPER_END, split_halves  # noqa: E402

SPECIMEN = (ROOT / "dewmark" / "data" / "specimen.exam.md").read_text(encoding="utf-8")
PDP = sorted((ROOT / "samples" / "pdp-5n2927").glob("*.exam.md"))


def reply_to(paper, old=None, new=None):
    head, _ = split_halves(paper)
    if old:
        assert old in head
        head = head.replace(old, new, 1)
    return f"{PAPER_BEGIN}\n{head.rstrip()}\n{PAPER_END}\n"


def open_help(page):
    page.click("#help > summary")


def test_the_browser_gives_the_same_answers_as_the_command_line(checker):
    """The reader, the package and the reply check, run in Pyodide and in
    CPython over the same text, must write the same JSON."""
    page = checker.page
    papers = [SPECIMEN] + [p.read_text(encoding="utf-8") for p in PDP]
    for text in papers:
        assert page.evaluate("t => api.check(t)", text) == web.check_json(text)
    assert page.evaluate("t => api.pack('invite', t, '{}')", SPECIMEN) == \
        web.package_json("invite", SPECIMEN, "{}")
    reply = reply_to(SPECIMEN, "Read this code.", "Look at this code.")
    assert page.evaluate("([t, r]) => api.reply('tidy', t, r, '{}', 'null')", [SPECIMEN, reply]) == \
        web.reply_json("tidy", SPECIMEN, reply, "{}", "null")
    assert page.evaluate("() => api.modes()") == web.modes_json()


def test_a_template_opened_as_it_stands_says_it_was_not_built(context):
    page = context.new_page()
    page.goto((ROOT / "checker" / "index.html").as_uri())
    page.wait_for_selector("#unbuilt:not(.hidden)")
    assert "not built" in page.inner_text("#unbuilt")


def test_an_example_checks_clean_and_a_broken_file_lists_its_problems(checker):
    page = checker.page
    page.click("#example")
    page.wait_for_function("document.getElementById('status').textContent.includes('No problems')")
    assert "20 marks, 2 questions, 5 answer boxes" in page.inner_text("#summary")
    page.fill("#editor", SPECIMEN.replace("(3 marks)", "(4 marks)", 1))   # 1(a) is worth one more
    page.click("#check")
    page.wait_for_selector("#messages .msg.problem")
    assert "1 problem" in page.inner_text("#status")
    first = page.inner_text("#messages .msg.problem")
    assert "marks-sum" in first and "Question 1's parts add up to 13 marks" in first
    assert page.is_visible("#copy-problems")


def test_a_problems_line_button_selects_that_line_in_the_editor(checker):
    page = checker.page
    page.fill("#editor", SPECIMEN.replace("(3 marks)", "(4 marks)", 1))
    page.click("#check")
    page.wait_for_selector("#messages .msg.problem button.jump")
    page.click("#messages .msg.problem button.jump")
    selected = page.evaluate("() => { const e = document.getElementById('editor');"
                             " return e.value.slice(e.selectionStart, e.selectionEnd); }")
    assert selected == "## Question 1: Variables and functions (12 marks)"
    assert page.evaluate("document.activeElement.id") == "editor"


def test_typing_checks_by_itself_after_a_pause(checker):
    page = checker.page
    page.fill("#editor", SPECIMEN)
    page.wait_for_function("document.getElementById('status').textContent.includes('No problems')")


def test_a_package_and_a_reply_with_one_change_of_wording(checker):
    page = checker.page
    page.fill("#editor", SPECIMEN)
    open_help(page)
    page.click("#make")
    page.wait_for_selector("#package-box:not(.hidden)")
    package = page.input_value("#package")
    assert package.startswith("THIS CONTAINS YOUR EXAM PAPER.")
    assert "Answer: 8" not in package, "the marking scheme must not be in the package"
    assert "Your marking scheme is not in it" in page.inner_text("#package-info")

    page.fill("#reply", reply_to(SPECIMEN, "Read this code.", "Look at this code."))
    page.click("#check-reply")
    page.wait_for_selector("#reply-result .hunk")
    assert "1 change of wording" in page.inner_text("#reply-result")
    assert "Look" in page.inner_text("#reply-result .hunk ins")
    assert "Read" in page.inner_text("#reply-result .hunk del")

    page.uncheck("#hunk-1")                       # leave it as the teacher wrote it
    assert page.evaluate("document.activeElement.id") == "hunk-1", "focus must survive a re-render"
    page.click("#reply-result button.primary")
    assert page.input_value("#editor") == SPECIMEN

    page.check("#hunk-1")
    page.click("#reply-result button.primary")
    assert page.input_value("#editor") == SPECIMEN.replace("Read this code.", "Look at this code.")


def test_a_reply_that_changes_a_number_is_refused_and_the_file_stays(checker):
    page = checker.page
    page.fill("#editor", SPECIMEN)
    open_help(page)
    page.click("#make")
    page.wait_for_selector("#package-box:not(.hidden)")
    page.fill("#reply", reply_to(SPECIMEN, "with the value 21", "with the value 12"))
    page.click("#check-reply")
    page.wait_for_selector("#reply-result .msg.problem")
    shown = page.inner_text("#reply-result")
    assert "reply-number-changed" in shown and "was not used" in shown
    assert page.is_visible("#reply-result >> text=Copy these problems")
    assert not page.query_selector("#reply-result .hunk")
    assert page.input_value("#editor") == SPECIMEN


def test_a_package_with_something_that_looks_like_student_information_waits_to_be_checked(checker):
    page = checker.page
    page.fill("#editor", SPECIMEN.replace("Read this code.", "Read this code, from jo@college.ie."))
    open_help(page)
    page.click("#make")
    page.wait_for_selector("#findings:not(.hidden)")
    assert "an e-mail address" in page.inner_text("#findings")
    assert page.is_disabled("#copy-package") and page.is_disabled("#save-package")
    page.check("#gate")
    assert page.is_enabled("#copy-package") and page.is_enabled("#save-package")


def test_copy_needs_the_papers_details_before_it_makes_a_package(checker):
    page = checker.page
    open_help(page)
    page.check("input[value=copy]")
    page.fill("#word-paper", "1. Variables (6 marks)\nState what print(4 * 2.5) prints. [6]\n")
    page.click("#make")
    page.wait_for_function("document.getElementById('make-status').textContent.includes('details')")
    for key, value in {"code": "word-paper", "title": "Word Paper", "module": "Computing",
                       "module-code": "5N0000", "total-marks": "6", "time-allowed": "1 hour"}.items():
        page.fill(f"#about-{key}", value)
    page.select_option("#about-kind", "practice")
    page.click("#make")
    page.wait_for_selector("#package-box:not(.hidden)")
    package = page.input_value("#package")
    assert "code: word-paper" in package and "THE SPECIMEN" in package


def test_nothing_is_saved_and_nothing_but_python_is_fetched(checker):
    page = checker.page
    page.fill("#editor", SPECIMEN)
    open_help(page)
    page.click("#make")
    page.wait_for_selector("#package-box:not(.hidden)")
    page.fill("#reply", reply_to(SPECIMEN, "Read this code.", "Look at this code."))
    page.click("#check-reply")
    page.wait_for_selector("#reply-result .hunk")
    assert page.evaluate("[localStorage.length, sessionStorage.length]") == [0, 0]
    assert page.evaluate("document.cookie") == ""
    for request in checker.requests:
        assert request.method == "GET", request.url
        assert request.url.startswith(("file://", "https://cdn.jsdelivr.net/", "data:", "blob:")), request.url
        assert request.post_data is None


def test_the_page_says_why_it_cannot_load_python_and_offers_to_try_again(context, checker_file):
    page = context.new_page()
    page.add_init_script("window.DEWMARK_PYTHON_BASE = 'https://cdn.jsdelivr.net/pyodide/no-such-version/full/';")
    page.goto(checker_file.as_uri())
    page.wait_for_selector("#load button")
    assert "could not load Python" in page.inner_text("#load")
    assert "Try again" in page.inner_text("#load")
