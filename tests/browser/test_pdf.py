"""Rehearsals for the PDF the page writes (assets/page-pdf.js).

A PDF is checked as the people who open it will meet it: by a real PDF reader
(PyMuPDF, which is MuPDF, the same reader that Moodle's PDF tools and many
phones use), not by looking at the bytes the writer meant to write. Each test
sits a paper in Chromium, has the page write its PDF, and reads the file back:
its text, where the text sits on each page, which fonts it carries, and whether
the reader had to repair it. A reader that has to repair a file is a reader
that may show a marker something else.
"""

import json
import os
import re
import shutil
import subprocess
import time

import pytest

from conftest import REHEARSAL_PAPER, ROOT, _unavailable
from helpers import (EVERYTHING, FAKE_PICKER, begin, fill_everything, finish_and_download,
                     open_page, stored, type_details, wait_for, write)

from dewmark.build import build_pages
from dewmark.receipt import receipt

try:
    import pymupdf
except ImportError:                                           # pragma: no cover
    pymupdf = None


@pytest.fixture(autouse=True)
def reader():
    if pymupdf is None:
        _unavailable("PyMuPDF is not installed, so a PDF cannot be read back")


MAKE = """async () => {
    fixReceipt();
    const r = await makePdf();
    return { bytes: Array.from(r.bytes), missing: r.missing, pages: r.pages };
}"""


def make_pdf(page):
    """Have the page write its PDF now; returns (bytes, characters it could not draw)."""
    result = page.evaluate(MAKE)
    return bytes(result["bytes"]), result["missing"]


def opened(data):
    pymupdf.TOOLS.mupdf_warnings()                            # clear what came before
    doc = pymupdf.open(stream=data, filetype="pdf")
    return doc


def text_of(doc):
    return "\n".join(page.get_text() for page in doc)


def sitting(context, pages, name="Agnes Nitt", number="S12345", variant="student"):
    page = open_page(context, pages[variant])
    begin(page, name=name, number=number)
    return page


# --- a PDF is a PDF -----------------------------------------------------------------------------------------------

def check_classic_structure(data):
    """The file's own table says where every object is, and it is right. Moodle's
    PDF import reads only this plain kind of file, with no object streams."""
    assert data.startswith(b"%PDF-1.4\n")
    assert b"/ObjStm" not in data and b"/Type /XRef" not in data
    start = int(re.search(rb"startxref\n(\d+)\n%%EOF\n$", data).group(1))
    assert data[start:start + 4] == b"xref"
    header = re.match(rb"xref\n0 (\d+)\n", data[start:])
    count = int(header.group(1))
    table = data[start + header.end():start + header.end() + 20 * count]
    entries = [table[i:i + 20] for i in range(0, len(table), 20)]
    assert entries[0] == b"0000000000 65535 f \n"
    for number, entry in enumerate(entries[1:], start=1):
        assert re.fullmatch(rb"\d{10} 00000 n \n", entry), entry
        offset = int(entry[:10])
        assert data[offset:offset + len(f"{number} 0 obj\n")] == f"{number} 0 obj\n".encode(), number
    assert f"/Size {count}".encode() in data


def test_the_file_is_plain_pdf_with_a_right_table_and_the_reader_needs_no_repair(context, pages):
    page = sitting(context, pages)
    fill_everything(page)
    data, _ = make_pdf(page)
    check_classic_structure(data)
    doc = opened(data)
    assert doc.is_pdf and not doc.is_repaired and doc.page_count >= 1
    assert pymupdf.TOOLS.mupdf_warnings() == ""
    assert doc.metadata["producer"] == "dewmark page writer 1" and doc.metadata["creator"] == "dewmark"
    assert "Agnes Nitt (S12345)" in doc.metadata["title"] and doc.metadata["author"] == "Agnes Nitt"
    assert doc.metadata["creationDate"].startswith("D:20")


def test_every_font_is_carried_in_the_file_and_only_the_fonts_that_were_used(context, pages):
    page = sitting(context, pages)
    write(page, "text only")
    data, _ = make_pdf(page)
    doc = opened(data)
    names = {font[3] for font in doc.get_page_fonts(0)}
    assert names == {"DMKPDF+DejaVuSans"}, "no code was written, so the code font is not carried"
    assert all(font[1] == "ttf" for font in doc.get_page_fonts(0))        # an embedded TrueType file
    page.fill('[data-answer="q2a"] textarea', "print(1)")
    page.wait_for_timeout(200)
    names = {font[3] for font in opened(make_pdf(page)[0]).get_page_fonts(0)}
    assert names == {"DMKPDF+DejaVuSans", "DMKPDF+DejaVuSansMono"}


