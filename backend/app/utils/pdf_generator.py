import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

DARK = colors.HexColor("#1a1a2e")
GRAY = colors.HexColor("#555555")
RULE = colors.HexColor("#cccccc")

SECTION_HEADERS = {"SUMMARY", "EXPERIENCE", "PROJECTS", "TECHNICAL SKILLS", "SKILLS", "EDUCATION"}


def generate_pdf(resume_text: str, role_title: str = "Resume") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    name_style = ParagraphStyle(
        "name", fontSize=18, fontName="Helvetica-Bold", spaceAfter=2,
        textColor=DARK, alignment=TA_CENTER,
    )
    contact_style = ParagraphStyle(
        "contact", fontSize=8.5, fontName="Helvetica", spaceAfter=4,
        textColor=GRAY, alignment=TA_CENTER, leading=12,
    )
    section_style = ParagraphStyle(
        "section", fontSize=9.5, fontName="Helvetica-Bold", spaceBefore=6,
        spaceAfter=2, textColor=DARK,
    )
    role_line_style = ParagraphStyle(
        "role_line", fontSize=9.5, fontName="Helvetica-Bold", spaceAfter=1,
        textColor=DARK,
    )
    body_style = ParagraphStyle(
        "body", fontSize=9, fontName="Helvetica", spaceAfter=1,
        leading=12, alignment=TA_LEFT, textColor=colors.black,
    )

    sections = _parse_sections(resume_text)
    story = []

    # ── HEADER (name + contact line) ────────────────────────────────────────
    header_lines = sections.pop("HEADER", [])
    if header_lines:
        name_line = next((l.strip() for l in header_lines if l.strip()), "")
        contact_line = next((l.strip() for l in header_lines[1:] if l.strip()), "")
        if name_line:
            story.append(Paragraph(_esc(name_line), name_style))
        if contact_line:
            story.append(Paragraph(_esc(contact_line), contact_style))
    else:
        story.append(Paragraph(_esc(role_title), name_style))

    story.append(HRFlowable(width="100%", thickness=1.0, color=DARK, spaceAfter=4))

    # ── BODY SECTIONS ───────────────────────────────────────────────────────
    for section, lines in sections.items():
        if section == "OVERVIEW":
            continue
        story.append(Paragraph(section.upper(), section_style))
        story.append(HRFlowable(width="100%", thickness=0.4, color=RULE, spaceAfter=2))

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            # Bold role/company lines in EXPERIENCE (format: "Role at Company")
            if section == "EXPERIENCE" and " at " in stripped and not stripped[0].islower():
                story.append(Paragraph(_esc(stripped), role_line_style))
            else:
                story.append(Paragraph(_esc(stripped), body_style))

        story.append(Spacer(1, 2))

    doc.build(story)
    return buf.getvalue()


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _parse_sections(text: str) -> dict[str, list[str]]:
    ALL_HEADERS = SECTION_HEADERS | {"HEADER"}
    sections: dict[str, list[str]] = {}
    current = "OVERVIEW"
    lines: list[str] = []

    for line in text.split("\n"):
        upper = line.strip().upper()
        if upper in ALL_HEADERS:
            if lines or current != "OVERVIEW":
                sections[current] = lines
            current = upper
            lines = []
        else:
            lines.append(line)

    if lines:
        sections[current] = lines
    return sections
