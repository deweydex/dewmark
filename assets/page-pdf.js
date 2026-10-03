/* The PDF the page writes (decision 23).

   Every hand-in includes a PDF, made by the page itself with no network: for
   each part of the paper, its printed number and heading and the answer as the
   student typed it (text; code with line numbers; the chosen options; the
   filled gaps; "not attempted"), under the student's name, student number and
   the exam code on every page, with the Paper ID and the receipt in the footer.
   The question wording stays in the paper, not in the PDF.

   This is a small PDF writer of our own and not a library, for three reasons.
   The output is plain PDF 1.4 with an ordinary cross-reference table, which is
   what the PDF tools in Moodle's grader read. The page needs no code it did not
   write. And everything that goes in a file a marker will open is here to read.
   It writes text, rules, and fonts, and nothing else: no pictures yet.

   The text is set in DejaVu Sans, with DejaVu Sans Mono for code (cut down to
   the characters a student is likely to write: assets/vendor/pdf-fonts/, made by
   dev/make_pdf_fonts.py). A character in neither is shown as U+FFFD, and the
   page tells the student which, and offers Print or save as PDF instead. Bold
   is the same letters drawn with a thin outline. */

const PDF_SIZE = { width: 595.28, height: 841.89, left: 56, right: 56, top: 84, bottom: 70 };
const PDF_INK = "0.10 0.10 0.10";
const PDF_MUTED = "0.38 0.40 0.45";
const PDF_ACCENT = "0.106 0.165 0.290";
const PDF_RULE = "0.78 0.80 0.85";

const number = (value) => {
  const text = value.toFixed(2);
  return text.replace(/\.?0+$/, "") || "0";
};
const encodeAscii = (text) => Uint8Array.from(text, (c) => c.charCodeAt(0) & 255);
const concatBytes = (parts) => {
  const out = new Uint8Array(parts.reduce((sum, p) => sum + p.length, 0));
  let at = 0;
  for (const part of parts) { out.set(part, at); at += part.length; }
  return out;
};

/* --- TrueType ------------------------------------------------------------------------ */

/* Reads the few things of a TrueType file that a PDF needs: how wide each glyph
   is, which glyph a character has, and the figures of the font descriptor. */
