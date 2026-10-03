"""The invigilator's code: a short number that lets the person running a sitting
do what a student must not do alone (planning/DECISIONS_2026-09-27.md, D4;
`DECISIONS_LOG.md` entry 0.17).

The code does four things on the student's page. It adds time to a paper whose
timer is enforced, and so reopens one that has closed. It lets a student start
a paper again under an enforced timer. It lets a student continue work saved
under a different name. It opens the list of work saved on the computer.

**It is made when the pages are built, for one sitting**, by
`python -m dewmark build FILE -o DIR --sitting "2026-10-20 Group A"`, which
prints it for the sitting card, or taken from `--code`. It is never a setting of
the exam file, so the paste route never hands it to an assistant, a new sitting
has a new code, and a file in the folder students receive never holds it. The
page holds only a short hash of it, made with the paper's code, so the code is
not in the page's text.

**It guards against accidents and casual attempts, not against a student with
developer tools.** A hash of a number with six digits can be searched in
seconds by a program, and a student who can read the page can change what it
checks. The invigilator, in the room, is the real remedy (as at a paper exam),
and the answer file records every grant of time so that the invigilator and the
marker can see it. The page asks for the code slowly after three wrong tries,
which stops a student pressing keys, not a student with a script.

Standard library only, so the page's JavaScript and this module can be tested
against each other (`tests/browser/test_time.py`).
"""

import hashlib
import re
import secrets

SALT = "dewmark-invigilator/1"
LENGTH = (4, 8)                        # digits a code may have when it is given, not made


def normalise(text):
    """The digits of what was typed: spaces, hyphens and the like do not count."""
    return re.sub(r"\D", "", str(text))


def issue():
    """A new code: six digits, from the system's secure source."""
    return f"{secrets.randbelow(10 ** 6):06d}"


def valid(text):
    """Whether `text` can be a code given by the teacher: 4 to 8 digits."""
    digits = normalise(text)
    return LENGTH[0] <= len(digits) <= LENGTH[1] and re.fullmatch(r"[\d \-]+", str(text).strip()) is not None


def pretty(code):
    """The code as it is written on a card: `482 915`."""
    digits = normalise(code)
    return " ".join(digits[i:i + 3] for i in range(0, len(digits), 3))


def check(exam_code, code):
    """What the page keeps instead of the code: 16 hexadecimal digits, made from
    the paper's code and the digits of the invigilator's."""
    return hashlib.sha256(f"{SALT}:{exam_code}:{normalise(code)}".encode("utf-8")).hexdigest()[:16]
