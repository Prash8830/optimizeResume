import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT


def generate_pdf(resume_text: str, role_title: str = "Resume") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    styles = getSampleStyleSheet()
    name_style = ParagraphStyle("name", fontSize=16, fontName="Helvetica-Bold", spaceAfter=4, textColor=colors.HexColor("#1a1a2e"))
    section_style = ParagraphStyle("section", fontSize=10, fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=2, textColor=colors.HexColor("#1a1a2e"), textTransform="uppercase")
    body_style = ParagraphStyle("body", fontSize=9, fontName="Helvetica", spaceAfter=2, leading=13, alignment=TA_LEFT)

    SECTION_HEADERS = {"SUMMARY", "EXPERIENCE", "PROJECTS", "TECHNICAL SKILLS", "SKILLS", "EDUCATION"}

    story = []
    story.append(Paragraph(role_title, name_style))
    story.append(Spacer(1, 4))

    sections = _parse_sections(resume_text)
    for section, lines in sections.items():
        if section != "OVERVIEW":
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=2))
            story.append(Paragraph(section, section_style))

        for line in lines:
            stripped = line.strip()
            if stripped:
                # Escape special XML characters for ReportLab
                safe = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(safe, body_style))

    doc.build(story)
    return buf.getvalue()


def _parse_sections(text: str) -> dict[str, list[str]]:
    SECTION_HEADERS = {"SUMMARY", "EXPERIENCE", "PROJECTS", "TECHNICAL SKILLS", "SKILLS", "EDUCATION"}
    sections: dict[str, list[str]] = {}
    current = "OVERVIEW"
    lines: list[str] = []

    for line in text.split("\n"):
        upper = line.strip().upper()
        if upper in SECTION_HEADERS:
            if lines:
                sections[current] = lines
            current = upper
            lines = []
        else:
            lines.append(line)

    if lines:
        sections[current] = lines
    return sections
