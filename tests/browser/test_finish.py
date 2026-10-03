"""Rehearsals for the finish sheet: check the answers, save the answer file and the
PDF, hand them in.

The sheet's one button writes both files into the folder the student chose, reads
them back, and says what it found, so that a student never hands in a file that was
not written. In a browser that cannot write into a folder it downloads both and says
plainly that it cannot look inside them. The folder is a stand-in kept in memory
(tests/browser/helpers.py, FAKE_PICKER), which can be made to refuse a write or to
give back the wrong bytes.
"""

import json
import re

import pytest

from conftest import _unavailable
from helpers import (EVERYTHING, FAKE_PICKER, NO_PICKER, answer_file, begin, downloads_of_both,
                     fill_everything, folder_bytes, folder_names, open_page, pdf_file, save_both,
                     stored, wait_for, write)

from dewmark.receipt import receipt

try:
    import pymupdf
except ImportError:                                           # pragma: no cover
    pymupdf = None


def sitting(context, pages, variant="student", picker=FAKE_PICKER, name="Agnes Nitt", number="S12345"):
    page = open_page(context, pages[variant], picker=picker)
    begin(page, name=name, number=number)
    return page


def pdf_text(data):
    if pymupdf is None:
        _unavailable("PyMuPDF is not installed, so a PDF cannot be read back")
    return "\n".join(page.get_text() for page in pymupdf.open(stream=data, filetype="pdf"))


# --- the three steps ---------------------------------------------------------------------------------------------

def test_the_finish_sheet_has_the_three_steps_in_order_with_the_papers_own_hand_in_words(context, pages):
    page = sitting(context, pages)
    write(page, "x")
    page.click("#dm-finish")
    assert page.evaluate("document.activeElement.id") == "dm-finish-h"
    steps = [h.strip() for h in page.eval_on_selector_all("#dm-finish-screen .dm-finish-steps h3", "(e) => e.map((x) => x.textContent)")]
    assert steps == ["1. Check your answers", "2. Save your answer file and your PDF", "3. Hand it in"]
    assert "Hand it in." in page.text_content(".dm-finish-steps li:nth-child(3)")
    assert page.is_visible("#dm-submit") and page.text_content("#dm-submit") == "Save my answer file and PDF"
    for hidden in ("#dm-saved", "#dm-problem", "#dm-confirm", "#dm-pdf-note", "#dm-again-row", "#dm-rechoose"):
        assert page.is_hidden(hidden), hidden


# --- a folder ----------------------------------------------------------------------------------------------------

def test_one_press_puts_both_files_in_the_folder_reads_them_back_and_says_what_it_found(context, pages):
    page = sitting(context, pages)
    fill_everything(page)
    save_both(page)
    names = sorted(folder_names(page))
    assert names == ["dewmark_rehearsal_s12345_agnes-nitt.json", "dewmark_rehearsal_s12345_agnes-nitt.pdf"]
    record = answer_file(page)
    assert record["receipt"] == receipt(record) and record["finished_at"]
    assert pdf_file(page).startswith(b"%PDF-1.4") and pdf_file(page).rstrip().endswith(b"%%EOF")
    assert page.text_content("#dm-saved") == (
        f"Checked: the file holds 9 answers. Receipt {record['receipt']}. The PDF has 2 pages. "
        "Both are in the folder answers-folder.")
    assert page.is_hidden("#dm-problem") and page.is_hidden("#dm-again-row")
    assert page.text_content("#dm-pdf-note") == "" or page.is_hidden("#dm-pdf-note")


def test_the_answer_file_in_the_folder_is_the_one_the_page_has_been_saving_into(context, pages):
    page = sitting(context, pages)
    write(page, "x")
    wait_for(page, "Object.values(window.__folder).some((d) => d.length > 0)")
    save_both(page)
    assert len(folder_names(page)) == 2, "no third file: the answer file is written over, not added to"


def test_the_pdf_in_the_folder_is_the_pdf_of_the_files_receipt(context, pages):
    page = sitting(context, pages)
    fill_everything(page)
    save_both(page)
    record = answer_file(page)
    assert f"Receipt {record['receipt']}" in pdf_text(pdf_file(page))


def test_the_confirmation_card_has_what_an_invigilator_checks(context, pages):
    page = sitting(context, pages, name="Síle Ní Bhriain", number="D00123456")
    fill_everything(page)
    save_both(page)
    record = answer_file(page)
    card = {key: page.text_content(f"#dm-c-{key}") for key in
            ("name", "number", "paper", "id", "answers", "saved", "receipt", "files")}
    assert card["name"] == "Síle Ní Bhriain" and card["number"] == "D00123456"
    assert card["paper"] == "Rehearsal Paper (rehearsal, version 1)"
    assert card["id"] == record["exam"]["fingerprint"] and card["receipt"] == record["receipt"]
    assert card["answers"] == "9 answers" and re.search(r"\d{4}", card["saved"])
    assert card["files"] == "dewmark_rehearsal_d00123456_sile-ni-bhriain.json, dewmark_rehearsal_d00123456_sile-ni-bhriain.pdf"
    assert page.is_visible("#dm-confirm") and "invigilator" in page.text_content("#dm-confirm-h")


def test_an_empty_paper_can_be_saved_and_checked(context, pages):
    page = sitting(context, pages)
    save_both(page)
    assert "Checked: the file holds 0 answers." in page.text_content("#dm-saved")
    assert answer_file(page)["answers"] == {}