class TrueType {
  constructor(bytes) {
    this.bytes = bytes;
    const view = (this.view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength));
    this.tables = {};
    for (let i = 0, count = view.getUint16(4); i < count; i++) {
      const at = 12 + i * 16;
      const tag = String.fromCharCode(...bytes.subarray(at, at + 4));
      this.tables[tag] = { offset: view.getUint32(at + 8), length: view.getUint32(at + 12) };
    }
    for (const need of ["head", "hhea", "hmtx", "maxp", "cmap", "glyf", "loca"]) {
      if (!this.tables[need]) throw new Error("The font has no " + need + " table.");
    }
    const head = this.tables.head.offset;
    this.unitsPerEm = view.getUint16(head + 18);
    this.box = [36, 38, 40, 42].map((at) => view.getInt16(head + at));
    const hhea = this.tables.hhea.offset;
    this.ascent = view.getInt16(hhea + 4);
    this.descent = view.getInt16(hhea + 6);
    this.metricCount = view.getUint16(hhea + 34);
    this.capHeight = this.unitsPerEm * 0.72;
    const os2 = this.tables["OS/2"];
    if (os2 && os2.length >= 90 && view.getUint16(os2.offset) >= 2) {
      this.capHeight = view.getInt16(os2.offset + 88) || this.capHeight;
    }
    this.italicAngle = this.tables.post ? view.getInt32(this.tables.post.offset + 4) / 65536 : 0;
    this.codes = this.readCmap();
  }

  /* The width of a glyph in the thousandths of an em that a PDF counts in. */
  width(gid) {
    const index = Math.min(gid, this.metricCount - 1);
    return (this.view.getUint16(this.tables.hmtx.offset + index * 4) * 1000) / this.unitsPerEm;
  }

  glyph(codePoint) {
    return this.codes.get(codePoint) || 0;
  }

  readCmap() {
    const { view } = this;
    const table = this.tables.cmap.offset;
    let chosen = null;
    for (let i = 0, count = view.getUint16(table + 2); i < count; i++) {
      const at = table + 4 + i * 8;
      const platform = view.getUint16(at), encoding = view.getUint16(at + 2);
      const where = table + view.getUint32(at + 4);
      const format = view.getUint16(where);
      const rank = (platform === 3 && encoding === 10 && format === 12) ? 3
        : (platform === 0 && format === 12) ? 3
        : (platform === 3 && encoding === 1 && format === 4) ? 2
        : (platform === 0 && format === 4) ? 2 : 0;
      if (rank && (!chosen || rank > chosen.rank)) chosen = { rank, where, format };
    }
    if (!chosen) throw new Error("The font has no character map this writer can read.");
    const codes = new Map();
    const at = chosen.where;
    if (chosen.format === 12) {
      for (let g = 0, groups = view.getUint32(at + 12); g < groups; g++) {
        const start = view.getUint32(at + 16 + g * 12), end = view.getUint32(at + 20 + g * 12);
        const first = view.getUint32(at + 24 + g * 12);
        for (let c = start; c <= end; c++) if (first + c - start) codes.set(c, first + c - start);
      }
      return codes;
    }
    const segments = view.getUint16(at + 6) / 2;
    const endAt = at + 14, startAt = endAt + segments * 2 + 2;
    const deltaAt = startAt + segments * 2, rangeAt = deltaAt + segments * 2;
    for (let s = 0; s < segments; s++) {
      const end = view.getUint16(endAt + s * 2), start = view.getUint16(startAt + s * 2);
      const delta = view.getInt16(deltaAt + s * 2), range = view.getUint16(rangeAt + s * 2);
      for (let c = start; c <= end && c < 0xffff; c++) {
        let gid = 0;
        if (range === 0) gid = (c + delta) & 0xffff;
        else {
          const found = view.getUint16(rangeAt + s * 2 + range + (c - start) * 2);
          if (found) gid = (found + delta) & 0xffff;
        }
        if (gid) codes.set(c, gid);
      }
    }
    return codes;
  }
}

/* --- the file ----------------------------------------------------------------------------- */

/* Deflate in the zlib wrapper PDF's FlateDecode expects, if the browser can;
   a stream left as it is is just as valid and bigger. */
async function deflate(bytes) {
  if (typeof CompressionStream !== "function") return null;
  const stream = new CompressionStream("deflate");
  const writer = stream.writable.getWriter();
  writer.write(bytes);
  writer.close();
  return new Uint8Array(await new Response(stream.readable).arrayBuffer());
}

/* A PDF string: plain ASCII in brackets, anything else as UTF-16 in hexadecimal. */
function pdfString(text) {
  if (/^[\x20-\x7e]*$/.test(text)) return "(" + text.replace(/[\\()]/g, "\\$&") + ")";
  let hex = "FEFF";
  for (let i = 0; i < text.length; i++) hex += text.charCodeAt(i).toString(16).padStart(4, "0");
  return "<" + hex.toUpperCase() + ">";
}

class PdfFile {
  constructor() { this.objects = []; }

  reserve() { this.objects.push(null); return this.objects.length; }

  put(id, bytes) { this.objects[id - 1] = bytes; return id; }

  add(text) { return this.put(this.reserve(), encodeAscii(text)); }

  /* An object that is a dictionary followed by a stream. */
  async addStream(entries, data, id = this.reserve()) {
    const packed = await deflate(data);
    const body = packed || data;
    const head = "<< " + entries + (packed ? " /Filter /FlateDecode" : "") + " /Length " + body.length + " >>\nstream\n";
    this.put(id, concatBytes([encodeAscii(head), body, encodeAscii("\nendstream")]));
    return id;
  }

