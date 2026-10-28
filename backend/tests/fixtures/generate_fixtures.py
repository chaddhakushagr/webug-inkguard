"""
Deterministic fixture generator for document upload and accessibility testing.
Generates:
1. good.docx - Valid docx, correct heading order, alt text, descriptive link, table.
2. bad_a11y.docx - Missing alt text, heading skip (H1->H3), click here link, empty heading, low contrast run.
3. text.pdf - Valid text PDF with metadata title and paragraph content.
4. scanned.pdf - Scanned PDF (image only, 0 text chars).
5. corrupted.docx - Corrupted archive bytes.
6. renamed_exe.docx - Executable binary (MZ header) renamed to .docx.
7. oversize.docx - Valid DOCX exceeding 5 MB limit (5.3 MB).
8. zip_bomb.docx - Zip bomb DOCX (decompressed size > 25 MB).
"""

import os
import io
import zipfile
import docx
from docx.shared import RGBColor, Inches
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from PIL import Image
from fpdf import FPDF

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "documents"))


def create_sample_png(color="blue", size=(40, 40)) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_good_docx(path: str):
    doc = docx.Document()
    doc.add_heading("Lumo Botanical Daily Skincare Manual", level=1)
    
    p1 = doc.add_paragraph("Lumo offers grounded daily barrier support formulated with pure plant squalane and rosehip oil.")
    doc.add_heading("Morning Application Routine", level=2)
    
    # Add image with alt text
    p2 = doc.add_paragraph()
    r_img = p2.add_run()
    img_bytes = create_sample_png("green", (50, 50))
    r_img.add_picture(io.BytesIO(img_bytes), width=Inches(1.0))
    
    # Set alt text in wp:docPr
    for drawing in p2._p.xpath(".//w:drawing"):
        doc_prs = drawing.xpath(".//wp:docPr")
        if doc_prs:
            doc_prs[0].set("descr", "Lumo Botanical Hydrating Serum Bottle")
            doc_prs[0].set("title", "Hydrating Serum")

    # Add hyperlink with descriptive anchor text
    p3 = doc.add_paragraph("For full guidance, ")
    part = p3.part
    r_id = part.relate_to("https://lumo.skincare/catalogue", docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = parse_xml(f'<w:hyperlink {nsdecls("w", "r")} r:id="{r_id}"><w:r><w:t>explore our natural botanical skincare catalogue</w:t></w:r></w:hyperlink>')
    p3._p.append(hyperlink)

    # Add table
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Ingredient"
    table.cell(0, 1).text = "Origin"
    table.cell(1, 0).text = "Plant Squalane"
    table.cell(1, 1).text = "Olive Extract"

    doc.save(path)


def generate_bad_a11y_docx(path: str):
    doc = docx.Document()
    doc.add_heading("Lumo Accessibility Benchmark Document", level=1)
    
    # 1. Skipped heading level: H1 directly to H3 (RULE-A11Y-03)
    doc.add_heading("Skipped Subheading Level Three", level=3)

    # 2. Empty heading level 2 (RULE-A11Y-04)
    doc.add_heading("", level=2)

    # 3. Image without alt text (RULE-A11Y-02)
    p_img = doc.add_paragraph()
    r_img = p_img.add_run()
    img_bytes = create_sample_png("red", (40, 40))
    r_img.add_picture(io.BytesIO(img_bytes), width=Inches(1.0))
    # explicitly ensure descr is empty
    for drawing in p_img._p.xpath(".//w:drawing"):
        doc_prs = drawing.xpath(".//wp:docPr")
        if doc_prs:
            if "descr" in doc_prs[0].attrib:
                del doc_prs[0].attrib["descr"]
            if "title" in doc_prs[0].attrib:
                del doc_prs[0].attrib["title"]

    # 4. "Click here" link text (RULE-A11Y-01)
    p_link = doc.add_paragraph("To see ingredients, ")
    part = p_link.part
    r_id = part.relate_to("https://lumo.skincare/shop", docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = parse_xml(f'<w:hyperlink {nsdecls("w", "r")} r:id="{r_id}"><w:r><w:t>click here</w:t></w:r></w:hyperlink>')
    p_link._p.append(hyperlink)

    # 5. Low-contrast font run (< 4.5:1 WCAG ratio) (RULE-A11Y-05)
    p_contrast = doc.add_paragraph()
    r_low = p_contrast.add_run("This subtle caption text is rendered in very light grey on white.")
    r_low.font.color.rgb = RGBColor(220, 220, 220)  # ~1.38:1 contrast

    doc.save(path)


def generate_text_pdf(path: str):
    pdf = FPDF()
    pdf.set_title("Lumo Botanical Skincare Formulation Guide")
    pdf.add_page()
    pdf.set_font("helvetica", size=14)
    pdf.cell(text="Lumo Botanical Skincare Formulation Guide")
    pdf.ln(10)
    pdf.set_font("helvetica", size=11)
    pdf.multi_cell(
        w=0,
        text=(
            "Lumo creates pure plant-derived skincare routines designed for gentle daily barrier hydration. "
            "Our clean formulations feature cold-pressed rosehip seed extract and squalane."
        ),
    )
    pdf.output(path)


def generate_scanned_pdf(path: str):
    pdf = FPDF()
    pdf.add_page()
    # Insert an image without any text layer
    img_bytes = create_sample_png("purple", (200, 200))
    img_buf = io.BytesIO(img_bytes)
    pdf.image(img_buf, x=30, y=30, w=120)
    pdf.output(path)


def generate_corrupted_docx(path: str):
    # Starts with PK\x03\x04 but is truncated and filled with random invalid bytes
    corrupted_data = b"PK\x03\x04\x14\x00\x00\x00\x08\x00" + b"\xff\x00\xdeadbeef" * 20
    with open(path, "wb") as f:
        f.write(corrupted_data)


def generate_renamed_exe(path: str):
    # Standard DOS/Windows PE executable header
    exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00\xb8\x00\x00\x00" + (b"\x90" * 512)
    with open(path, "wb") as f:
        f.write(exe_bytes)


def generate_oversize_docx(path: str):
    # A valid docx file padded beyond 5 MB (5.3 MB)
    doc = docx.Document()
    doc.add_heading("Oversize Document Test", level=1)
    doc.add_paragraph("This document contains embedded high-resolution asset data exceeding 5 MB.")
    
    # Save base docx to memory
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)

    # Re-package with a large padded binary entry to exceed 5 MB cleanly
    oversize_buf = io.BytesIO()
    with zipfile.ZipFile(buf, "r") as zin:
        with zipfile.ZipFile(oversize_buf, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                zout.writestr(item, zin.read(item.filename))
            # Write 5.3 MB of uncompressible random/pseudo bytes
            padding = os.urandom(5_300_000)
            zout.writestr("word/media/large_asset.dat", padding)

    with open(path, "wb") as f:
        f.write(oversize_buf.getvalue())


def generate_zip_bomb_docx(path: str):
    # Zip bomb: decompressed size > 25 MB (e.g. 28 MB of zeroes compressed to ~30 KB)
    bomb_buf = io.BytesIO()
    with zipfile.ZipFile(bomb_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Standard DOCX minimal structure
        zf.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
        zf.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Zip Bomb</w:t></w:r></w:p></w:body></w:document>')
        # 28 MB of repetitive zeros compresses to ~28 KB (ratio ~1000:1)
        zf.writestr("word/media/huge_payload.dat", b"0" * (28 * 1024 * 1024))

    with open(path, "wb") as f:
        f.write(bomb_buf.getvalue())


def generate_all_fixtures():
    os.makedirs(FIXTURES_DIR, exist_ok=True)
    generate_good_docx(os.path.join(FIXTURES_DIR, "good.docx"))
    generate_bad_a11y_docx(os.path.join(FIXTURES_DIR, "bad_a11y.docx"))
    generate_text_pdf(os.path.join(FIXTURES_DIR, "text.pdf"))
    generate_scanned_pdf(os.path.join(FIXTURES_DIR, "scanned.pdf"))
    generate_corrupted_docx(os.path.join(FIXTURES_DIR, "corrupted.docx"))
    generate_renamed_exe(os.path.join(FIXTURES_DIR, "renamed_exe.docx"))
    generate_oversize_docx(os.path.join(FIXTURES_DIR, "oversize.docx"))
    generate_zip_bomb_docx(os.path.join(FIXTURES_DIR, "zip_bomb.docx"))
    print(f"All 8 fixtures successfully generated in {FIXTURES_DIR}")


if __name__ == "__main__":
    generate_all_fixtures()
