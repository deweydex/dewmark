"""Rehearsals for the browser's own print window (assets/page-finish.js, `printing`; assets/page.css).

The page's own PDF has a header and a footer on every page (tests/browser/test_pdf.py). The
print window is the backup when that PDF cannot be made, and what Ctrl+P gives, so it has
the same frame and the same answers. Chromium prints a page to PDF the way its print window
would, and PyMuPDF reads it back: every page is checked for its header in the top margin, its
footer in the bottom margin and its page number, and the answers are checked for being whole.
"""

import re

import pytest

from conftest import _unavailable
from helpers import begin, fill_everything, save_both, stored, write

try:
    import pymupdf
except ImportError:                                           # pragma: no cover
    pymupdf = None

TOP, BOTTOM = 24 * 72 / 25.4, 22 * 72 / 25.4                   # the page margins in points (assets/page.css)
HEADER = "Agnes Nitt · S12345 · rehearsal"


@pytest.fixture(autouse=True)
def reader():
    if pymupdf is None:
        _unavailable("PyMuPDF is not installed, so a printed page cannot be read back")


def long_answers(page):
    page.fill('[data-answer="q1a"] textarea', "\n".join(f"line {i} of a long answer" for i in range(1, 61)))
    page.fill('[data-answer="q1c"] textarea', " ".join(f"word{i}" for i in range(1, 400)))
    page.wait_for_timeout(200)


def printed(page, tmp_path, name="print.pdf"):
    """What the browser's print window would give, as a PDF read back: the paper shown in place of the
    finish sheet, and the same event the browser sends before it prints."""
    page.evaluate("""() => {
        document.getElementById('dm-finish-screen').hidden = true;
        document.getElementById('dm-app').hidden = false;
        window.dispatchEvent(new Event('beforeprint'));
    }""")
    target = tmp_path / name
    page.pdf(path=str(target), format="A4", print_background=True, prefer_css_page_size=True)
    page.evaluate("() => window.dispatchEvent(new Event('afterprint'))")
    return pymupdf.open(str(target))


def sitting(context, pages, name="Agnes Nitt", number="S12345"):
    from helpers import open_page
    page = open_page(context, pages["student"])
    begin(page, name=name, number=number)
    return page


def test_every_printed_page_has_the_header_at_the_top_and_the_footer_at_the_foot_and_a_page_number(context, pages, tmp_path):
    page = sitting(context, pages)
    long_answers(page)
    doc = printed(page, tmp_path)
    assert len(doc) >= 4, "the rehearsal needs a paper that runs over several pages"
    for number, sheet in enumerate(doc, start=1):
        head = sheet.search_for(HEADER)
        assert head and head[0].y1 <= TOP, f"page {number} has no header in the top margin: {head}"
        foot = sheet.search_for("Paper ID")
        assert foot and foot[0].y0 >= sheet.rect.height - BOTTOM, f"page {number} has no footer in the bottom margin"
        assert f"Page {number} of {len(doc)}" in sheet.get_text(), f"page {number} is not numbered"


def test_the_footer_has_the_paper_id_the_page_shows_and_no_receipt_until_the_student_has_saved(context, pages, tmp_path):
    page = sitting(context, pages)
    long_answers(page)
    paper_id = page.evaluate("() => MODEL.exam.fingerprint")
    first = printed(page, tmp_path, "before.pdf")
    assert f"Paper ID {paper_id} · No receipt yet" in first[0].get_text().replace("\n", " ")
    save_both(page)
    receipt = stored(page)["dewmark:rehearsal:student"]["receipt"]
    later = printed(page, tmp_path, "after.pdf")
    assert all(f"Paper ID {paper_id} · Receipt {receipt}" in sheet.get_text().replace("\n", " ") for sheet in later)


def test_a_long_answer_is_printed_whole_not_clipped_to_its_last_lines(context, pages, tmp_path):
    page = sitting(context, pages)
    long_answers(page)
    text = "".join(sheet.get_text() for sheet in printed(page, tmp_path))
    assert all(f"line {i} of a long answer" in text for i in range(1, 61))
    assert all(f"word{i}" in text for i in range(1, 400))


def test_every_kind_of_answer_is_printed(context, pages, tmp_path):
    page = sitting(context, pages)
    fill_everything(page)
    text = "".join(sheet.get_text() for sheet in printed(page, tmp_path))
    for expected in ("alpha", "x = 2", "one two three", "print(1)", "print(2)", "root", "stem", "plant", "leaves"):
        assert expected in text, expected


@pytest.mark.parametrize("name", [
    "<b>Agnes</b> & <i>Nitt</i>",
    'Agnes "Nitt" \\ Smith',
    "Síle Ní Bhriain-O'Connor",
    'x"; } body { display: none } /*',
])
def test_a_name_with_markup_quotes_or_css_in_it_is_printed_as_the_words_it_is(context, pages, tmp_path, name):
    page = sitting(context, pages, name=name)
    long_answers(page)
    doc = printed(page, tmp_path)
    for number, sheet in enumerate(doc, start=1):
        assert sheet.search_for(f"{name} · S12345 · rehearsal"), f"page {number}: {name}"
    assert "line 60 of a long answer" in "".join(sheet.get_text() for sheet in doc), "the name changed the page"


