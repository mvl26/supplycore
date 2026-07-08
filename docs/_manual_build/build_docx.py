#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build SupplyCore_HuongDanSuDung_v1.0.docx by reusing AssetCore_HuongDanSuDung_v2.0.docx
as a STYLE TEMPLATE (styles.xml / numbering.xml / theme / headers / footers) and injecting
SupplyCore content assembled from a small line-based DSL.

DSL blocks (one per line; tab `\t` separates the type from the payload):
  H1 \t <num> \t <title>
  H2 \t <num> \t <title>
  H3 \t <num> \t <title>
  H4 \t <num> \t <title>
  FIRST \t <text>                 first paragraph after a heading (FirstParagraph style)
  BODY  \t <text>                 normal body paragraph (BodyText style)
  UL    \t <text>                 bullet item (Compact + bullet numId=1)
  OL    \t <text>                 ordered step (consecutive OL = one restarting list)
  NOTE  \t <text>                 green callout ("Gợi ý:" lead unless text starts with 'Lead: ')
  WARN  \t <text>                 red callout  ("Lưu ý:" lead unless text starts with 'Lead: ')
  IMG   \t <caption>             screenshot placeholder
  TABLE \t <col1>|<col2>|...      table header (next ROW lines are body rows)
  ROW   \t <c1>|<c2>|...          table body row

