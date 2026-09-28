"""Builder messages (docs/EXAM_FORMAT.md §7).

Every message says where (a line, and the part it concerns), what is
wrong, and what to do, and carries a stable code a help page can be
keyed on. A problem stops a paper being issued; a warning does not.
"""

from dataclasses import asdict, dataclass


@dataclass
class Message:
    code: str
    line: int
    what: str
    fix: str = ""
    where: str = ""
    level: str = "problem"   # "problem" or "warning"

    def as_dict(self):
        return asdict(self)

    def __str__(self):
        head = f"Line {self.line}" + (f" · {self.where}" if self.where else "")
        text = f"{head} · {self.what}"
        if self.fix:
            text += f"\n    {self.fix}"
        if self.level == "warning":
            text = "(warning) " + text
        return text + f"  [{self.code}]"


class Messages(list):
    """The messages from one reading, in the order they were found."""

    def problem(self, code, line, what, fix="", where=""):
        self.append(Message(code, line, what, fix, where, "problem"))

    def warning(self, code, line, what, fix="", where=""):
        self.append(Message(code, line, what, fix, where, "warning"))

    @property
    def problems(self):
        return [m for m in self if m.level == "problem"]

    @property
    def warnings(self):
        return [m for m in self if m.level == "warning"]

    def codes(self):
        return [m.code for m in self]