def test_a_long_name_and_a_long_exam_code_still_fit_in_the_top_margin(context, pages, tmp_path):
    name = "Bartholomew Maximilian Featherstonehaugh-Cholmondeley"
    page = sitting(context, pages, name=name, number="D00123456789")
    long_answers(page)
    for number, sheet in enumerate(printed(page, tmp_path), start=1):
        found = sheet.search_for(f"{name} · D00123456789 · rehearsal")
        assert found and found[0].y1 <= TOP, f"page {number} wraps or loses a long name"


def frame(page):
    """The two custom properties that the page margins read, as the page set them."""
    return page.evaluate("""() => ({
        who: document.documentElement.style.getPropertyValue('--dm-print-who'),
        foot: document.documentElement.style.getPropertyValue('--dm-print-foot') })""")


def test_nothing_of_the_frame_is_on_the_screen_or_in_the_readable_copy(context, pages):
    page = sitting(context, pages)
    assert frame(page) == {"who": "", "foot": ""}
    paper_id = page.evaluate("() => MODEL.exam.fingerprint")
    page.evaluate("() => window.dispatchEvent(new Event('beforeprint'))")
    html = page.evaluate("() => readableCopy()")
    assert 'class="dm-print-twin' not in html and "--dm-print-who:" not in html
    assert f"Paper ID {paper_id} ·" not in html
    page.evaluate("() => window.dispatchEvent(new Event('afterprint'))")


def test_the_copies_of_the_boxes_are_made_for_the_printing_and_taken_away_after_it(context, pages):
    page = sitting(context, pages)
    write(page, "something")
    assert page.query_selector(".dm-print-twin") is None
    page.evaluate("() => window.dispatchEvent(new Event('beforeprint'))")
    assert page.query_selector_all(".dm-print-twin")
    assert page.text_content('[data-answer="q1a"] .dm-print-twin') == "something"
    assert frame(page)["who"] == f'"{HEADER}"'
    page.evaluate("() => window.dispatchEvent(new Event('afterprint'))")
    assert page.query_selector(".dm-print-twin") is None and frame(page) == {"who": "", "foot": ""}


def test_ctrl_p_on_the_paper_gets_the_same_frame_because_the_page_listens_for_the_browsers_own_event(context, pages):
    page = sitting(context, pages)
    assert frame(page)["who"] == ""
    page.evaluate("() => window.dispatchEvent(new Event('beforeprint'))")
    assert frame(page)["who"] == f'"{HEADER}"'
    assert frame(page)["foot"].startswith('"Paper ID ')


def test_the_print_button_shows_the_paper_while_the_window_is_open_and_brings_the_finish_sheet_back(context, pages):
    page = sitting(context, pages)
    page.evaluate("""() => {
        window.__during = null;
        window.print = () => {
            window.__during = { app: !document.getElementById('dm-app').hidden,
                                finish: !document.getElementById('dm-finish-screen').hidden };
            window.dispatchEvent(new Event('beforeprint'));
            window.dispatchEvent(new Event('afterprint'));
        };
    }""")
    page.click("#dm-finish")
    page.click("#dm-print")
    assert page.evaluate("() => window.__during") == {"app": True, "finish": False}
    assert page.is_visible("#dm-finish-screen") and page.is_hidden("#dm-app")


def test_the_students_text_size_does_not_change_what_is_printed(context, pages, tmp_path):
    page = sitting(context, pages)
    long_answers(page)
    normal = printed(page, tmp_path, "normal.pdf")
    page.evaluate("() => document.documentElement.style.setProperty('--dm-size', '32')")
    large = printed(page, tmp_path, "large.pdf")
    assert len(large) == len(normal)


def test_a_long_answer_runs_on_to_the_next_page_and_leaves_no_page_nearly_empty(context, pages, tmp_path):
    """A rule that never splits an answer sends a long one to a page of its own, after a page that holds
    only a heading: the rehearsal paper then takes nine pages instead of five."""
    page = sitting(context, pages)
    long_answers(page)
    doc = printed(page, tmp_path)
    assert len(doc) <= 6
    assert all(len(sheet.get_text()) > 600 for sheet in list(doc)[:-1]), [len(sheet.get_text()) for sheet in doc]


def test_the_screens_controls_are_not_printed(context, pages, tmp_path):
    page = sitting(context, pages)
    long_answers(page)
    text = "".join(sheet.get_text() for sheet in printed(page, tmp_path))
    for control in ("Finish…", "Save a copy", "Browser", "Hide time", "Take a break", "Reading settings"):
        assert control not in text, control
    assert re.search(r"Question 1: Writing", text)


def test_the_answer_key_prints_with_the_exam_code_and_the_paper_id(context, pages, tmp_path):
    from helpers import open_page
    page = open_page(context, pages["answer_key"])
    begin(page, choose=False)
    sheet = printed(page, tmp_path)[0]
    assert any(box.y1 <= TOP for box in sheet.search_for("rehearsal")), "no exam code in the top margin"
    assert "Paper ID" in sheet.get_text()
    assert page.errors == []