Inline: **bold** spans are rendered bold. Use `Lead: rest` inside NOTE/WARN to set a custom bold lead label.
Blank lines and lines beginning with '#' are ignored (comments).
"""
import zipfile, re, sys, os, glob, html, struct, json

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "img")
try:
    MANIFEST = json.load(open(os.path.join(IMG_DIR, "manifest.json"), encoding="utf-8"))
except Exception:
    MANIFEST = {}
EMBED_IMAGES = []   # {rid, media, path}
FIG = [0]
MAXW_EMU = 5760000  # ~6.3 in (content width)

def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])  # width, height at IHDR

def emu_dims(path):
    w, h = png_size(path)
    cx, cy = w * 9525, h * 9525  # px -> EMU at 96 dpi
    if cx > MAXW_EMU:
        cy = int(cy * MAXW_EMU / cx); cx = MAXW_EMU
    return cx, cy
DOCS = os.path.dirname(HERE)
TEMPLATE = os.path.join(DOCS, "AssetCore_HuongDanSuDung_v2.0.docx")
OUT = os.path.join(DOCS, "SupplyCore_HuongDanSuDung_v1.0.docx")
CONTENT_DIR = os.path.join(HERE, "content")

# ---- captured from template ----
COVER_BREAK_SECTPR = ('<w:sectPr w:rsidR="004B0341"><w:headerReference w:type="default" r:id="rId7"/>'
    '<w:footerReference w:type="default" r:id="rId8"/><w:pgSz w:w="12240" w:h="15840"/>'
    '<w:pgMar w:top="1440" w:right="1440" w:bottom="2250" w:left="1440" w:header="0" w:footer="1440" w:gutter="0"/>'
    '<w:cols w:space="720"/><w:formProt w:val="0"/><w:docGrid w:linePitch="100"/></w:sectPr>')
FINAL_SECTPR = ('<w:sectPr w:rsidR="004B0341"><w:headerReference w:type="default" r:id="rId174"/>'
    '<w:footerReference w:type="default" r:id="rId175"/><w:pgSz w:w="12240" w:h="15840"/>'
    '<w:pgMar w:top="1440" w:right="1440" w:bottom="2250" w:left="1440" w:header="0" w:footer="1440" w:gutter="0"/>'
    '<w:pgNumType w:start="1"/><w:cols w:space="720"/><w:formProt w:val="0"/><w:docGrid w:linePitch="100"/></w:sectPr>')

ordered_list_counter = [600]  # numIds we add to numbering.xml, all -> abstractNumId 9 (decimal)
used_ordered_numids = []

def esc(s):
    return html.escape(s, quote=False)

def runs(text, base_rpr=""):
    """Render text with **bold** spans into a sequence of <w:r>."""
    out = []
    parts = re.split(r'(\*\*.*?\*\*)', text)
    for p in parts:
        if not p:
            continue
        if p.startswith('**') and p.endswith('**') and len(p) >= 4:
            inner = p[2:-2]
            rpr = '<w:rPr>' + base_rpr + '<w:b/><w:bCs/></w:rPr>'
            out.append('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, esc(inner)))
        else:
            rpr = ('<w:rPr>' + base_rpr + '</w:rPr>') if base_rpr else ''
            out.append('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, esc(p)))
    return ''.join(out)

def p_heading(level, num, title):
    style = "Heading%d" % level
    return ('<w:p><w:pPr><w:pStyle w:val="%s"/></w:pPr>'
            '<w:r><w:rPr><w:rStyle w:val="SectionNumber"/></w:rPr><w:t xml:space="preserve">%s</w:t></w:r>'
            '<w:r><w:tab/><w:t xml:space="preserve">%s</w:t></w:r></w:p>'
            % (style, esc(num), esc(title)))

def p_styled(style, text):
    ppr = ('<w:pPr><w:pStyle w:val="%s"/></w:pPr>' % style) if style else '<w:pPr/>'
    return '<w:p>%s%s</w:p>' % (ppr, runs(text))

def p_bullet(text):
    return ('<w:p><w:pPr><w:pStyle w:val="Compact"/>'
            '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr>%s</w:p>'
            % runs(text))

def p_ordered(text, numid):
    return ('<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="%d"/></w:numPr></w:pPr>%s</w:p>'
            % (numid, runs(text)))

def p_callout(text, color, fill, default_lead):
    # split optional custom lead: "Lead: rest"
    m = re.match(r'^([^:]{1,40}):\s+(.*)$', text, re.S)
    if m:
        lead, rest = m.group(1) + ':', ' ' + m.group(2)
    else:
        lead, rest = default_lead, ' ' + text
    pbdr = ('<w:pBdr><w:top w:val="single" w:sz="4" w:space="6" w:color="%s"/>'
            '<w:left w:val="single" w:sz="30" w:space="6" w:color="%s"/>'
            '<w:bottom w:val="single" w:sz="4" w:space="6" w:color="%s"/>'
            '<w:right w:val="single" w:sz="4" w:space="6" w:color="%s"/></w:pBdr>'
            % (color, color, color, color))
    ppr = ('<w:pPr><w:pStyle w:val="BlockText"/>%s<w:shd w:val="clear" w:color="auto" w:fill="%s"/>'
           '<w:spacing w:before="120" w:after="120"/><w:ind w:left="200" w:right="80"/></w:pPr>'
           % (pbdr, fill))
    lead_run = ('<w:r><w:rPr><w:b/><w:bCs/><w:color w:val="%s"/></w:rPr><w:t xml:space="preserve">%s</w:t></w:r>'
                % (color, esc(lead)))
    return '<w:p>%s%s%s</w:p>' % (ppr, lead_run, runs(rest))

def p_image(caption):
    pbdr = ('<w:pBdr><w:top w:val="dashed" w:sz="6" w:space="6" w:color="9AA7B4"/>'
            '<w:left w:val="dashed" w:sz="6" w:space="6" w:color="9AA7B4"/>'
            '<w:bottom w:val="dashed" w:sz="6" w:space="6" w:color="9AA7B4"/>'
            '<w:right w:val="dashed" w:sz="6" w:space="6" w:color="9AA7B4"/></w:pBdr>')
    ppr = ('<w:pPr>%s<w:shd w:val="clear" w:color="auto" w:fill="F4F6F8"/>'
           '<w:spacing w:before="80" w:after="80"/><w:jc w:val="center"/></w:pPr>' % pbdr)
    r = ('<w:r><w:rPr><w:i/><w:iCs/><w:color w:val="5D6D7E"/><w:sz w:val="18"/></w:rPr>'
         '<w:t xml:space="preserve">%s</w:t></w:r>' % esc('[ẢNH MÀN HÌNH] ' + caption))
    return '<w:p>%s%s</w:p>' % (ppr, r)

def p_image_embed(caption, imgfile):
    path = os.path.join(IMG_DIR, imgfile)
    cx, cy = emu_dims(path)
    idx = len(EMBED_IMAGES) + 1
    rid = "rIdimg%d" % idx
    media = "manual_%03d.png" % idx
    EMBED_IMAGES.append({"rid": rid, "media": media, "path": path})
    FIG[0] += 1
    A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    P = 'http://schemas.openxmlformats.org/drawingml/2006/picture'
    drawing = (
        '<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
        '<wp:extent cx="%d" cy="%d"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
        '<wp:docPr id="%d" name="Picture %d"/>'
        '<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="%s" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        '<a:graphic xmlns:a="%s"><a:graphicData uri="%s">'
        '<pic:pic xmlns:pic="%s"><pic:nvPicPr><pic:cNvPr id="%d" name="Picture %d"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing>'
        % (cx, cy, idx, idx, A, A, P, P, idx, idx, rid, cx, cy))
    img_p = ('<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="40"/></w:pPr>'
             '<w:r>%s</w:r></w:p>' % drawing)
    cap_p = ('<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="0" w:after="200"/></w:pPr>'
             '<w:r><w:rPr><w:i/><w:iCs/><w:color w:val="5D6D7E"/><w:sz w:val="18"/></w:rPr>'
             '<w:t xml:space="preserve">%s</w:t></w:r></w:p>'
             % esc("Hình %d. %s" % (FIG[0], caption)))
    return img_p + cap_p

def cell(text, header=False):
    if header:
        rpr = '<w:rPr><w:b/><w:bCs/><w:color w:val="FFFFFF"/></w:rPr>'
        shd = '<w:shd w:val="clear" w:color="auto" w:fill="0F4761"/>'
        run = '<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, esc(text))
    else:
        shd = ''
        run = runs(text)
    tcpr = '<w:tcPr>%s</w:tcPr>' % shd
    return ('<w:tc>%s<w:p><w:pPr><w:pStyle w:val="Compact"/><w:spacing w:after="36"/></w:pPr>%s</w:p></w:tc>'
            % (tcpr, run))

def build_table(headers, rows):
    ncol = len(headers)
    total = 9000
    w = total // ncol
    grid = ''.join('<w:gridCol w:w="%d"/>' % w for _ in range(ncol))
    borders = ('<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="BFD3E0"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="BFD3E0"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="BFD3E0"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="BFD3E0"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="BFD3E0"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="BFD3E0"/></w:tblBorders>')
    tblpr = ('<w:tblPr><w:tblStyle w:val="Table"/><w:tblW w:w="%d" w:type="dxa"/>'
             '<w:tblInd w:w="0" w:type="dxa"/>%s<w:tblLayout w:type="fixed"/>'
             '<w:tblLook w:val="0020" w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="0" w:noVBand="0"/></w:tblPr>'
             % (total, borders))
    hdr_cells = ''.join(cell(h, header=True) for h in headers)
    hdr_row = '<w:tr><w:trPr><w:tblHeader/></w:trPr>%s</w:tr>' % hdr_cells
    body_rows = ''
    for r in rows:
        r = (r + [''] * ncol)[:ncol]
        body_rows += '<w:tr>%s</w:tr>' % ''.join(cell(c) for c in r)
    return '<w:tbl>%s<w:tblGrid>%s</w:tblGrid>%s%s</w:tbl>' % (tblpr, grid, hdr_row, body_rows)

def parse_dsl(text):
    """Return list of XML strings (paragraphs/tables)."""
    out = []
    lines = text.split('\n')
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        line = raw.rstrip('\r')
        if not line.strip() or line.lstrip().startswith('#'):
            i += 1
            continue
        if '\t' in line:
            typ, payload = line.split('\t', 1)
        else:
            typ, payload = line, ''
        typ = typ.strip()
        if typ in ('H1', 'H2', 'H3', 'H4'):
            parts = payload.split('\t')
            num = parts[0].strip() if parts else ''
            title = parts[1].strip() if len(parts) > 1 else ''
            out.append(p_heading(int(typ[1]), num, title))
            i += 1
        elif typ == 'FIRST':
            out.append(p_styled('FirstParagraph', payload)); i += 1
        elif typ == 'BODY':
            out.append(p_styled('BodyText', payload)); i += 1
        elif typ == 'UL':
            out.append(p_bullet(payload)); i += 1
        elif typ == 'OL':
            # gather consecutive OL into one restarting list
            numid = ordered_list_counter[0]; ordered_list_counter[0] += 1
            used_ordered_numids.append(numid)
            while i < n:
                l2 = lines[i].rstrip('\r')
                if l2.split('\t', 1)[0].strip() == 'OL':
                    p = l2.split('\t', 1)[1] if '\t' in l2 else ''
                    out.append(p_ordered(p, numid)); i += 1
                else:
                    break
        elif typ == 'NOTE':
            out.append(p_callout(payload, '1E8449', 'EAF7EF', 'Gợi ý:')); i += 1
        elif typ == 'WARN':
            out.append(p_callout(payload, 'C0392B', 'FDEDEC', 'Lưu ý:')); i += 1
        elif typ == 'IMG':
            img = MANIFEST.get(payload)
            if img and os.path.exists(os.path.join(IMG_DIR, img)):
                out.append(p_image_embed(payload, img))
            else:
                out.append(p_image(payload))
            i += 1
        elif typ == 'TABLE':
            headers = [c.strip() for c in payload.split('|')]
            rows = []
            i += 1
            while i < n:
                l2 = lines[i].rstrip('\r')
                if l2.split('\t', 1)[0].strip() == 'ROW':
                    pay = l2.split('\t', 1)[1] if '\t' in l2 else ''
                    rows.append([c.strip() for c in pay.split('|')]); i += 1
                else:
                    break
            out.append(build_table(headers, rows))
        else:
            # treat unknown as body text
            out.append(p_styled('BodyText', line)); i += 1
    return out

def cover_xml():
    def centered(run_xml, before="0", after="0", extra_ppr=""):
        return ('<w:p><w:pPr><w:spacing w:before="%s" w:after="%s"/><w:jc w:val="center"/>%s</w:pPr>%s</w:p>'
                % (before, after, extra_ppr, run_xml))
    def run(text, sz, color, caps=False, spacing=None, bold=True):
        rpr = '<w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>'
        if bold: rpr += '<w:b/><w:bCs/>'
        if caps: rpr += '<w:caps/>'
        rpr += '<w:color w:val="%s"/>' % color
        if spacing: rpr += '<w:spacing w:val="%d"/>' % spacing
        rpr += '<w:sz w:val="%d"/><w:szCs w:val="%d"/></w:rPr>' % (sz, sz)
        return '<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, esc(text))
    parts = []
    # spacers
    for _ in range(3):
        parts.append('<w:p><w:pPr><w:spacing w:after="0"/></w:pPr></w:p>')
    # top blue rule
    parts.append('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="24" w:space="8" w:color="2E8BC0"/></w:pBdr>'
                 '<w:spacing w:after="0"/><w:jc w:val="center"/></w:pPr></w:p>')
    parts.append(centered(run('SupplyCore', 108, '0F4761'), before="240", after="60"))
    parts.append(centered(run('HỆ THỐNG QUẢN LÝ VẬT TƯ & CUNG ỨNG Y TẾ', 24, '14689E', caps=True, spacing=30), after="40"))
    parts.append(centered(run('HƯỚNG DẪN SỬ DỤNG', 36, '2E75B6', caps=True, spacing=20), before="120", after="200"))
    # lower blue rule
    parts.append('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="12" w:space="8" w:color="2E8BC0"/></w:pBdr>'
                 '<w:spacing w:after="200"/><w:jc w:val="center"/></w:pPr></w:p>')
    parts.append(centered(run('Tài liệu hướng dẫn dành cho người dùng', 24, '5D6D7E', bold=False), before="240", after="40"))
    parts.append(centered(run('Phiên bản 1.0', 24, '5D6D7E', bold=False), after="40"))
    parts.append(centered(run('Tháng 6 năm 2026', 24, '5D6D7E', bold=False), after="40"))
    # final cover paragraph carries the section break
    parts.append('<w:p><w:pPr><w:spacing w:after="0"/>%s</w:pPr></w:p>' % COVER_BREAK_SECTPR)
    return ''.join(parts)

def toc_xml():
    out = []
    out.append('<w:p><w:pPr><w:pStyle w:val="TOCHeading"/></w:pPr><w:r><w:t>Mục lục</w:t></w:r></w:p>')
    out.append('<w:p><w:pPr><w:pStyle w:val="TOC1"/></w:pPr>'
               '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
               '<w:r><w:instrText xml:space="preserve"> TOC \\o "1-3" \\h \\z \\u </w:instrText></w:r>'
               '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
               '<w:r><w:rPr><w:i/><w:iCs/><w:color w:val="5D6D7E"/></w:rPr>'
               '<w:t xml:space="preserve">Nhấn chuột phải vào dòng này rồi chọn “Update Field / Cập nhật trường” để tạo Mục lục.</w:t></w:r>'
               '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')
    out.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
    return ''.join(out)

def make_numbering(orig):
    add = ''.join('<w:num w:numId="%d"><w:abstractNumId w:val="9"/></w:num>' % nid
                  for nid in used_ordered_numids)
    return orig.replace('</w:numbering>', add + '</w:numbering>')

def main():
    # collect content
    files = sorted(glob.glob(os.path.join(CONTENT_DIR, '*.dsl')))
    if not files:
        print('No .dsl content files found in', CONTENT_DIR); sys.exit(1)
    body_blocks = []
    for f in files:
        with open(f, encoding='utf-8') as fh:
            body_blocks.extend(parse_dsl(fh.read()))
    content_xml = ''.join(body_blocks)

    zin = zipfile.ZipFile(TEMPLATE, 'r')
    orig_doc = zin.read('word/document.xml').decode('utf-8')
    root_open = orig_doc[:orig_doc.find('<w:body>') + len('<w:body>')]
    new_doc = root_open + cover_xml() + toc_xml() + content_xml + FINAL_SECTPR + '</w:body></w:document>'

    orig_numbering = zin.read('word/numbering.xml').decode('utf-8')
    new_numbering = make_numbering(orig_numbering)

    header2 = zin.read('word/header2.xml').decode('utf-8')
    header2 = header2.replace('AssetCore', 'SupplyCore')

    core = zin.read('docProps/core.xml').decode('utf-8')
    core = re.sub(r'<dc:title>.*?</dc:title>', '<dc:title>SupplyCore — Hướng dẫn sử dụng (v1.0)</dc:title>', core)

    replaced = {
        'word/document.xml': new_doc.encode('utf-8'),
        'word/numbering.xml': new_numbering.encode('utf-8'),
        'word/header2.xml': header2.encode('utf-8'),
        'docProps/core.xml': core.encode('utf-8'),
    }

    # drop body media images (keep header/footer media) to slim the file, fix rels
    rels = zin.read('word/_rels/document.xml.rels').decode('utf-8')
    # find which rIds are still referenced in new_doc (rId7,rId8,rId174,rId175 from sectPr)
    used_rids = set(re.findall(r'r:id="(rId\d+)"', new_doc))
    # keep only rels whose Id is used OR which are not image targets (styles, numbering, header, footer, theme, fontTable, settings)
    def keep_rel(m):
        rid = m.group('id'); target = m.group('target')
        if 'media/' in target:
            return rid in used_rids
        return True
    new_rels_parts = []
    for m in re.finditer(r'<Relationship\b[^>]*Id="(?P<id>[^"]+)"[^>]*Target="(?P<target>[^"]+)"[^>]*/>', rels):
        if keep_rel(m):
            new_rels_parts.append(m.group(0))
    # add relationships for embedded manual screenshots
    for im in EMBED_IMAGES:
        new_rels_parts.append(
            '<Relationship Id="%s" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/%s"/>'
            % (im['rid'], im['media']))
    new_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + ''.join(new_rels_parts) + '</Relationships>'
    replaced['word/_rels/document.xml.rels'] = new_rels.encode('utf-8')

    # ensure png is declared in [Content_Types].xml
    ctypes = zin.read('[Content_Types].xml').decode('utf-8')
    if 'Extension="png"' not in ctypes:
        ctypes = ctypes.replace('</Types>',
            '<Default Extension="png" ContentType="image/png"/></Types>')
        replaced['[Content_Types].xml'] = ctypes.encode('utf-8')

    # which media files are still referenced anywhere (header/footer rels + kept doc rels)
    keep_media = set()
    for relname in ['word/_rels/document.xml.rels', 'word/_rels/header1.xml.rels',
                    'word/_rels/header2.xml.rels', 'word/_rels/footer1.xml.rels',
                    'word/_rels/footer2.xml.rels']:
        try:
            rr = replaced.get(relname)
            rr = rr.decode('utf-8') if rr else zin.read(relname).decode('utf-8')
        except KeyError:
            continue
        for t in re.findall(r'Target="([^"]+)"', rr):
            if 'media/' in t:
                keep_media.add('word/' + t.replace('../', '').lstrip('/') if not t.startswith('media') else 'word/' + t)
                keep_media.add('word/' + t.lstrip('/'))

    zout = zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        name = item.filename
        if name.startswith('word/media/'):
            if name not in keep_media:
                continue
        data = replaced.get(name, zin.read(name))
        zout.writestr(item, data)
    # write embedded screenshot media
    for im in EMBED_IMAGES:
        with open(im['path'], 'rb') as fh:
            zout.writestr('word/media/%s' % im['media'], fh.read())
    zout.close()
    zin.close()
    size = os.path.getsize(OUT)
    print('Wrote', OUT, '(%.1f KB)' % (size / 1024.0))
    print('Content paragraphs/tables:', len(body_blocks), '| ordered lists:', len(used_ordered_numids),
          '| embedded screenshots:', len(EMBED_IMAGES))

if __name__ == '__main__':
    main()
