"""Receipts and fingerprints: two short codes that let people and programs
check that a file is the file it should be (planning/PROPOSAL.md §5, the finish
sheet; docs/ANSWER_FILE.md).

**A fingerprint** identifies exactly one paper, as the students are given it:
`7KQ-4MD`. It is made from the part of the exam file above `# Marking scheme`
(the settings, the questions, the reference cards), without the hints, with
line endings and trailing spaces made the same, and from a checksum of every
picture the paper carries. It is never made from the marking scheme, so a
teacher who corrects a key does not change what students sat, and a page's
bytes do not depend on the scheme (the mutation test in `dewmark/secrecy.py`
holds the builder to that). A teacher who changes a word of a question, a
mark, or a picture, changes the fingerprint. The student page, the practice
page and the answer key of one paper share it; the answer file's `page` field
says which one a student sat.

**A receipt** identifies exactly one answer file as it was handed in:
`7F3A 92C1`. It is made from the whole record except `saved_at` (which changes
every time the page saves) and `receipt` itself. A change to a single answer, a
name or the finish time changes it. The page shows it when the student saves,
puts it in the file and in every page of the PDF, and the marking workbench will
show it again from the file it reads, which is how a file edited after it was
handed in is found. It detects accident and casual change. It is not a
signature: nothing in it is secret, so someone who can edit the file and run
this function can write a matching receipt.

Both are the start of a SHA-256 of a **canonical form** of their material, so
that the page (which is JavaScript) and this module (which is Python, and is
what the workbench runs) get the same code from the same data. The canonical
form is JSON with the keys of every object in sorted order, no spaces, and
every character outside the printable ASCII range written as `\\uXXXX` in
lower-case hexadecimal (a character above U+FFFF as two of them). That is what
Python's `json.dumps(..., sort_keys=True, separators=(",", ":"),
ensure_ascii=True)` writes. `assets/page.js` writes the same text, and
`tests/browser/test_page.py` checks the two agree on a record full of the
characters most likely to make them differ.

This module uses only the standard library, so the checker page and the
workbench can run it unchanged.
"""

import hashlib
import json

from .package import split_halves
from .secrecy import without_hints

# Crockford's alphabet for the fingerprint: digits and capitals without I, L,
# O and U, so a code read aloud or from paper is not mistaken for another.
ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# What a receipt leaves out: the time of the last save, which changes every
# few seconds while a student works, and the receipt itself.
NOT_IN_A_RECEIPT = ("saved_at", "receipt")


def canonical(value):
    """The text that is hashed: sorted keys, no spaces, ASCII only."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value):
    return hashlib.sha256(canonical(value).encode("ascii")).digest()


def receipt(record):
    """The receipt of an answer record, as `7F3A 92C1`."""
    material = {k: v for k, v in record.items() if k not in NOT_IN_A_RECEIPT}
    code = _digest(material).hex()[:8].upper()
    return f"{code[:4]} {code[4:]}"


def paper_text(text):
    """The paper as students are given it, in a form that does not change when
    an editor changes line endings or trailing spaces: the part above the
    marking scheme, without its hints."""
    head, _ = split_halves(text, reference=False)
    lines = [line.rstrip() for line in without_hints(head).split("\n")]
    return "\n".join(lines).strip("\n")


def fingerprint(text, pictures=()):
    """The fingerprint of an exam file, as `7KQ-4MD`. `pictures` is the
    pictures the paper carries as (path, SHA-256 in hexadecimal) pairs, in any
    order, so that changing a picture's file changes the paper."""
    bits = int.from_bytes(_digest({
        "paper": paper_text(text),
        "pictures": sorted([path, checksum] for path, checksum in pictures),
    })[:4], "big") >> 2                  # the first 30 bits: six letters of five
    letters = "".join(ALPHABET[(bits >> shift) & 31] for shift in range(25, -1, -5))
    return f"{letters[:3]}-{letters[3:]}"
