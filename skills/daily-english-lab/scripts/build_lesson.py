#!/usr/bin/env python3
"""Build a beige English lesson with embedded fonts and auditable page renders.

Uses ReportLab's bundled Vera fonts by default. No font downloads, scheduler
changes, network access, or overwrite of existing lesson files are performed.
"""
import argparse
from datetime import date
from functools import partial
from io import BytesIO
import json
from pathlib import Path
import re
import sys
from xml.sax.saxutils import escape


def strings(blocks):
    for block in blocks:
        yield block["heading"]
        yield from block.get("paragraphs", [])
        yield from block.get("items", [])
        table = block.get("table")
        if table:
            yield from table["headers"]
            for row in table["rows"]:
                yield from row


def validate_input(data):
    date.fromisoformat(data["date"])
    for key in ("title", "topic", "level"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"{key} must be a nonempty string")
    total = data["total_minutes"]
    timing = data["timing"]
    if not isinstance(total, int) or total <= 0:
        raise ValueError("total_minutes must be a positive integer")
    if not timing or any(not isinstance(t["minutes"], int) or t["minutes"] <= 0 for t in timing):
        raise ValueError("Each timing entry needs positive integer minutes")
    if sum(t["minutes"] for t in timing) != total:
        raise ValueError("Timing entries do not add up to total_minutes")
    blocks = data["blocks"]
    if not isinstance(blocks, list) or not blocks:
        raise ValueError("blocks must contain the lesson")
    answers_started = False
    for block in blocks:
        if not isinstance(block.get("heading"), str) or not block["heading"].strip():
            raise ValueError("Each block needs a heading")
        if block.get("kind") == "answer-key":
            answers_started = True
        elif answers_started:
            raise ValueError("Answer-key blocks must come after all exercise blocks")
        for key in ("paragraphs", "items"):
            if not isinstance(block.get(key, []), list) or any(not isinstance(x, str) for x in block.get(key, [])):
                raise ValueError(f"{key} must be a list of strings")
        table = block.get("table")
        if table:
            n = len(table["headers"])
            if n < 1 or any(len(row) != n for row in table["rows"]):
                raise ValueError("Table rows must match header width")
        lines = block.get("answer_lines", 0)
        if not isinstance(lines, int) or not 0 <= lines <= 12:
            raise ValueError("answer_lines must be between 0 and 12")
    if not any(b.get("kind") == "reading" for b in blocks):
        raise ValueError("A reading block is required")
    if not answers_started:
        raise ValueError("An answer-key block is required")
    main_texts = [data["title"], data["topic"], data["level"], *strings(blocks)]
    main_texts.extend(t["label"] for t in timing)
    for source in data.get("sources", []):
        if not re.match(r"^https?://[^\s]+$", source["url"]):
            raise ValueError("Each source needs a valid HTTP(S) URL")
        date.fromisoformat(source["accessed"])
        main_texts.extend([source["title"], source["url"], source["accessed"]])
    for text in main_texts:
        if not isinstance(text, str):
            raise ValueError("All display content must be strings")
        if re.search(r"[\u2e80-\u9fff\uf900-\ufaff\U00020000-\U0003134f]", text):
            raise ValueError("The main lesson must be English; put Chinese in chinese_notes")
        if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text):
            raise ValueError("Display content contains control characters")
    return main_texts


def register_fonts(args, has_notes):
    import reportlab
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    font_dir = Path(reportlab.__file__).resolve().parent / "fonts"
    normal = Path(args.font) if args.font else font_dir / "Vera.ttf"
    bold = Path(args.bold_font) if args.bold_font else (normal if args.font else font_dir / "VeraBd.ttf")
    for name, path in (("LabRegular", normal), ("LabBold", bold)):
        if not path.is_file():
            raise ValueError(f"Font does not exist: {path}")
        pdfmetrics.registerFont(TTFont(name, str(path)))
    if has_notes:
        candidates = [Path(args.cjk_font)] if args.cjk_font else [
            Path("C:/Windows/Fonts/simhei.ttf"),
            Path("C:/Windows/Fonts/ARIALUNI.ttf"),
            Path("C:/Windows/Fonts/simsun.ttc"),
            Path("/usr/share/fonts/truetype/arphic/uming.ttc"),
            Path("/Library/Fonts/Arial Unicode.ttf"),
        ]
        errors = []
        for candidate in candidates:
            if not candidate.is_file():
                continue
            try:
                pdfmetrics.registerFont(TTFont("LabCJK", str(candidate)))
                break
            except Exception as exc:
                errors.append(f"{candidate}: {type(exc).__name__}")
        else:
            raise ValueError("Chinese notes need an embeddable TrueType CJK font. Use --cjk-font. " + "; ".join(errors))