  /* Everything in order, with the cross-reference table that says where each
     object starts. The table is the plain kind, with no object streams, which is
     what an older PDF reader (the one in Moodle's grader, for one) can read. */
  finish(root, info, fileId) {
    const parts = [encodeAscii("%PDF-1.4\n%"), Uint8Array.of(0xe2, 0xe3, 0xcf, 0xd3, 10)];
    let length = parts.reduce((sum, p) => sum + p.length, 0);
    const offsets = [];
    this.objects.forEach((body, i) => {
      if (!body) throw new Error("Object " + (i + 1) + " was reserved and never written.");
      offsets.push(length);
      const wrapped = concatBytes([encodeAscii((i + 1) + " 0 obj\n"), body, encodeAscii("\nendobj\n")]);
      parts.push(wrapped);
      length += wrapped.length;
    });
    let table = "xref\n0 " + (this.objects.length + 1) + "\n0000000000 65535 f \n";
    for (const offset of offsets) table += String(offset).padStart(10, "0") + " 00000 n \n";
    table += "trailer\n<< /Size " + (this.objects.length + 1) + " /Root " + root + " 0 R /Info " + info
      + " 0 R /ID [<" + fileId + "> <" + fileId + ">] >>\nstartxref\n" + length + "\n%%EOF\n";
    parts.push(encodeAscii(table));
    return concatBytes(parts);
  }
}

/* A font in the file: a Type 0 font over a TrueType font that is embedded whole.
   Text is written as two-byte glyph numbers, and a ToUnicode table for the glyphs
   used lets a reader copy, search and read the text aloud. */
async function embedFont(file, font, name, used) {
  const scale = (n) => Math.round((n * 1000) / font.unitsPerEm);
  const data = font.bytes;
  const fontFile = await file.addStream("/Length1 " + data.length, data);
  const descriptor = file.add("<< /Type /FontDescriptor /FontName /" + name + " /Flags 4 /FontBBox ["
    + font.box.map(scale).join(" ") + "] /ItalicAngle " + number(font.italicAngle) + " /Ascent "
    + scale(font.ascent) + " /Descent " + scale(font.descent) + " /CapHeight " + scale(font.capHeight)
    + " /StemV 80 /FontFile2 " + fontFile + " 0 R >>");
  const gids = [...used.keys()].sort((a, b) => a - b);
  const widths = gids.map((gid) => gid + " [" + number(font.width(gid)) + "]").join(" ");
  const cid = file.add("<< /Type /Font /Subtype /CIDFontType2 /BaseFont /" + name
    + " /CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> /FontDescriptor "
    + descriptor + " 0 R /DW 1000 /W [" + widths + "] /CIDToGIDMap /Identity >>");
  const hex4 = (n) => n.toString(16).padStart(4, "0");
  const unicode = (cp) => cp > 0xffff
    ? hex4(0xd800 + ((cp - 0x10000) >> 10)) + hex4(0xdc00 + ((cp - 0x10000) & 0x3ff)) : hex4(cp);
  let map = "/CIDInit /ProcSet findresource begin 12 dict begin begincmap\n"
    + "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
    + "/CMapName /Adobe-Identity-UCS def /CMapType 2 def\n1 begincodespacerange <0000> <FFFF> endcodespacerange\n";
  for (let i = 0; i < gids.length; i += 100) {
    const chunk = gids.slice(i, i + 100);
    map += chunk.length + " beginbfchar\n"
      + chunk.map((gid) => "<" + hex4(gid) + "> <" + unicode(used.get(gid)) + ">").join("\n") + "\nendbfchar\n";
  }
  map += "endcmap CMapName currentdict /CMap defineresource pop end end";
  const toUnicode = await file.addStream("", encodeAscii(map));
  return file.add("<< /Type /Font /Subtype /Type0 /BaseFont /" + name + " /Encoding /Identity-H"
    + " /DescendantFonts [" + cid + " 0 R] /ToUnicode " + toUnicode + " 0 R >>");
}

/* --- setting text -------------------------------------------------------------------------- */

/* The fonts of one PDF, and what it takes to draw a character: a glyph from the
   font asked for, else from the other, else the replacement character. */
class PdfFonts {
  constructor(sans, mono) {
    this.list = [sans, mono];
    this.used = [new Map(), new Map()];
    this.missing = new Set();
    this.cache = new Map();
  }

