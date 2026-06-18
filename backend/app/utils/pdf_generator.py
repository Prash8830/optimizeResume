import io
from copy import deepcopy

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer
from reportlab.platypus.frames import Frame
from reportlab.pdfgen.canvas import Canvas

DARK = colors.HexColor("#1a1a2e")
GRAY = colors.HexColor("#555555")
RULE = colors.HexColor("#cccccc")

PAGE_W, PAGE_H = A4
LM = RM = 0.6 * inch
TM = BM = 0.5 * inch
CONTENT_W = PAGE_W - LM - RM
CONTENT_H = PAGE_H - TM - BM

SECTION_HEADERS = {"SUMMARY", "EXPERIENCE", "PROJECTS", "TECHNICAL SKILLS", "SKILLS", "EDUCATION"}


def generate_pdf(resume_text: str, role_title: str = "Resume") -> bytes:
    sections = _parse_sections(resume_text)

    # Pass 1: measure with default spacing
    story = _build_story(sections, role_title, sp=1.0)
    used_h = _measure_height(story)

    # Compute multiplier so content fills ~95% of the page
    if used_h > 0:
        target = CONTENT_H * 0.96
        sp = min(2.2, max(0.55, target / used_h))
    else:
        sp = 1.0

    # Pass 2: rebuild with adjusted spacing and produce the PDF
    story = _build_story(sections, role_title, sp=sp)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=LM, rightMargin=RM,
        topMargin=TM, bottomMargin=BM,
    )
    doc.build(story)
    return buf.getvalue()


def _build_story(sections: dict, role_title: str, sp: float = 1.0) -> list:
    name_style = ParagraphStyle(
        "name", fontSize=18, fontName="Helvetica-Bold",
        spaceAfter=max(1, 2 * sp), textColor=DARK, alignment=TA_CENTER,
    )
    contact_style = ParagraphStyle(
        "contact", fontSize=8.5, fontName="Helvetica",
        spaceAfter=max(1, 4 * sp), textColor=GRAY, alignment=TA_CENTER,
        leading=max(10, 12 * sp),
    )
    section_style = ParagraphStyle(
        "section", fontSize=9.5, fontName="Helvetica-Bold",
        spaceBefore=max(2, 6 * sp), spaceAfter=max(1, 2 * sp), textColor=DARK,
    )
    role_line_style = ParagraphStyle(
        "role_line", fontSize=9.5, fontName="Helvetica-Bold",
        spaceAfter=max(1, 1 * sp), textColor=DARK,
    )
    body_style = ParagraphStyle(
        "body", fontSize=9, fontName="Helvetica",
        spaceAfter=max(1, 1.5 * sp), leading=max(11, 12 * sp),
        alignment=TA_LEFT, textColor=colors.black,
    )

    story = []

    # ── HEADER ────────────────────────────────────────────────────────────────
    header_lines = dict(sections).get("HEADER", [])
    if header_lines:
        name_line = next((l.strip() for l in header_lines if l.strip()), "")
        contact_line = next((l.strip() for l in header_lines[1:] if l.strip()), "")
        if name_line:
            story.append(Paragraph(_esc(name_line), name_style))
        if contact_line:
            story.append(Paragraph(_esc(contact_line), contact_style))
    else:
        story.append(Paragraph(_esc(role_title), name_style))

    story.append(HRFlowable(width="100%", thickness=1.0, color=DARK, spaceAfter=max(2, 4 * sp)))

    # ── BODY SECTIONS ─────────────────────────────────────────────────────────
    for section, lines in sections.items():
        if section in ("HEADER", "OVERVIEW"):
            continue

        story.append(Paragraph(section.upper(), section_style))
        story.append(HRFlowable(width="100%", thickness=0.4, color=RULE, spaceAfter=max(1, 2 * sp)))

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if (section == "EXPERIENCE"
                    and " at " in stripped
                    and not stripped[0].islower()
                    and len(stripped.split()) <= 12):
                story.append(Paragraph(_esc(stripped), role_line_style))
            else:
                story.append(Paragraph(_esc(stripped), body_style))

        story.append(Spacer(1, max(1, 3 * sp)))

    return story


def _measure_height(story: list) -> float:
    """Return total rendered height (points) of story on a virtual tall canvas."""
    tall_h = CONTENT_H * 8
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=(CONTENT_W + 100, tall_h + 100))
    frame = Frame(
        10, 10, CONTENT_W, tall_h,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        showBoundary=0,
    )
    frame.addFromList(deepcopy(story), c)
    c.save()
    # frame._y starts at (y1 + height) = 10 + tall_h; decreases as content is drawn
    return (10 + tall_h) - frame._y


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
