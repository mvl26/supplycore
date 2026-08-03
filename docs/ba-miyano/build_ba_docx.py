#!/usr/bin/env python3
"""Sinh bản Word (.docx) của Tài liệu BA SupplyCore MVL từ bản HTML gốc.

    python3 docs/ba-miyano/build_ba_docx.py

Đọc  : docs/ba-miyano/SupplyCore_MVL_BA.html   (bản gốc — sửa nội dung ở đây)
Ghi  : docs/ba-miyano/SupplyCore_MVL_BA.docx

Yêu cầu: python-docx  (pip install python-docx)

GIỚI HẠN ĐÃ BIẾT — sơ đồ mermaid không render thành ảnh (máy build không có
mermaid-cli/pandoc). Mỗi sơ đồ được đưa vào Word dưới dạng KHỐI VĂN BẢN
monospace kèm chú thích, vẫn đọc hiểu được luồng. Nếu cần ảnh thật: cài
`npm i -g @mermaid-js/mermaid-cli` rồi render riêng và chèn tay.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

try:
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, RGBColor
except ImportError:                                          # pragma: no cover
    sys.exit("Thiếu python-docx. Chạy: pip install python-docx")


HERE = Path(__file__).resolve().parent
SRC = HERE / "SupplyCore_MVL_BA.html"
OUT = HERE / "SupplyCore_MVL_BA.docx"

INK = RGBColor(0x15, 0x23, 0x3F)
ACCENT = RGBColor(0x24, 0x56, 0xC9)
FAINT = RGBColor(0x7C, 0x89, 0xA6)
CRIT = RGBColor(0xBE, 0x3A, 0x3A)
WARN = RGBColor(0x9C, 0x65, 0x11)
OK = RGBColor(0x1B, 0x7A, 0x4E)

NOTE_COLOR = {"info": ACCENT, "warn": WARN, "crit": CRIT, "ok": OK}


# ---------------------------------------------------------------------------
# Bước 1 — phân tích HTML thành danh sách "khối" trung gian
# ---------------------------------------------------------------------------
# Mỗi khối là dict: {"kind": ..., ...}. Runs văn bản giữ được in đậm / mã lệnh
# vì Word cần biết định dạng từng đoạn chữ, không chỉ chuỗi thô.

INLINE_TAGS = {"strong", "b", "em", "i", "code", "span", "small", "a", "br", "sup"}
SKIP_TAGS = {"style", "script", "title"}


class BAParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict] = []
        self.skip_depth = 0

        self.stack: list[str] = []          # ngữ cảnh thẻ block đang mở
        self.div_depth = 0                  # độ sâu <div> hiện tại
        self.block_depth: list[int] = []    # độ sâu <div> lúc mở từng block trong stack
        self.runs: list[tuple[str, set]] = []   # (text, styles) đang tích lũy
        self.styles: list[str] = []         # style inline đang bật

        # bảng
        self.table: list[list[list]] | None = None
        self.row: list[list] | None = None
        self.cell_runs: list | None = None
        self.in_head = False
        self.head_rows = 0

        # callout
        self.note_kind: str | None = None

        # sơ đồ
        self.in_pre = False
        self.pre_buf: list[str] = []

        # mục lục sidebar -> bỏ qua
        self.in_toc = False

    # -- tiện ích ---------------------------------------------------------
    def _flush_runs(self) -> list[tuple[str, set]]:
        runs = [(t, s) for t, s in self.runs if t.strip() or t in (" ", "\n")]
        while runs and runs[0][0] in (" ", "\n"):
            runs.pop(0)
        while runs and runs[-1][0] in (" ", "\n"):
            runs.pop()
        self.runs = []
        return runs

    def _emit(self, kind: str, **kw):
        self.blocks.append({"kind": kind, **kw})

    def _push(self, name: str):
        """Mở một block; nhớ độ sâu <div> để đóng đúng thẻ bao ngoài cùng."""
        self.stack.append(name)
        self.block_depth.append(self.div_depth)
        self.runs = []

    def _pop(self):
        self.block_depth.pop()
        return self.stack.pop()

    # -- HTMLParser -------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "")

        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return

        # Sidebar mục lục: Word tự sinh mục lục theo Heading, bỏ bản HTML.
        if tag == "details" and "toc" in cls:
            self.in_toc = True
            return
        if self.in_toc:
            return

        if tag == "pre" and "mermaid" in cls:
            self.in_pre = True
            self.pre_buf = []
            return
        if self.in_pre:
            # <br/> bên trong nhãn node mermaid: giữ dấu ngắt để chữ không dính nhau.
            if tag == "br":
                self.pre_buf.append(" / ")
            return

        if tag in ("h1", "h2", "h3", "h4", "p", "li"):
            self._push("cap" if (tag in ("p", "li") and "cap" in cls) else tag)
            return

        if tag == "div":
            self.div_depth += 1
            if "meta-row" in cls:
                self._push("meta")
            elif cls == "stat":
                self._push("stat")
            elif "note" in cls.split():
                kind = "info"
                for k in ("crit", "warn", "ok"):
                    if k in cls.split():
                        kind = k
                self.note_kind = kind
                self._push("note")
            elif "lead-card" in cls:
                self._push("pre-block")
            return

        if self.stack and self.stack[-1] in ("meta", "stat") and tag == "span":
            # mỗi <span> trong khối meta/stat là một mục riêng → xuống dòng
            if self.runs:
                self.runs.append(("\n", set()))
            return

        if tag == "table":
            self.table = []
            self.head_rows = 0
            return
        if tag == "thead":
            self.in_head = True
            return
        if tag == "tr" and self.table is not None:
            self.row = []
            return
        if tag in ("td", "th") and self.row is not None:
            self.cell_runs = []
            self.runs = []
            return

        # inline
        if tag in ("strong", "b"):
            self.styles.append("b")
        elif tag in ("em", "i"):
            self.styles.append("i")
        elif tag == "code":
            self.styles.append("mono")
        elif tag == "span" and ("chip" in cls or "sev" in cls or "nw" in cls):
            self.styles.append("mono")
        elif tag == "br":
            self.runs.append(("\n", set()))

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return

        if tag == "details" and self.in_toc:
            self.in_toc = False
            return
        if self.in_toc:
            return

        if tag == "pre" and self.in_pre:
            self.in_pre = False
            text = "".join(self.pre_buf).strip("\n")
            if text:
                self._emit("diagram", text=text)
            return

        if tag in ("strong", "b", "em", "i", "code", "span"):
            if self.styles:
                self.styles.pop()
            # Nhãn callout dùng <b> làm tiêu đề khối → tách dòng khỏi phần thân,
            # nếu không Word dán liền ("Thay đổi so với v1.0Quy tắc…").
            if tag == "b" and self.stack and self.stack[-1] == "note":
                self.runs.append(("\n", set()))
            return

        if tag in ("td", "th") and self.row is not None:
            self.row.append(self._flush_runs())
            self.cell_runs = None
            return
        if tag == "tr" and self.table is not None and self.row is not None:
            self.table.append(self.row)
            if self.in_head:
                self.head_rows += 1
            self.row = None
            return
        if tag == "thead":
            self.in_head = False
            return
        if tag == "table" and self.table is not None:
            if self.table:
                self._emit("table", rows=self.table, head_rows=self.head_rows or 1)
            self.table = None
            return

        if tag == "div":
            self.div_depth -= 1
            # Chỉ đóng block khi về đúng <div> đã mở nó (bỏ qua div lồng bên trong).
            if not (self.stack and self.stack[-1] in ("note", "pre-block", "meta", "stat")
                    and self.block_depth[-1] == self.div_depth + 1):
                return
        elif tag not in ("h1", "h2", "h3", "h4", "p", "li"):
            return

        if self.stack:
            top = self.stack[-1]
            expected = {"h1", "h2", "h3", "h4", "p", "li", "cap", "note",
                        "pre-block", "meta", "stat"}
            if top not in expected:
                return
            self._pop()
            runs = self._flush_runs()
            if not runs:
                return
            if top == "note":
                self._emit("note", runs=runs, note_kind=self.note_kind or "info")
                self.note_kind = None
            elif top == "pre-block":
                self._emit("pre", text="".join(t for t, _ in runs))
            elif top in ("meta", "stat"):
                self._emit(top, runs=runs)
            else:
                self._emit(top, runs=runs)

    def handle_data(self, data):
        if self.skip_depth or self.in_toc:
            return
        if self.in_pre:
            self.pre_buf.append(data)
            return
        if not data.strip():
            # giữ 1 khoảng trắng giữa hai run liền nhau (vd "</code> và")
            if self.runs and not self.runs[-1][0].endswith((" ", "\n")):
                self.runs.append((" ", set()))
            return
        text = re.sub(r"\s+", " ", data)
        self.runs.append((text, set(self.styles)))


# ---------------------------------------------------------------------------
# Bước 2 — dựng file Word
# ---------------------------------------------------------------------------
def _add_runs(par, runs, base_size=10.5, color=INK):
    for text, styles in runs:
        for i, chunk in enumerate(text.split("\n")):
            if i:
                par.add_run().add_break()
            if not chunk:
                continue
            r = par.add_run(chunk)
            r.font.size = Pt(base_size)
            r.font.color.rgb = color
            if "b" in styles:
                r.bold = True
            if "i" in styles:
                r.italic = True
            if "mono" in styles:
                r.font.name = "Consolas"
                r.font.size = Pt(base_size - 1)
                r.font.color.rgb = ACCENT


def _plain(runs) -> str:
    return "".join(t for t, _ in runs)


def build(blocks) -> Document:
    doc = Document()

    normal = doc.styles["Normal"]
    normal.font.name = "Segoe UI"
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(6)

    first_h1 = True

    for b in blocks:
        kind = b["kind"]

        if kind == "h1":
            if first_h1:
                first_h1 = False
                t = doc.add_paragraph()
                t.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = t.add_run(_plain(b["runs"]))
                r.bold = True
                r.font.size = Pt(30)
                r.font.color.rgb = INK
                s = doc.add_paragraph()
                s.alignment = WD_ALIGN_PARAGRAPH.CENTER
                sr = s.add_run("Tài liệu Phân tích Nghiệp vụ (Business Analysis)")
                sr.font.size = Pt(12)
                sr.font.color.rgb = ACCENT
            else:
                doc.add_heading(_plain(b["runs"]), level=1)

        elif kind in ("h2", "h3", "h4"):
            lvl = {"h2": 1, "h3": 2, "h4": 3}[kind]
            text = _plain(b["runs"]).strip()
            # "01Giới thiệu & Bối cảnh" -> "01 · Giới thiệu & Bối cảnh"
            text = re.sub(r"^(\d{2})(?=[A-ZÀ-Ỹ])", r"\1 · ", text)
            if kind == "h2":
                doc.add_page_break()
            h = doc.add_heading(text, level=lvl)
            for r in h.runs:
                r.font.color.rgb = INK if lvl > 1 else ACCENT

        elif kind == "p":
            p = doc.add_paragraph()
            _add_runs(p, b["runs"])

        elif kind == "meta":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _add_runs(p, b["runs"], base_size=10, color=FAINT)

        elif kind == "stat":
            # "12" + "phân hệ nghiệp vụ (M0–M12)" → một dòng gạch đầu dòng gọn
            parts = [t.strip() for t, _ in b["runs"] if t.strip()]
            if len(parts) >= 2:
                p = doc.add_paragraph(style="List Bullet")
                r = p.add_run(parts[0] + " ")
                r.bold = True
                r.font.color.rgb = ACCENT
                r2 = p.add_run(" ".join(parts[1:]))
                r2.font.size = Pt(10)

        elif kind == "cap":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _add_runs(p, b["runs"], base_size=9, color=FAINT)
            for r in p.runs:
                r.italic = True

        elif kind == "li":
            p = doc.add_paragraph(style="List Bullet")
            _add_runs(p, b["runs"])

        elif kind == "note":
            color = NOTE_COLOR[b["note_kind"]]
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(14)
            p.paragraph_format.space_before = Pt(8)
            _add_runs(p, b["runs"], base_size=10)
            if p.runs:
                p.runs[0].bold = True
                p.runs[0].font.color.rgb = color

        elif kind == "pre":
            p = doc.add_paragraph()
            r = p.add_run(b["text"])
            r.font.name = "Consolas"
            r.font.size = Pt(9)

        elif kind == "diagram":
            p = doc.add_paragraph()
            r = p.add_run(b["text"])
            r.font.name = "Consolas"
            r.font.size = Pt(8.5)
            r.font.color.rgb = FAINT
            n = doc.add_paragraph()
            nr = n.add_run("(Sơ đồ mô tả bằng cú pháp mermaid — xem bản HTML để thấy sơ đồ đồ họa.)")
            nr.italic = True
            nr.font.size = Pt(8)
            nr.font.color.rgb = FAINT

        elif kind == "table":
            rows, head_rows = b["rows"], b["head_rows"]
            ncol = max(len(r) for r in rows)
            t = doc.add_table(rows=0, cols=ncol)
            t.style = "Table Grid"
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            for ri, row in enumerate(rows):
                cells = t.add_row().cells
                for ci in range(ncol):
                    cell = cells[ci]
                    cell.paragraphs[0].text = ""
                    par = cell.paragraphs[0]
                    runs = row[ci] if ci < len(row) else []
                    _add_runs(par, runs, base_size=9)
                    if ri < head_rows:
                        for r in par.runs:
                            r.bold = True
            doc.add_paragraph()

    return doc


def main() -> int:
    if not SRC.exists():
        sys.exit(f"Không tìm thấy {SRC}")
    parser = BAParser()
    parser.feed(SRC.read_text(encoding="utf-8"))
    doc = build(parser.blocks)
    doc.save(OUT)
    print(f"OK → {OUT}  ({OUT.stat().st_size // 1024} KB, {len(parser.blocks)} khối)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