  resolve(codePoint, mono) {
    const key = (mono ? "m" : "s") + codePoint;
    let found = this.cache.get(key);
    if (found) return found;
    const order = mono ? [1, 0] : [0, 1];
    for (const index of order) {
      const gid = this.list[index].glyph(codePoint);
      if (gid) { found = { font: index, gid, codePoint }; break; }
    }
    if (!found) {
      /* A box is drawn, and the text a reader copies from it is a question mark. */
      this.missing.add(String.fromCodePoint(codePoint));
      const box = codePoint === 0xfffd ? { font: 0, gid: 0 } : this.resolve(0xfffd, mono);
      found = { font: box.font, gid: box.gid, codePoint: 0x3f };
    }
    this.cache.set(key, found);
    return found;
  }

  /* Glyphs for a piece of text, with the characters that cannot be written
     taken out and tabs made into spaces. */
  glyphs(text, mono) {
    const out = [];
    for (const char of text.replace(/\t/g, "    ")) {
      const cp = char.codePointAt(0);
      if (cp < 0x20 || (cp >= 0x7f && cp < 0xa0) || (cp >= 0x200b && cp <= 0x200f)
          || cp === 0xfeff || (cp >= 0x202a && cp <= 0x202e) || (cp >= 0x2066 && cp <= 0x2069)) continue;
      out.push(this.resolve(cp, mono));
    }
    return out;
  }

  width(glyphs, size) {
    let sum = 0;
    for (const g of glyphs) sum += this.list[g.font].width(g.gid);
    return (sum * size) / 1000;
  }

  /* Break text into lines no wider than `limit` at spaces, a word wider than
     the limit by letters. A new line in the text is kept; spaces at the start of
     a paragraph are kept (they are indentation); spaces at a break are dropped. */
  wrap(text, size, limit, mono) {
    const lines = [];
    for (const paragraph of text.replace(/\r\n?|\u2028|\u2029/g, "\n").split("\n")) {
      const glyphs = this.glyphs(paragraph, mono);
      const tokens = [];
      for (const g of glyphs) {
        const space = g.codePoint === 32 || g.codePoint === 0xa0;
        const last = tokens[tokens.length - 1];
        if (last && last.space === space) last.glyphs.push(g);
        else tokens.push({ space, glyphs: [g] });
      }
      let line = [], width = 0, first = true;
      const push = () => {
        while (line.length && line[line.length - 1].codePoint === 32) line.pop();
        lines.push(line);
        line = []; width = 0; first = false;
      };
      for (const token of tokens) {
        const w = this.width(token.glyphs, size);
        if (token.space) {
          if (!line.length && !first) continue;
          if (width + w > limit && line.length) { push(); continue; }
          line.push(...token.glyphs); width += w;
        } else if (width + w <= limit) {
          line.push(...token.glyphs); width += w;
        } else {
          if (line.some((g) => g.codePoint !== 32)) push();
          if (w <= limit) { line.push(...token.glyphs); width = w; continue; }
          for (const g of token.glyphs) {                      // a word wider than the line
            const gw = this.width([g], size);
            if (width + gw > limit && line.length) push();
            line.push(g); width += gw;
          }
        }
      }
      push();
    }
    return lines;
  }

  /* The operators that draw one line of glyphs with its left end at x and its
     baseline at y: a run for each stretch in one font. */
  draw(glyphs, x, y, size, { colour = PDF_INK, bold = false } = {}) {
    const runs = [];
    for (const g of glyphs) {
      const last = runs[runs.length - 1];
      if (last && last.font === g.font) last.glyphs.push(g);
      else runs.push({ font: g.font, glyphs: [g] });
    }
    let at = x;
    let out = "q " + colour + " rg " + colour + " RG" + (bold ? " " + number(size * 0.035) + " w" : "") + "\n";
    for (const run of runs) {
      let hex = "";
      for (const g of run.glyphs) {
        this.used[run.font].set(g.gid, g.codePoint);
        hex += g.gid.toString(16).padStart(4, "0");
      }
      out += "BT /F" + (run.font + 1) + " " + number(size) + " Tf " + (bold ? "2" : "0") + " Tr 1 0 0 1 "
        + number(at) + " " + number(y) + " Tm <" + hex + "> Tj ET\n";
      at += this.width(run.glyphs, size);
    }
    return out + "Q\n";
  }
}