def test_a_file_that_comes_back_different_is_refused_and_nothing_is_called_saved(context, pages):
    page = sitting(context, pages)
    fill_everything(page)
    page.evaluate("() => { window.__folderFails = 'altered'; }")
    save_both(page)
    problem = page.text_content("#dm-problem")
    assert "in your folder is not the one the page saved" in problem and ".pdf" in problem
    assert "Your answers are safe in this browser" in problem and "Save a copy" in problem
    assert page.is_hidden("#dm-saved") and page.is_hidden("#dm-confirm") and page.is_visible("#dm-rechoose")
    assert stored(page)["dewmark:rehearsal:student"]["answers"] == EVERYTHING


def test_a_folder_that_refuses_the_write_is_explained_and_choosing_again_saves(context, pages):
    page = sitting(context, pages)
    fill_everything(page)
    page.evaluate("() => { window.__folderFails = 'write'; }")
    save_both(page)
    assert "could not write into your folder (NotAllowedError)" in page.text_content("#dm-problem")
    assert page.is_hidden("#dm-confirm") and page.is_visible("#dm-rechoose")
    page.evaluate("() => { window.__folderFails = null; }")
    page.click("#dm-rechoose")
    page.wait_for_selector("#dm-saved:not([hidden])")
    assert page.is_hidden("#dm-problem") and page.is_hidden("#dm-rechoose") and page.is_visible("#dm-confirm")
    assert "Checked: the file holds 9 answers" in page.text_content("#dm-saved")
    assert len(folder_names(page)) == 2


def test_the_button_cannot_start_a_second_save_while_the_first_is_running(context, pages):
    page = sitting(context, pages)
    fill_everything(page)
    page.click("#dm-finish")
    page.evaluate("() => { const b = document.getElementById('dm-submit'); b.click(); b.click(); }")
    page.wait_for_selector("#dm-saved:not([hidden])")
    assert not page.errors and len(folder_names(page)) == 2
    assert page.is_enabled("#dm-submit")


def test_a_change_after_saving_takes_the_check_the_card_and_the_receipt_away(context, pages):
    page = sitting(context, pages)
    write(page, "first")
    save_both(page)
    assert page.is_visible("#dm-confirm") and page.is_visible("#dm-saved")
    page.click("#dm-keep-working")
    write(page, "second")
    page.click("#dm-finish")
    for gone in ("#dm-saved", "#dm-confirm", "#dm-pdf-note", "#dm-problem"):
        assert page.is_hidden(gone), gone
    assert page.is_visible("#dm-changed")
    page.click("#dm-submit")
    page.wait_for_selector("#dm-saved:not([hidden])")
    assert page.is_hidden("#dm-changed") and answer_file(page)["answers"] == {"q1a": "second"}


# --- no folder ----------------------------------------------------------------------------------------------------

def test_a_browser_with_no_folder_downloads_both_files_and_says_it_cannot_look_inside(context, pages, tmp_path):
    page = sitting(context, pages, picker=NO_PICKER)
    fill_everything(page)
    files = downloads_of_both(page, tmp_path)
    assert files["json"].name == "dewmark_rehearsal_s12345_agnes-nitt.json"
    assert files["pdf"].name == "dewmark_rehearsal_s12345_agnes-nitt.pdf"
    record = json.loads(files["json"].read_text())
    assert record["receipt"] == receipt(record) and record["answers"] == EVERYTHING
    assert f"Receipt {record['receipt']}" in pdf_text(files["pdf"].read_bytes())
    saved = page.text_content("#dm-saved")
    assert saved.startswith("Saved. Your browser put two files in its downloads folder: ")
    assert "A page cannot look inside a file it downloaded, so open them to check." in saved
    assert "Checked" not in saved
    assert page.is_visible("#dm-again-row") and page.is_visible("#dm-confirm")


def test_a_file_the_browser_held_back_can_be_saved_again_with_the_same_receipt(context, pages, tmp_path):
    page = sitting(context, pages, picker=NO_PICKER)
    fill_everything(page)
    first = downloads_of_both(page, tmp_path)
    receipt_before = json.loads(first["json"].read_text())["receipt"]
    with page.expect_download() as caught:
        page.click("#dm-again-file")
    again = tmp_path / ("again-" + caught.value.suggested_filename)
    caught.value.save_as(again)
    assert json.loads(again.read_text())["receipt"] == receipt_before
    with page.expect_download() as caught:
        page.click("#dm-again-pdf")
    pdf = tmp_path / ("again-" + caught.value.suggested_filename)
    caught.value.save_as(pdf)
    assert f"Receipt {receipt_before}" in pdf_text(pdf.read_bytes())


def test_the_answer_key_saves_nothing_to_a_folder_whatever_the_browser_allows(context, pages, tmp_path):
    page = sitting(context, pages, variant="answer_key")
    write(page, "x")
    files = downloads_of_both(page, tmp_path)
    assert set(files) == {"json", "pdf"} and folder_names(page) == []
    assert "Saved. Your browser put two files" in page.text_content("#dm-saved")


@pytest.mark.parametrize("name, number, expected", [
    ("Síle Ní Bhriain", "D00123456", "dewmark_rehearsal_d00123456_sile-ni-bhriain"),
    ("Seán Ó Dónaill", "S1", "dewmark_rehearsal_s1_sean-o-donaill"),
    ("Zażółć Łukasz", "X 9", "dewmark_rehearsal_x-9_zazolc-lukasz"),
    ("Søren Ærø Đặng", "D1", "dewmark_rehearsal_d1_soren-aero-dang"),
    ("Привіт", "U7", "dewmark_rehearsal_u7_student"),
    ("  O'Brien-Smith  ", "../x", "dewmark_rehearsal_x_o-brien-smith"),
])
def test_file_names_lose_accents_and_anything_that_is_not_safe_in_a_file_name(context, pages, name, number, expected):
    page = sitting(context, pages, name=name, number=number)
    write(page, "x")
    wait_for(page, "Object.values(window.__folder).some((d) => d.length > 0)")
    assert folder_names(page) == [expected + ".json"]