def check_glyphs(texts, fonts):
    from reportlab.pdfbase import pdfmetrics
    for name in fonts:
        face = pdfmetrics.getFont(name).face
        missing = sorted({ord(c) for text in texts for c in text if not c.isspace() and not face.charToGlyph.get(ord(c))})
        if missing:
            raise ValueError(f"Missing glyphs in {name}: " + ", ".join(f"U+{code:04X}" for code in missing))


def markdown(data, blocks, is_notes=False):
    title = "Chinese notes" if is_notes else data["title"]
    lines = [f"# {title}", "", f"{data['date']} | {data['level']} | {data['total_minutes']} minutes", ""]
    if not is_notes:
        lines.extend([" | ".join(f"{t['label']}: {t['minutes']} min" for t in data["timing"]), ""])
    for block in blocks:
        lines.extend([f"## {block['heading']}", ""])
        for text in block.get("paragraphs", []):
            lines.extend([text, ""])
        for text in block.get("items", []):
            lines.extend([f"- {text}", ""])
        if block.get("table"):
            tab = block["table"]
            row = lambda cells: "| " + " | ".join(c.replace("|", "\\|").replace("\n", " ") for c in cells) + " |"
            lines.extend([row(tab["headers"]), row(["---"] * len(tab["headers"]))])
            lines.extend(row(r) for r in tab["rows"])
            lines.append("")
        if block.get("answer_lines"):
            lines.extend(["Response space:", "", "\n".join("____________________________" for _ in range(block["answer_lines"])), ""])
    if not is_notes:
        lines.extend(["## Sources", ""])
        for source in data.get("sources", []):
            lines.extend([f"- [{source['title']}]({source['url']}) (accessed {source['accessed']})", ""])
    return "\n".join(lines)