/* --- laying a paper out ------------------------------------------------------------------- */

class PdfLayout {
  constructor(fonts) {
    this.fonts = fonts;
    this.pages = [];
    this.y = 0;
    this.bar = null;
    this.queue = [];
    this.newPage();
  }

  get limit() { return PDF_SIZE.width - PDF_SIZE.left - PDF_SIZE.right; }

  newPage() {
    this.closeBar();
    this.pages.push([]);
    this.y = PDF_SIZE.height - PDF_SIZE.top;
  }

  add(ops) { this.pages[this.pages.length - 1].push(ops); }

  ensure(height) {
    if (this.y - height < PDF_SIZE.bottom) this.newPage();
  }

  /* The thin rule beside an answer, drawn for the part of it on each page. */
  openBar() { this.bar = { page: this.pages.length - 1, top: this.y }; }

  closeBar() {
    if (!this.bar) return;
    const x = PDF_SIZE.left + 3;
    this.pages[this.bar.page].push("q " + PDF_RULE + " RG 1.6 w " + number(x) + " " + number(this.bar.top - 1)
      + " m " + number(x) + " " + number(this.y - 3) + " l S Q\n");
    this.bar = null;
  }

  /* Lines of text, one after another, over as many pages as it takes. */
  lines(rows, { size, step, indent = 0, mono = false, colour = PDF_INK, bold = false, bar = false }) {
    if (bar) this.openBar();
    for (const row of rows) {
      if (this.y - step < PDF_SIZE.bottom) {
        const wasBar = this.bar !== null;
        this.newPage();
        if (wasBar) this.openBar();
      }
      this.y -= step;
      const glyphs = row.glyphs || row;
      if (row.number !== undefined && row.number !== null) {
        const label = this.fonts.glyphs(String(row.number), true);
        this.add(this.fonts.draw(label, PDF_SIZE.left + indent + (row.gutter || 0) - 5
          - this.fonts.width(label, size), this.y, size, { colour: PDF_MUTED }));
      }
      if (glyphs.length) {
        this.add(this.fonts.draw(glyphs, PDF_SIZE.left + indent + (row.gutter || 0), this.y, size, { colour, bold }));
      }
    }
    if (bar) this.closeBar();
  }

  gap(height) { this.y -= height; }

  /* A heading waits until the next heading or an answer arrives, so that a run of
     headings and the first lines under them are kept on one page. */
  heading(text, style) {
    this.queue.push({ text, style });
  }

  flush(extra = 0) {
    if (!this.queue.length) return;
    const drawn = this.queue.map(({ text, style }) => ({
      rows: this.fonts.wrap(text, style.size, this.limit - (style.indent || 0), false), style }));
    const height = drawn.reduce((sum, { rows, style }) => sum + style.before + rows.length * style.step, 0);
    this.ensure(height + extra);
    for (const { rows, style } of drawn) {
      this.gap(style.before);
      this.lines(rows, { size: style.size, step: style.step, indent: style.indent || 0, bold: true, colour: PDF_ACCENT });
      if (style.rule) {
        this.add("q " + PDF_ACCENT + " RG 0.8 w " + number(PDF_SIZE.left) + " " + number(this.y - 3) + " m "
          + number(PDF_SIZE.width - PDF_SIZE.right) + " " + number(this.y - 3) + " l S Q\n");
        this.gap(4);
      }
    }
    this.queue = [];
  }
}

const HEADINGS = {
  section: { size: 12.5, step: 16, before: 16, rule: true },
  question: { size: 11.5, step: 15, before: 14 },
  part: { size: 10.5, step: 14, before: 10 },
  subpart: { size: 10, step: 13, before: 7, indent: 10 },
};

