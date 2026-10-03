"""Make the fonts the page writes PDFs with (assets/vendor/pdf-fonts/).

The page's PDF writer (assets/page-pdf.js) embeds a font in every PDF it makes,
so that Irish accents, Polish and Romanian letters, Greek, Cyrillic and the
common mathematical symbols print as the student typed them, on a computer with
no network and whatever fonts it has. This script cuts DejaVu Sans and
DejaVu Sans Mono down to those characters. It is run by hand, when the
character set changes, and its output is committed with the record in
assets/vendor/SOURCE.json; tests/test_vendor.py fails if a file is edited by
hand. Nothing here runs when a paper is built.

    pip install fonttools
    python dev/make_pdf_fonts.py [DIRECTORY holding DejaVuSans.ttf and DejaVuSansMono.ttf]

DejaVu fonts are Bitstream Vera with public-domain changes. Its licence
(assets/vendor/pdf-fonts/DEJAVU-LICENSE.txt) lets the font be copied and
embedded if the notice stays with it, and lets a modified font be distributed if
it is not named Bitstream or Vera; a subset named DejaVu is within that.
"""

import hashlib
import json
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "vendor" / "pdf-fonts"

LATIN = [(0x0020, 0x007E), (0x00A0, 0x024F), (0x02C6, 0x02DD), (0x0300, 0x036F),
         (0x2000, 0x206F), (0x2070, 0x209F), (0x20A0, 0x20CF), (0x2100, 0x214F),
         (0x2150, 0x218F), (0xFFFD, 0xFFFD)]
# Sans carries everything a student is likely to write that is not code: Greek and
# Cyrillic, Vietnamese letters, arrows and the mathematical operators, and a few
# marks a student uses to tick or point.
WIDE = LATIN + [(0x0370, 0x03FF), (0x0400, 0x04FF), (0x1E00, 0x1EFF), (0x2190, 0x21FF),
                (0x2200, 0x22FF), (0x2713, 0x2718), (0x2605, 0x2606), (0x25A0, 0x25A1),
                (0x25AA, 0x25AB), (0x25B2, 0x25B2), (0x25BA, 0x25BA), (0x25BC, 0x25BC),
                (0x25CB, 0x25CB), (0x25CF, 0x25CF)]
# Mono is for code: Latin and punctuation only. A character it lacks is drawn
# from Sans, so a listing is never refused for a Greek letter in a comment.
FONTS = {"DejaVuSans": WIDE, "DejaVuSansMono": LATIN}


def make(source, target, ranges):
    options = subset.Options()
    options.layout_features = []
    options.hinting = False
    options.notdef_outline = True
    options.name_IDs = [0, 1, 2, 3, 4, 5, 6]
    options.glyph_names = False
    options.drop_tables += ["GSUB", "GPOS", "GDEF", "kern", "MATH", "FFTM", "gasp", "BASE", "JSTF"]
    font = TTFont(source, recalcTimestamp=False)
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=[c for a, b in ranges for c in range(a, b + 1)])
    subsetter.subset(font)
    font.save(target)
    return len(TTFont(target).getBestCmap())


def main(folder):
    record = {}
    for name, ranges in FONTS.items():
        source = Path(folder) / f"{name}.ttf"
        target = OUT / f"{name}-subset.ttf"
        characters = make(source, target, ranges)
        data = target.read_bytes()
        record[target.name] = {
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "characters": characters,
            "from": {"file": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}}
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/usr/share/fonts/truetype/dejavu")
