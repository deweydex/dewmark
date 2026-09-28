"""Shared set-up for the browser rehearsals.

These tests open built exam pages and the marking workbench in a real
Chromium, because the bugs they guard against live in the page, not the
builder: what gets written to browser storage, and when. They need the
playwright package and a Chromium. Where either is missing they are
skipped, unless DEWMARK_REQUIRE_BROWSER is set, as it is in CI, where a
skipped rehearsal would read as a passed one.
"""

import glob
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
import build_exam  # noqa: E402

SAMPLE = ROOT / "samples" / "sample-mixed-paper.exam.md"


def _unavailable(reason):
    if os.environ.get("DEWMARK_REQUIRE_BROWSER"):
        pytest.fail(reason)
    pytest.skip(reason)


def find_chromium():
    """A Chromium to launch: DEWMARK_CHROMIUM if set, else one under
    PLAYWRIGHT_BROWSERS_PATH or /opt/pw-browsers, else None so Playwright
    uses its own download."""
    if os.environ.get("DEWMARK_CHROMIUM"):
        return os.environ["DEWMARK_CHROMIUM"]
    for root in (os.environ.get("PLAYWRIGHT_BROWSERS_PATH"), "/opt/pw-browsers"):
        if root:
            for candidate in sorted(glob.glob(root + "/chromium-*/chrome-linux*/chrome")):
                return candidate
    return None


@pytest.fixture(scope="session")
def browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        _unavailable("playwright is not installed")
    with sync_playwright() as playwright:
        try:
            launched = playwright.chromium.launch()
        except Exception:
            chromium = find_chromium()
            if not chromium:
                _unavailable("no Chromium to launch")
            launched = playwright.chromium.launch(executable_path=chromium)
        yield launched
        launched.close()


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    """The mixed sample built once: its three pages and its scheme."""
    out = tmp_path_factory.mktemp("built")
    build_exam.build(SAMPLE, out)
    return {
        "student": out / "sample-mixed-2027.student.html",
        "practice": out / "sample-mixed-2027.practice.html",
        "answer_key": out / "sample-mixed-2027.answer-key.html",
        "scheme": out / "dewmark_sample-mixed-2027_marking_scheme.json",
        "dir": out,
    }


@pytest.fixture
def context(browser):
    """A fresh browser profile: its own storage, shared by every page
    opened in it, as the pages of one college PC's browser are."""
    ctx = browser.new_context(accept_downloads=True)
    yield ctx
    ctx.close()