/* One answer box, drawn under its heading. */
function layoutAnswer(layout, block) {
  const fonts = layout.fonts;
  const text = { size: 10.5, step: 14.2 };
  const wrapped = (words, size, limit, mono) => fonts.wrap(words, size, limit, mono);
  const labels = block.labels.map((label) => wrapped(label, 8.5, layout.limit - 12, false));
  let body = [];
  let mono = false;
  let marked = "";
  if (!block.attempted) {
    body = [fonts.glyphs("(not attempted)", false)];
    marked = PDF_MUTED;
  } else if (block.code !== undefined) {
    mono = true;
    const listing = block.code.replace(/\n$/, "").split("\n");     // a last newline is not a line
    const gutter = String(listing.length).length * 5.7 + 10;       // mono at 9 pt is 5.7 pt a character
    listing.forEach((line, index) => {
      wrapped(line, 9, layout.limit - 12 - gutter, true).forEach((row, part) => {
        body.push({ glyphs: row, number: part === 0 ? index + 1 : null, gutter });
      });
    });
  } else if (block.text !== undefined) {
    body = wrapped(block.text, text.size, layout.limit - 12, false);
  } else {
    body = block.rows.flatMap((row) => wrapped(row, text.size, layout.limit - 12, false));
  }
  const first = body.slice(0, 2).length * (mono ? 11.6 : text.step);
  layout.flush(first + labels.reduce((sum, rows) => sum + rows.length * 11, 0) + 8);
  layout.gap(3);
  for (const rows of labels) layout.lines(rows, { size: 8.5, step: 11, indent: 12, colour: PDF_MUTED });
  if (mono) layout.lines(body, { size: 9, step: 11.6, indent: 12, mono: true, bar: true });
  else layout.lines(body, { size: text.size, step: text.step, indent: 12, colour: marked || PDF_INK, bar: true });
  layout.gap(3);
}

/* The title page block: who sat what, and the codes that tie the file to the others. */
function layoutTitle(layout, content) {
  const fonts = layout.fonts;
  layout.lines(fonts.wrap(content.title, 17, layout.limit, false), { size: 17, step: 21, bold: true, colour: PDF_ACCENT });
  for (const line of content.subtitle) {
    layout.lines(fonts.wrap(line, 9.5, layout.limit, false), { size: 9.5, step: 13, colour: PDF_MUTED });
  }
  layout.gap(10);
  const rows = content.facts;
  const labelWidth = Math.max(...rows.map(([label]) => fonts.width(fonts.glyphs(label, false), 9.5))) + 12;
  for (const [label, value] of rows) {
    const wrapped = fonts.wrap(value, 9.5, layout.limit - labelWidth, false);
    layout.ensure(13 * Math.max(1, wrapped.length));
    layout.add(fonts.draw(fonts.glyphs(label, false), PDF_SIZE.left, layout.y - 13, 9.5, { colour: PDF_MUTED }));
    layout.lines(wrapped.length ? wrapped : [[]], { size: 9.5, step: 13, indent: labelWidth });
  }
  layout.gap(4);
  layout.add("q " + PDF_RULE + " RG 0.8 w " + number(PDF_SIZE.left) + " " + number(layout.y) + " m "
    + number(PDF_SIZE.width - PDF_SIZE.right) + " " + number(layout.y) + " l S Q\n");
}

/* The header and footer of every page, drawn last because they say how many pages there are. */
function frame(layout, content) {
  const fonts = layout.fonts;
  const total = layout.pages.length;
  layout.pages.forEach((ops, index) => {
    const who = fonts.glyphs(content.student + " · " + content.studentNumber + " · " + content.examCode, false);
    const page = fonts.glyphs("Page " + (index + 1) + " of " + total, false);
    const top = PDF_SIZE.height - 44;
    ops.push(fonts.draw(who, PDF_SIZE.left, top, 9, { colour: PDF_INK, bold: true }));
    ops.push(fonts.draw(page, PDF_SIZE.width - PDF_SIZE.right - fonts.width(page, 9), top, 9, { colour: PDF_MUTED }));
    ops.push("q " + PDF_RULE + " RG 0.8 w " + number(PDF_SIZE.left) + " " + number(top - 6) + " m "
      + number(PDF_SIZE.width - PDF_SIZE.right) + " " + number(top - 6) + " l S Q\n");
    const codes = fonts.glyphs("Paper ID " + content.paperId + " · Receipt " + content.receipt, false);
    const name = fonts.glyphs(content.title, false);
    ops.push("q " + PDF_RULE + " RG 0.8 w " + number(PDF_SIZE.left) + " 48 m "
      + number(PDF_SIZE.width - PDF_SIZE.right) + " 48 l S Q\n");
    ops.push(fonts.draw(codes, PDF_SIZE.left, 34, 8.5, { colour: PDF_INK }));
    ops.push(fonts.draw(name, PDF_SIZE.width - PDF_SIZE.right - Math.min(fonts.width(name, 8.5), layout.limit * 0.5),
      34, 8.5, { colour: PDF_MUTED }));
  });
}

