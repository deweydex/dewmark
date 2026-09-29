"""Printed numbers, and the permanent names made from them
(docs/EXAM_FORMAT.md §4.2, §4.4).

A number is what is printed beside a question, part or box: "Question 3",
"3(a)", "1A (i)", "B2(c)(ii)". It is read into four pieces (section
letter, question, part letter, sub-part numeral), and an answer's
permanent name is built from them: q, the question and part, then "." and
the sub-part, then "." and the caption. Names are the key a student's saved
answers and the marker's record are stored under, so this module decides
the contract; change it and every stored answer moves.
"""

import re
import unicodedata

NUMBER_RE = re.compile(r"""
    ^\s*(?:(?:question|q)\.?\s*)?
    (?:(?P<sec>[A-Za-z])(?=\d))?
    (?P<q>\d+)?
    [\s.]*
    (?:\(?(?P<part>[a-hA-H])\)?(?![A-Za-z]))?
    \s*
    (?:\((?P<sub>[ivxIVX]+)\))?
    \s*""", re.X | re.I)

# A title follows a number after ":", an en or em dash, or " - ".
TITLE_SPLIT_RE = re.compile(r"\s*(?::|—|–|\s-\s)\s*")


def slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def read_number(text, question=None, part=None):
    """Read a printed number from the start of `text`.

    `question` is the (section, number) of the question being read and
    `part` its current part letter, so that "(a)" under Question 3 and
    "(i)" under 3(a) resolve. Returns ((sec, q, part, sub), rest of text),
    or (None, text) when the text does not start with a number.
    """
    m = NUMBER_RE.match(text)
    if not m or not (m.group("q") or m.group("part") or m.group("sub")):
        return None, text
    sec = (m.group("sec") or "").lower()
    q = m.group("q") or ""
    letter = (m.group("part") or "").lower()
    sub = (m.group("sub") or "").lower()
    if not q:
        if question is None:
            return None, text
        sec, q = question
        if not letter and part:
            letter = part
    return (sec, q, letter, sub), text[m.end():]


def split_title(text):
    """Split "1(a): Parts of a function" into its number text and title."""
    pieces = TITLE_SPLIT_RE.split(text, maxsplit=1)
    return pieces[0], (pieces[1] if len(pieces) > 1 else "")


def name_of(number, caption=""):
    sec, q, part, sub = number
    name = "q" + sec + q + part
    if sub:
        name += "." + sub
    if caption and slug(caption):
        name += "." + slug(caption)
    return name


def label_of(number):
    """The number written the one way dewmark shows it: 3(a)(ii)."""
    sec, q, part, sub = number
    label = sec.upper() + q
    if part:
        label += f"({part})"
    if sub:
        label += f"({sub})"
    return label