def create_pdf(path, data, blocks, background, is_notes=False):
    from reportlab.pdfgen import canvas
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle, PageBreak, HRFlowable, KeepTogether
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle

    regular = "LabCJK" if is_notes else "LabRegular"
    bold = "LabCJK" if is_notes else "LabBold"
    wrap = "CJK" if is_notes else None
    ink = colors.HexColor("#302F29")
    olive = colors.HexColor("#66755A")
    line = colors.HexColor("#D9CCB7")
    width = A4[0] - 90
    styles = {
        "title": ParagraphStyle("title", fontName=bold, fontSize=23, leading=29, textColor=ink, spaceAfter=13, wordWrap=wrap),
        "h": ParagraphStyle("h", fontName=bold, fontSize=13, leading=18, textColor=olive, spaceBefore=13, spaceAfter=8, keepWithNext=True, wordWrap=wrap),
        "body": ParagraphStyle("body", fontName=regular, fontSize=10.2, leading=15.7, textColor=ink, spaceAfter=8, wordWrap=wrap),
        "small": ParagraphStyle("small", fontName=regular, fontSize=8.1, leading=11.6, textColor=olive, spaceAfter=7, wordWrap=wrap),
        "cell": ParagraphStyle("cell", fontName=regular, fontSize=9, leading=13.3, textColor=ink, wordWrap=wrap),
        "cellhead": ParagraphStyle("cellhead", fontName=bold, fontSize=9, leading=13.3, textColor=ink, wordWrap=wrap),
    }
    def p(text, kind="body"):
        return Paragraph(escape(text).replace("\n", "<br/>"), styles[kind])
    printable = [data["date"], data["level"], str(data["total_minutes"]), "DAILY ENGLISH LAB", "Chinese notes"]
    printable.extend(strings(blocks))
    if not is_notes:
        printable.extend([data["title"], data["topic"]])
        printable.extend(t["label"] for t in data["timing"])
        for source in data.get("sources", []):
            printable.extend([source["title"], source["url"], source["accessed"]])
    check_glyphs(printable, [regular, bold])

    story = [p("Chinese notes" if is_notes else data["title"], "title")]
    story.append(p(f"{data['date']} | {data['level']} | {data['total_minutes']} minutes", "small"))
    if not is_notes:
        story.extend([p(f"Topic: {data['topic']}", "small"), p(" | ".join(f"{t['label']} {t['minutes']} min" for t in data["timing"]), "small")])
    for block in blocks:
        if block.get("break_before"):
            story.append(PageBreak())
        block_start = len(story)
        story.append(p(block["heading"], "h"))
        story.extend(p(text) for text in block.get("paragraphs", []))
        story.extend(p(f"- {text}") for text in block.get("items", []))
        if block.get("table"):
            tab = block["table"]
            cells = [[p(c, "cellhead") for c in tab["headers"]]]
            cells.extend([p(c, "cell") for c in row] for row in tab["rows"])
            n = len(tab["headers"])
            col_widths = ([width * .34, width * .66] if n == 2 else [width / n] * n)
            table = LongTable(cells, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#E5E7D8")),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#FBF6EC"), colors.HexColor(background)]),
                ("GRID", (0,0), (-1,-1), .4, line),
                ("LEFTPADDING", (0,0), (-1,-1), 7), ("RIGHTPADDING", (0,0), (-1,-1), 7),
                ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ]))
            story.extend([table, Spacer(1,9)])
        for _ in range(block.get("answer_lines", 0)):
            story.extend([Spacer(1,16), HRFlowable(width="100%", thickness=.4, color=line)])
        if block.get("keep_together"):
            story[block_start:] = [KeepTogether(story[block_start:])]
    if not is_notes and data.get("sources"):
        story.append(p("Sources", "h"))
        for source in data["sources"]:
            title = escape(source["title"])
            url = escape(source["url"], {'"': "&quot;"})
            story.append(Paragraph(f'<link href="{url}" color="#66755A"><u>{title}</u></link>', styles["small"]))
            story.append(p(f"Accessed {source['accessed']}", "small"))

    def page_frame(c, doc):
        c.saveState()
        c.setFillColor(colors.HexColor(background))
        c.rect(0,0,*A4,stroke=0,fill=1)
        c.setFont(regular, 8)
        c.setFillColor(olive)
        c.drawString(45,A4[1]-30,"DAILY ENGLISH LAB")
        c.drawRightString(A4[0]-45,27,f"{data['date']} | {doc.page}")
        c.setStrokeColor(line)
        c.setLineWidth(.45)
        c.line(45,A4[1]-37,A4[0]-45,A4[1]-37)
        c.line(45,40,A4[0]-45,40)
        c.restoreState()
    doc = SimpleDocTemplate(str(path),pagesize=A4,leftMargin=45,rightMargin=45,topMargin=57,bottomMargin=56,
        title="Chinese notes" if is_notes else data["title"],author="Daily English Lab")
    doc.build(story,onFirstPage=page_frame,onLaterPages=page_frame,canvasmaker=partial(canvas.Canvas,initialFontName=regular))
    # ReportLab can register an unused default Helvetica resource even when all
    # painted text uses TrueType. Remove only resources never selected anywhere.
    from pypdf import PdfReader, PdfWriter
    reader = PdfReader(path)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    used_ids = set()
    for page in writer.pages:
        fonts = page["/Resources"]["/Font"]
        active_id = None
        stack = []
        for operands, op in page.get_contents().operations:
            if op == b"q":
                stack.append(active_id)
            elif op == b"Q":
                active_id = stack.pop()
            if op == b"Tf":
                resource = fonts[str(operands[0])]
                reference = resource.indirect_reference
                active_id = reference.idnum
            elif op in (b"Tj",b"TJ",b"'",b'"'):
                used_ids.add(active_id)
    for page in writer.pages:
        fonts = page["/Resources"]["/Font"]
        content = page.get_contents()
        content.operations = [(a,o) for a,o in content.operations
            if not (o == b"Tf" and fonts[str(a[0])].indirect_reference.idnum not in used_ids)]
        page.replace_contents(content)
    for page in writer.pages:
        fonts = page["/Resources"]["/Font"]
        for key in list(fonts):
            if fonts[key].indirect_reference.idnum not in used_ids:
                del fonts[key]
    buffer = BytesIO()
    writer.write(buffer)
    path.write_bytes(buffer.getvalue())