def test_a_small_paper_gives_a_small_file(context, pages):
    page = sitting(context, pages)
    fill_everything(page)
    data, _ = make_pdf(page)
    assert len(data) < 160_000, len(data)


def test_the_same_answers_give_the_same_file(context, pages):
    page = sitting(context, pages)
    fill_everything(page)
    first, _ = make_pdf(page)
    second, _ = make_pdf(page)
    assert first == second


def tool(name):
    """A command-line PDF tool, or a skip: CI installs them and sets DEWMARK_REQUIRE_BROWSER."""
    found = shutil.which(name)
    if not found:
        _unavailable(f"{name} is not installed")
    return found


def test_qpdf_finds_nothing_wrong_with_the_file(context, pages, tmp_path):
    page = sitting(context, pages)
    fill_everything(page)
    page.fill('[data-answer="q1a"] textarea', IRISH + " " + GREEK_CYRILLIC + " " + MATHS)
    (tmp_path / "answers.pdf").write_bytes(make_pdf(page)[0])
    run = subprocess.run([tool("qpdf"), "--check", str(tmp_path / "answers.pdf")],
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    assert "No syntax or stream encoding errors found" in run.stdout


def test_ghostscript_draws_every_page_and_can_write_the_file_again(context, pages, tmp_path):
    """Moodle's grader turns each page into a picture with Ghostscript to mark on it."""
    page = sitting(context, pages)
    page.fill('[data-answer="q1a"] textarea', "\n".join(f"line {n}" for n in range(120)))
    fill = EVERYTHING["q1b"]
    page.fill('[data-answer="q1b"] textarea', fill)
    page.wait_for_timeout(200)
    data, _ = make_pdf(page)
    source = tmp_path / "answers.pdf"
    source.write_bytes(data)
    count = opened(data).page_count
    gs = tool("gs")
    drawn = subprocess.run([gs, "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER", "-sDEVICE=png16m", "-r50",
                            f"-sOutputFile={tmp_path}/page%d.png", str(source)], capture_output=True, text=True)
    assert drawn.returncode == 0 and drawn.stderr.strip() == "", drawn.stderr
    assert len(list(tmp_path.glob("page*.png"))) == count
    again = subprocess.run([gs, "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER", "-sDEVICE=pdfwrite",
                            f"-sOutputFile={tmp_path}/again.pdf", str(source)], capture_output=True, text=True)
    assert again.returncode == 0 and again.stderr.strip() == ""
    assert opened((tmp_path / "again.pdf").read_bytes()).page_count == count


# --- what is in it ---------------------------------------------------------------------------------------------

def test_the_pdf_has_the_candidate_the_codes_and_every_part_in_order(context, pages):
    page = sitting(context, pages, name="Síle Ní Bhriain", number="D00123456")
    fill_everything(page)
    data, missing = make_pdf(page)
    text = text_of(opened(data))
    assert missing == []
    order = ["Rehearsal Paper", "Candidate", "Síle Ní Bhriain, student number D00123456",
             "Question 1: Writing (6 marks)", "1(a) (2 marks)", "alpha", "1(b) (2 marks)", "x = 2",
             "1(c) (2 marks)", "one two three", "Question 2: Code (4 marks)", "2(a) (2 marks)", "print(1)",
             "2(b) (2 marks)", "print(2)", "Question 3: Filling in (8 marks)", "3(a) (2 marks)",
             "A. one", "C. three", "3(b) (2 marks)", "First: [root]", "Second: [stem]",
             "3(c) (2 marks)", "A [plant] has [leaves].", "3(d) (2 marks)", "small   |   [3]", "large   |   [4]"]
    at = 0
    for part in order:
        found = text.find(part, at)
        assert found >= 0, f"{part!r} is missing or out of order"
        at = found
    assert "B. two" not in text, "only the chosen options are written"
    assert "9 of 9 parts have an answer" in text and "Student paper" in text


def test_a_part_with_nothing_in_it_says_not_attempted_and_rough_work_is_labelled(context, pages):
    page = sitting(context, pages)
    write(page, "only this")
    text = text_of(opened(make_pdf(page)[0]))
    assert text.count("(not attempted)") == 8 and "only this" in text
    assert "1 of 9 parts have an answer" in text


def test_the_essay_says_how_many_words_it_has(context, pages):
    page = sitting(context, pages)
    page.fill('[data-answer="q1c"] textarea', "one two three four")
    page.wait_for_timeout(200)
    text = text_of(opened(make_pdf(page)[0]))
    assert "About 50 words" in text and "4 words" in text


def test_the_codes_are_the_ones_in_the_answer_file_the_same_finish_gives(context, pages, tmp_path):
    page = sitting(context, pages)
    fill_everything(page)
    page.click("#dm-finish")
    with page.expect_download() as caught:
        page.click("#dm-save-pdf")
    pdf = tmp_path / caught.value.suggested_filename
    caught.value.save_as(pdf)
    assert re.fullmatch(r"dewmark_rehearsal_s12345_agnes-nitt\.pdf", pdf.name)
    with page.expect_download() as caught:
        page.click("#dm-submit")
    answer_file = tmp_path / caught.value.suggested_filename
    caught.value.save_as(answer_file)
    record = json.loads(answer_file.read_text())
    text = text_of(pymupdf.open(pdf))
    assert f"Receipt {record['receipt']}" in text and f"Paper ID {record['exam']['fingerprint']}" in text
    assert record["receipt"] == receipt(record), "one finish sheet, one receipt, in the PDF and in the file"
    assert "Finished" in text and record["finished_at"][:16].replace("T", " ") in text
    assert "UTC" in text
    assert "9 answers" in page.text_content("#dm-saved") and "saved" in page.text_content("#dm-pdf-note")


def test_the_practice_pdf_says_it_is_the_practice_version(context, pages):
    page = sitting(context, pages, variant="practice")
    write(page, "x")
    text = text_of(opened(make_pdf(page)[0]))
    assert "Practice version" in text and "Student paper" not in text


# --- characters ------------------------------------------------------------------------------------------------

IRISH = "Síle Ní Bhriain, Seán Ó Dónaill, Máire Nic Uidhir, Éamon de Búrca, Ú Á É Í Ó"
EUROPE = "Zażółć gęślą jaźń, ţară, șțăîâ, Žluťoučký kůň, Ærø, ß, ð þ, Đặng Thị, ħ ŋ"
GREEK_CYRILLIC = "αβγδ ΩΣΠ, Привіт, Україна, Ёж, ґ є ї"
MATHS = "x ≥ 5, y ≤ 3, z ≠ 0, ± × ÷ √ ∑ ∫ ∞ ≈ π ½ ¾ ² ³ → ← ⇒ ∈ ∀ ∃ € £ ° ✓ ✗"


@pytest.mark.parametrize("sample", [IRISH, EUROPE, GREEK_CYRILLIC, MATHS], ids=["irish", "europe", "greek-cyrillic", "maths"])
def test_the_characters_students_write_come_out_as_they_were_typed(context, pages, sample):
    page = sitting(context, pages, name="Zażółć Ó Dónaill")
    page.fill('[data-answer="q1a"] textarea', sample)
    page.wait_for_timeout(200)
    data, missing = make_pdf(page)
    assert missing == [], missing
    doc = opened(data)
    text = text_of(doc)
    for word in sample.split():
        assert word in text, f"{word!r} did not come out of the PDF"
    for index in range(doc.page_count):
        assert "Zażółć Ó Dónaill · S12345 · rehearsal" in doc[index].get_text()


def test_code_with_letters_the_code_font_lacks_is_drawn_from_the_other_font(context, pages):
    page = sitting(context, pages)
    page.fill('[data-answer="q2a"] textarea', 'message = "Привіт, π ≥ 3"  # héllo\nprint(message)')
    page.wait_for_timeout(200)
    data, missing = make_pdf(page)
    assert missing == []
    text = text_of(opened(data))
    assert 'message = "Привіт, π ≥ 3"  # héllo' in text.replace(" ", " ")


def test_a_character_no_font_here_has_is_named_to_the_student_and_a_box_stands_for_it(context, pages):
    page = sitting(context, pages)
    page.fill('[data-answer="q1a"] textarea', "hello مرحبا 你好 end")
    page.wait_for_timeout(200)
    page.click("#dm-finish")
    with page.expect_download():
        page.click("#dm-save-pdf")
    note = page.text_content("#dm-pdf-note")
    assert "could not show these characters" in note and "你" in note and "م" in note
    assert "Print or save as PDF" in note and "exactly as you typed it" in note
    data, missing = make_pdf(page)
    assert sorted(missing) == sorted(set("مرحبا你好"))
    text = text_of(opened(data))
    assert "hello ????? ?? end" in text, "a box is drawn, and what a reader copies from it is a ?"
    assert "م" not in text and "你" not in text
    assert page.is_visible("#dm-print")


def test_control_and_zero_width_characters_are_left_out_not_drawn(context, pages):
    page = sitting(context, pages)
    page.fill('[data-answer="q1a"] textarea', "a​b\u0007c‮d﻿e tab\there")
    page.wait_for_timeout(200)
    data, missing = make_pdf(page)
    assert missing == []
    assert "abcde tab    here" in text_of(opened(data)).replace(" ", " ")


# --- laying out ---------------------------------------------------------------------------------------------------

def words_of(doc):
    """(page, x0, y0, x1, y1, text) for every word."""
    return [(i, *w[:5]) for i, page in enumerate(doc) for w in page.get_text("words")]


def test_a_long_answer_runs_over_pages_and_every_page_has_its_header_footer_and_count(context, pages):
    page = sitting(context, pages)
    page.fill('[data-answer="q1a"] textarea', " ".join(f"word{n}" for n in range(6000)))
    page.fill('[data-answer="q1c"] textarea', "\n\n".join(f"Paragraph {n}. " + "lorem ipsum " * 40 for n in range(40)))
    page.wait_for_timeout(300)
    data, _ = make_pdf(page)
    doc = opened(data)
    assert doc.page_count >= 6
    codes = re.search(r"Receipt ([0-9A-F]{4} [0-9A-F]{4})", doc[0].get_text()).group(1)
    for index, pdf_page in enumerate(doc):
        text = pdf_page.get_text()
        assert "Agnes Nitt · S12345 · rehearsal" in text, index
        assert f"Page {index + 1} of {doc.page_count}" in text, index
        assert f"Paper ID" in text and f"Receipt {codes}" in text, index
    text = text_of(doc)
    assert "word0 " in text and "word5999" in text, "nothing is lost across the page breaks"
    assert "Paragraph 39." in text


def test_text_stays_inside_the_margins_and_between_the_header_and_the_footer(context, pages):
    page = sitting(context, pages)
    page.fill('[data-answer="q1a"] textarea', "x" * 400 + " " + " ".join(f"w{n}" for n in range(3000)))
    page.fill('[data-answer="q2a"] textarea', "\n".join("    " * (n % 6) + f"line_{n} = " + "a" * (n % 90) for n in range(120)))
    page.wait_for_timeout(300)
    doc = opened(make_pdf(page)[0])
    width, height = doc[0].rect.width, doc[0].rect.height
    for index, x0, y0, x1, y1, _ in words_of(doc):
        assert x0 >= 54 and x1 <= width - 54, (index, x0, x1)
        assert y1 <= height - 30, (index, y1)
        assert y0 >= 28, (index, y0)


def test_lines_of_text_do_not_run_into_each_other(context, pages):
    page = sitting(context, pages)
    page.fill('[data-answer="q1a"] textarea', "\n".join(f"line {n} of the answer" for n in range(150)))
    page.fill('[data-answer="q2a"] textarea', "\n".join(f"code_{n}()" for n in range(150)))
    page.wait_for_timeout(300)
    doc = opened(make_pdf(page)[0])
    for index, pdf_page in enumerate(doc):
        lines = sorted((line["bbox"] for block in pdf_page.get_text("dict")["blocks"] if block["type"] == 0
                        for line in block["lines"]), key=lambda b: (b[1], b[0]))
        for a, b in zip(lines, lines[1:]):
            overlap_x = min(a[2], b[2]) - max(a[0], b[0])
            if overlap_x > 2:
                assert b[1] >= a[1] + 4 or abs(b[1] - a[1]) < 1.5 and a[0] != b[0], (index, a, b)


def body_lines(pdf_page):
    """The lines between the header and the footer, top to bottom, with their text."""
    out = []
    for block in pdf_page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            x0, y0, x1, y1 = line["bbox"]
            if 62 < y0 and y1 < pdf_page.rect.height - 62:
                out.append((y0, "".join(span["text"] for span in line["spans"])))
    return [text for _, text in sorted(out)]


HEADING = re.compile(r"\(\d+ marks?\)$")


def test_a_heading_is_never_left_alone_at_the_foot_of_a_page_whatever_the_answer_above_it(context, pages):
    """The sweep puts the next heading at every height a page can have, so a
    heading that would fall at the very foot must be carried to the next page."""
    page = sitting(context, pages)
    page.fill('[data-answer="q1b"] textarea', "the answer to 1(b)")
    page.fill('[data-answer="q1c"] textarea', "the answer to 1(c)")
    moved = 0
    for lines in range(36, 62):
        page.fill('[data-answer="q1a"] textarea', "\n".join(f"line {n}" for n in range(lines)))
        doc = opened(make_pdf(page)[0])
        for index, pdf_page in enumerate(doc):
            rows = body_lines(pdf_page)
            assert rows and not HEADING.search(rows[-1]), (lines, index, rows[-3:])
            if index and HEADING.search(rows[0]):
                moved += 1
    assert moved >= 3, "the sweep never put a heading at the top of a page, so it proved nothing"


def test_an_empty_paper_still_makes_a_valid_pdf(context, pages):
    page = sitting(context, pages)
    data, missing = make_pdf(page)
    doc = opened(data)
    assert doc.page_count == 1 and missing == []
    check_classic_structure(data)
    assert text_of(doc).count("(not attempted)") == 9 and "0 of 9 parts have an answer" in text_of(doc)


def test_a_very_long_answer_is_written_in_a_reasonable_time(context, pages):
    page = sitting(context, pages)
    page.fill('[data-answer="q1a"] textarea', " ".join(f"word{n}" for n in range(30000)))
    page.wait_for_timeout(300)
    started = time.time()
    data, _ = make_pdf(page)
    assert time.time() - started < 20
    doc = opened(data)
    assert doc.page_count > 40 and not doc.is_repaired
    assert f"Page {doc.page_count} of {doc.page_count}" in doc[doc.page_count - 1].get_text()


# --- the page ---------------------------------------------------------------------------------------------------

def test_saving_a_pdf_does_not_change_the_answers_and_a_second_save_keeps_the_receipt(context, pages, tmp_path):
    page = sitting(context, pages)
    fill_everything(page)
    page.click("#dm-finish")
    with page.expect_download():
        page.click("#dm-save-pdf")
    first = stored(page)["dewmark:rehearsal:student"]
    assert first["answers"] == EVERYTHING and re.fullmatch(r"[0-9A-F]{4} [0-9A-F]{4}", first["receipt"])
    with page.expect_download():
        page.click("#dm-save-pdf")
    assert stored(page)["dewmark:rehearsal:student"]["receipt"] == first["receipt"]


def test_print_or_save_as_pdf_prints_the_paper_and_the_finish_sheet_comes_back(context, pages):
    page = sitting(context, pages)
    write(page, "x")
    page.evaluate("""() => { window.__printed = null;
        window.print = () => { window.__printed = { app: !document.getElementById('dm-app').hidden,
            finish: !document.getElementById('dm-finish-screen').hidden }; }; }""")
    page.click("#dm-finish")
    page.click("#dm-print")
    assert page.evaluate("window.__printed") == {"app": True, "finish": False}
    page.evaluate("window.dispatchEvent(new Event('afterprint'))")
    assert page.is_hidden("#dm-app") and page.is_visible("#dm-finish-screen")


def test_a_page_with_no_way_to_make_a_pdf_says_so_and_loses_nothing(context, pages):
    page = sitting(context, pages)
    write(page, "x")
    page.evaluate("() => { window.makePdf = async () => { throw new Error('no'); }; }")
    page.click("#dm-finish")
    page.click("#dm-save-pdf")
    page.wait_for_selector("#dm-pdf-note:not([hidden])")
    assert "could not be made on this computer" in page.text_content("#dm-pdf-note")
    assert "Your answers are safe" in page.text_content("#dm-pdf-note")
    assert stored(page)["dewmark:rehearsal:student"]["answers"] == {"q1a": "x"}


def test_the_pdf_makes_no_request_and_stays_inside_the_page(context, pages):
    reached = []
    page = context.new_page()
    page.on("requestfinished", lambda request: reached.append(request.url))
    page.add_init_script(FAKE_PICKER)
    page.goto(pages["student"].resolve().as_uri())
    begin(page)
    fill_everything(page)
    make_pdf(page)
    assert [u for u in reached if not u.startswith("file:")] == []
