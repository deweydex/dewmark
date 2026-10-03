"""Files copied from dewlab are kept as they were copied (decision 31).

assets/vendor/SOURCE.json says where each file came from and what it held when
it was copied; a hand edit, or a file added without a record, fails here.
"""

import hashlib
import json
from pathlib import Path

VENDOR = Path(__file__).resolve().parent.parent / "assets" / "vendor"
RECORD = json.loads((VENDOR / "SOURCE.json").read_text(encoding="utf-8"))


def test_every_copied_file_is_as_it_was_copied():
    for name, held in RECORD["files"].items():
        data = (VENDOR / "fonts" / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == held["sha256"], f"{name} was edited by hand"
        assert len(data) == held["bytes"]


def test_no_file_sits_in_the_vendor_folder_without_a_record():
    on_disk = {p.name for p in (VENDOR / "fonts").iterdir()}
    assert on_disk == set(RECORD["files"])


def test_the_record_names_a_commit_in_dewlab():
    assert len(RECORD["source"]["commit"]) == 40
    assert RECORD["source"]["repository"] == "https://github.com/deweydex/dewlab"