/* The PDF for a piece of content (see pdfContent), as bytes, with the characters
   it could not draw. */
async function writePdf(content, sansBytes, monoBytes) {
  const fonts = new PdfFonts(new TrueType(sansBytes), new TrueType(monoBytes));
  const layout = new PdfLayout(fonts);
  layoutTitle(layout, content);
  for (const block of content.blocks) {
    if (block.type === "answer") layoutAnswer(layout, block);
    else layout.heading(block.text, HEADINGS[block.type]);
  }
  layout.flush();
  layout.closeBar();
  frame(layout, content);

  const file = new PdfFile();
  const catalog = file.reserve(), pagesId = file.reserve();
  const pageIds = [];
  const streams = [];
  for (const ops of layout.pages) {
    streams.push(await file.addStream("", encodeAscii(ops.join(""))));
    pageIds.push(file.reserve());
  }
  const sans = await embedFont(file, fonts.list[0], "DMKPDF+DejaVuSans", fonts.used[0]);
  const mono = fonts.used[1].size ? await embedFont(file, fonts.list[1], "DMKPDF+DejaVuSansMono", fonts.used[1]) : 0;
  pageIds.forEach((id, index) => file.put(id, encodeAscii(
    "<< /Type /Page /Parent " + pagesId + " 0 R /MediaBox [0 0 " + number(PDF_SIZE.width) + " "
    + number(PDF_SIZE.height) + "] /Resources << /Font << /F1 " + sans + " 0 R"
    + (mono ? " /F2 " + mono + " 0 R" : "") + " >> >> /Contents " + streams[index] + " 0 R >>")));
  file.put(pagesId, encodeAscii("<< /Type /Pages /Kids [" + pageIds.map((id) => id + " 0 R").join(" ")
    + "] /Count " + pageIds.length + " >>"));
  file.put(catalog, encodeAscii("<< /Type /Catalog /Pages " + pagesId + " 0 R /Lang (en-IE) >>"));
  const when = (content.when || "").replace(/[-:T]/g, "").slice(0, 14);
  const info = file.add("<< /Title " + pdfString(content.title + ": " + content.student + " (" + content.studentNumber + ")")
    + " /Author " + pdfString(content.student) + " /Subject " + pdfString("Answers handed in on a dewmark page")
    + " /Creator (dewmark) /Producer (dewmark page writer 1)"
    + (when.length === 14 ? " /CreationDate (D:" + when + "Z) /ModDate (D:" + when + "Z)" : "") + " >>");
  const id = hex(sha256(encodeAscii(content.receipt + content.paperId + content.studentNumber))).slice(0, 32);
  return { bytes: file.finish(catalog, info, id), missing: [...fonts.missing], pages: layout.pages.length };
}

/* --- what goes in a PDF --------------------------------------------------------------- */

/* A part of the page's text with its gaps filled in from the student's answer:
   each gap is written as [what they gave], and an empty one as [ ]. */
function textWithGaps(node, values) {
  let out = "";
  for (const child of node.childNodes) {
    if (child.nodeType === 3) out += child.nodeValue;
    else if (child.nodeType === 1 && child.dataset && child.dataset.slot) {
      const value = values[Number(child.dataset.slot) - 1];
      out += "[" + (typeof value === "string" && value ? value : " ") + "]";
    } else if (child.nodeType === 1 && !/^(SCRIPT|STYLE)$/.test(child.tagName)) {
      out += textWithGaps(child, values);
    }
  }
  return out;
}

const tidy = (text) => text.replace(/\s+/g, " ").trim();