def audit_pdf(path, blocks, page_dir):
    from pypdf import PdfReader
    import pypdfium2 as pdfium
    reader = PdfReader(path)
    fonts = []
    for page_no, page in enumerate(reader.pages,1):
        for resource, f in page["/Resources"]["/Font"].items():
            f = f.get_object()
            descendants = f.get("/DescendantFonts",[])
            leaves = [x.get_object() for x in descendants] if descendants else [f]
            for leaf in leaves:
                desc = leaf.get("/FontDescriptor")
                desc = desc.get_object() if desc else {}
                embedded = any(k in desc and len(desc[k].get_data())>0 for k in ("/FontFile","/FontFile2","/FontFile3"))
                if not embedded or not f.get("/ToUnicode"):
                    raise ValueError(f"Page {page_no}, {resource}: unembedded font or missing Unicode map")
            fonts.append({"page":page_no,"resource":str(resource),"name":str(f.get("/BaseFont")),"embedded":True,"to_unicode":True})
    normalized = lambda s: re.sub(r"\s+","",s)
    bodies = []
    for page in reader.pages:
        text = (page.extract_text() or "").replace("DAILY ENGLISH LAB", "")
        text = re.sub(r"(?m)^\d{4}-\d{2}-\d{2}\s*\|\s*\d+\s*$", "", text)
        bodies.append(text)
    all_text = normalized("\n".join(bodies))
    missing = [s[:80] for s in strings(blocks) if normalized(s) not in all_text]
    if missing:
        raise ValueError(f"Written text missing from PDF: {missing[:4]}")
    page_dir.mkdir(parents=True,exist_ok=True)
    doc = pdfium.PdfDocument(path)
    renders = []
    for i,page in enumerate(doc,1):
        image_path = page_dir / f"page-{i:02d}.png"
        bitmap = page.render(scale=1.6)
        bitmap.to_pil().save(image_path)
        renders.append(str(image_path.resolve()))
        bitmap.close();page.close()
    doc.close()
    return {"pdf":str(path.resolve()),"pages":len(reader.pages),"fonts":fonts,"text_complete":True,
        "missing_glyphs":[],"render_engine":"PDFium","rendered_pages":renders,"visual_review":"required_by_assistant"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",required=True,type=Path)
    parser.add_argument("--output-dir",required=True,type=Path)
    parser.add_argument("--stem")
    parser.add_argument("--font")
    parser.add_argument("--bold-font")
    parser.add_argument("--cjk-font")
    parser.add_argument("--background",default="#F5EBD9")
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8-sig"))
    validate_input(data)
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", args.background):
        raise ValueError("background must be a six-digit hex color")
    stem = args.stem or f"English_Lab_{data['date']}"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}", stem) or ".." in stem:
        raise ValueError("stem must be a plain filename without a path")
    args.output_dir.mkdir(parents=True,exist_ok=True)
    main_pdf = args.output_dir / f"{stem}.pdf"
    main_md = args.output_dir / f"{stem}.md"
    report_file = args.output_dir / f"{stem}-validation.json"
    page_root = args.output_dir / f"{stem}-pages"
    notes = data.get("chinese_notes", [])
    paths = [main_pdf,main_md,report_file,page_root]
    if notes:
        paths.extend(args.output_dir / f"{stem}-zh-notes{suffix}" for suffix in (".pdf",".md"))
    if any(p.exists() for p in paths):
        raise ValueError("Output already exists; use a different --stem or output directory")
    register_fonts(args,bool(notes))
    create_pdf(main_pdf,data,data["blocks"],args.background)
    main_md.write_text(markdown(data,data["blocks"]),encoding="utf-8")
    reports = [audit_pdf(main_pdf,data["blocks"],page_root/"main")]
    if notes:
        note_pdf = args.output_dir / f"{stem}-zh-notes.pdf"
        create_pdf(note_pdf,data,notes,args.background,is_notes=True)
        (args.output_dir/f"{stem}-zh-notes.md").write_text(markdown(data,notes,True),encoding="utf-8")
        reports.append(audit_pdf(note_pdf,notes,page_root/"zh-notes"))
    words = sum(len(re.findall(r"\b[\w]+(?:[-'][\w]+)*\b", " ".join(b.get("paragraphs",[]))))
        for b in data["blocks"] if b.get("kind")=="reading")
    result = {"status":"mechanical_checks_passed","date":data["date"],"reading_words":words,"background":args.background,
        "documents":reports,"visual_review":"Inspect every rendered page before delivering the PDF."}
    report_file.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"status":result["status"],"report":str(report_file.resolve()),"pages":[r["pages"] for r in reports],"reading_words":words},ensure_ascii=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError,KeyError,TypeError,FileNotFoundError,ImportError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        raise SystemExit(1)
