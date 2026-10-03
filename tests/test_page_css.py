"""The colour schemes of the page (assets/page.css) meet the accessibility
promises in planning/APPEARANCE_AND_READABILITY.md §5: text and its
background reach WCAG AA contrast (4.5 to 1) in every scheme, and the edges of
form controls and the keyboard focus ring reach 3 to 1, because a student must
be able to see where to type. The pairs listed here are the pairs the
stylesheet really puts together; a new pair goes in this list in the same
commit as the rule that uses it.
"""

import re
from pathlib import Path

import pytest

RAW = (Path(__file__).resolve().parent.parent / "assets" / "page.css").read_text(encoding="utf-8")
CSS = re.sub(r"/\*.*?\*/", "", RAW, flags=re.S)

TEXT = [
    ("ink", "bg"), ("ink", "surface"), ("ink", "box-bg"), ("ink", "tint"),
    ("ink", "good-bg"), ("ink", "warn-bg"),
    ("muted", "bg"), ("muted", "surface"), ("muted", "box-bg"), ("muted", "tint"),
    ("accent", "bg"), ("accent", "surface"), ("accent", "tint"), ("accent", "box-bg"),
    ("band-ink", "band-bg"), ("band-kind", "band-bg"),
    ("primary-ink", "primary-bg"), ("orange-ink", "orange"),
    ("good", "good-bg"), ("good", "surface"), ("good", "bg"),
    ("warn", "warn-bg"), ("warn", "surface"), ("warn", "bg"),
    ("bad", "surface"), ("bad", "bg"), ("bad", "bad-bg"),
    ("code-ink", "code-bg"),
]
EDGES = [("field-border", "surface"), ("field-border", "bg"), ("focus", "bg"), ("focus", "surface")]


def blocks(css):
    """{selector: {variable: value}} for each rule that sets --dm- variables;
    a rule inside @media (prefers-color-scheme: dark) is named 'dark-auto'."""
    out, depth, stack, start = {}, 0, [], 0
    for index, char in enumerate(css):
        if char == "{":
            stack.append(css[start:index].strip())
            start = index + 1
        elif char == "}":
            body = css[start:index]
            selector = stack.pop()
            variables = dict(re.findall(r"--dm-([a-z-]+):\s*(#[0-9a-fA-F]{6})", body))
            if variables and not selector.startswith("@"):
                name = "dark-auto" if any("prefers-color-scheme: dark" in s for s in stack) else selector
                out[name] = {**out.get(name, {}), **variables}
            start = index + 1
    return out


SCHEMES = blocks(CSS)
LIGHT = SCHEMES[":root, [data-scheme=\"light\"]"]


def luminance(colour):
    channels = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def test_the_stylesheet_has_every_scheme_the_settings_offer():
    found = set(SCHEMES)
    assert {'[data-scheme="cream"]', '[data-scheme="blue"]', '[data-scheme="dark"]',
            '[data-scheme="contrast"]', "dark-auto"} <= found


def test_every_scheme_sets_every_colour_the_light_one_does():
    """A colour a scheme forgets would fall back to the light scheme's, on a dark page."""
    for name in ('[data-scheme="cream"]', '[data-scheme="blue"]', '[data-scheme="dark"]',
                 '[data-scheme="contrast"]', "dark-auto"):
        assert set(SCHEMES[name]) >= set(LIGHT), (name, set(LIGHT) - set(SCHEMES[name]))


@pytest.mark.parametrize("name", [':root, [data-scheme="light"]', '[data-scheme="cream"]',
                                  '[data-scheme="blue"]', '[data-scheme="dark"]',
                                  '[data-scheme="contrast"]', "dark-auto"])
def test_text_and_its_background_reach_aa_in_every_scheme(name):
    scheme = {**LIGHT, **SCHEMES[name]} if name != ':root, [data-scheme="light"]' else LIGHT
    for ink, ground in TEXT:
        ratio = contrast(scheme[ink], scheme[ground])
        assert ratio >= 4.5, f"{name}: {ink} on {ground} is {ratio:.2f} to 1"


@pytest.mark.parametrize("name", [':root, [data-scheme="light"]', '[data-scheme="cream"]',
                                  '[data-scheme="blue"]', '[data-scheme="dark"]',
                                  '[data-scheme="contrast"]', "dark-auto"])
def test_the_edge_of_a_field_and_the_focus_ring_reach_three_to_one(name):
    scheme = {**LIGHT, **SCHEMES[name]} if name != ':root, [data-scheme="light"]' else LIGHT
    for edge, ground in EDGES:
        ratio = contrast(scheme[edge], scheme[ground])
        assert ratio >= 3, f"{name}: {edge} on {ground} is {ratio:.2f} to 1"


def test_the_practice_label_on_the_band_reaches_aa_where_it_is_not_overridden():
    for name, scheme in SCHEMES.items():
        if "band-bg" in scheme and name != '[data-scheme="contrast"]':
            assert contrast("#ffd9b8", scheme["band-bg"]) >= 4.5, name


@pytest.mark.parametrize("code", ["#ffffff/#1a1a1a", "#1b2030/#e8e6e1"])
def test_the_light_and_dark_code_choices_reach_aa(code):
    ground, ink = code.split("/")
    assert contrast(ink, ground) >= 4.5
    for token in code.split("/"):
        assert token in CSS