function answerContent(root) {
  const name = root.dataset.answer, kind = root.dataset.kind;
  const value = state.answers[name];
  const block = { type: "answer", name, kind, attempted: value !== undefined, labels: [] };
  for (const label of root.querySelectorAll(".dm-small-label")) {
    block.labels.push(label.textContent.trim() === "Not marked" ? "Rough work: not marked" : label.textContent.trim());
  }
  if (!block.attempted) return block;
  if (kind === "python exec") block.code = value.code;
  else if (kind === "code") block.code = value;
  else if (kind === "answer" || kind === "maths") block.text = value;
  else if (kind === "essay") {
    block.text = value;
    const words = value.trim().split(/\s+/).filter(Boolean).length;
    block.labels.push(words + (words === 1 ? " word" : " words"));
  } else if (kind === "choice") {
    block.rows = [...root.querySelectorAll(".dm-option")]
      .filter((option) => value.includes(option.querySelector("input").value))
      .map((option) => option.querySelector(".dm-letter").textContent + ". "
        + tidy(option.querySelector(".dm-option-text").textContent));
  } else if (kind === "table") {
    block.rows = [...root.querySelectorAll("tr")].map((row) =>
      [...row.cells].map((cell) => tidy(textWithGaps(cell, value))).join("   |   "));
  } else {
    const lines = root.querySelectorAll(kind === "boxes" ? ".dm-boxline" : ".dm-blanks p");
    block.rows = [...lines].map((line) => tidy(textWithGaps(line, value)));
  }
  return block;
}

const stamp = (iso) => iso ? iso.replace("T", " ").slice(0, 16) + " UTC" : "not yet";

/* Everything the PDF says, from the paper on the page and the student's record. */
function pdfContent() {
  gatherState();
  const exam = MODEL.exam;
  const blocks = [];
  const headings = { "dm-section-title": "section", "dm-question-title": "question",
    "dm-part-title": "part", "dm-subpart-title": "subpart" };
  for (const el of document.querySelectorAll(
      "#dm-paper .dm-section-title, #dm-paper .dm-question-title, #dm-paper .dm-part-title, "
      + "#dm-paper .dm-subpart-title, #dm-paper .dm-answer")) {
    if (el.classList.contains("dm-answer")) blocks.push(answerContent(el));
    else blocks.push({ type: headings[el.className.split(" ")[0]], text: tidy(el.textContent) });
  }
  const parts = Object.values(MODEL.questions).flatMap((question) => question.parts).filter((p) => p.marks);
  const attempted = parts.filter(partAnswered).length;
  const kind = { student: "Student paper", practice: "Practice version", "answer-key": "Answer key" }[VARIANT];
  const details = state.student || {};
  return {
    title: exam.title, subtitle: [[exam.institution, exam.college].filter(Boolean).join(" · "),
      [exam.module && exam.module + (exam.moduleCode ? " (" + exam.moduleCode + ")" : ""), exam.session]
        .filter(Boolean).join(" · ")].filter(Boolean),
    student: details["full name"] || "", studentNumber: details["student number"] || "", examCode: exam.code,
    paperId: exam.fingerprint, receipt: state.receipt || "not yet saved", when: state.finished_at || state.saved_at,
    facts: [["Candidate", (details["full name"] || "") + ", student number " + (details["student number"] || "")],
      ["Paper", exam.title + " (" + exam.code + ", version " + exam.version + "), " + kind],
      ["Paper ID", exam.fingerprint], ["Receipt", state.receipt || "not yet saved"],
      ["Started", stamp(state.started_at)], ["Finished", stamp(state.finished_at)],
      ["Answers", attempted + " of " + parts.length + " parts have an answer"]],
    blocks,
  };
}

/* The fonts are carried in the page as base64, and read when the first PDF is made. */
let pdfFontBytes = null;
function pdfFonts() {
  if (!pdfFontBytes) {
    const carried = JSON.parse($("dewmark-pdf-fonts").textContent);
    const decode = (text) => Uint8Array.from(atob(text), (c) => c.charCodeAt(0));
    pdfFontBytes = { sans: decode(carried.sans), mono: decode(carried.mono) };
  }
  return pdfFontBytes;
}

async function makePdf() {
  const fonts = pdfFonts();
  return writePdf(pdfContent(), fonts.sans, fonts.mono);
}
