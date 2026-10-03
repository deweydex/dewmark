"""Files copied from elsewhere are kept as they were copied (decision 31).

assets/vendor/SOURCE.json says where each file came from and what it held when
it was copied or made; a hand edit, or a file added without a record, fails here.
"""

import hashlib
import json
from pathlib import Path

import pytest

VENDOR = Path(__file__).resolve().parent.parent / "assets" / "vendor"
RECORD = json.loads((VENDOR / "SOURCE.json").read_text(encoding="utf-8"))
FILES = {name: held for source in RECORD["sources"] for name, held in source["files"].items()}


@pytest.mark.parametrize("name", sorted(FILES))
def test_every_copied_file_is_as_it_was_copied(name):
    data = (VENDOR / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == FILES[name]["sha256"], f"{name} was edited by hand"
    assert len(data) == FILES[name]["bytes"]


def test_no_file_sits_in_the_vendor_folder_without_a_record():
    on_disk = {p.relative_to(VENDOR).as_posix() for p in VENDOR.rglob("*")
               if p.is_file() and p.name != "SOURCE.json"}
    assert on_disk == set(FILES)


def test_each_source_says_where_it_came_from():
    dewlab, dejavu = RECORD["sources"]
    assert len(dewlab["commit"]) == 40 and dewlab["repository"] == "https://github.com/deweydex/dewlab"
    assert dejavu["upstream"].startswith("https://dejavu-fonts.github.io") and dejavu["made_by"]
    assert dejavu["licence"] in dejavu["files"], "a font is carried with its licence"


def test_a_subset_font_keeps_the_name_the_licence_allows():
    """DejaVu's licence lets a modified font be distributed if it is not named
    Bitstream or Vera. The subsets keep the name DejaVu."""
    for name in FILES:
        if name.endswith("-subset.ttf"):
            data = (VENDOR / name).read_bytes()
            text = data.decode("latin-1") + data.decode("utf-16-be", "ignore")
            assert "DejaVu" in text
