import io

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


def generate_docx(resume_text: str, role_title: str = "Resume") -> bytes:
    """Convert plain-text resume to ATS-safe DOCX."""
    doc = Document()

    # Remove default styles that confuse ATS
    _set_default_font(doc)

    # Title
    title = doc.add_heading(role_title, level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _style_heading(title, size=16, bold=True)

    sections = _parse_sections(resume_text)
    for section_name, lines in sections.items():
        # Section header
        heading = doc.add_heading(section_name, level=1)
        _style_heading(heading, size=11, bold=True, uppercase=True)

        for line in lines:
            if line.strip():
                para = doc.add_paragraph(line.strip())
                para.style.font.size = Pt(10)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _set_default_font(doc: Document) -> None:
    from docx.oxml.ns import qn
    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(10)


def _style_heading(heading, size: int, bold: bool = True, uppercase: bool = False) -> None:
    for run in heading.runs:
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = RGBColor(0x1a, 0x1a, 0x2e)
        if uppercase:
            run.text = run.text.upper()


def _parse_sections(text: str) -> dict[str, list[str]]:
    section_headers = ["SUMMARY", "EXPERIENCE", "PROJECTS", "TECHNICAL SKILLS", "SKILLS", "EDUCATION"]
    sections: dict[str, list[str]] = {}
    current_section = "OVERVIEW"
    current_lines: list[str] = []

    for line in text.split("\n"):
        upper = line.strip().upper()
        if upper in section_headers:
            if current_lines:
                sections[current_section] = current_lines
            current_section = upper
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections[current_section] = current_lines

    return sections
