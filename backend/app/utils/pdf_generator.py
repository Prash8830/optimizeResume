import re


def generate_pdf(resume_text: str, role_title: str = "Resume") -> bytes:
    """Convert plain-text resume to ATS-safe PDF via WeasyPrint."""
    from weasyprint import HTML

    html = _resume_text_to_html(resume_text, role_title)
    return HTML(string=html).write_pdf()


def _resume_text_to_html(text: str, role_title: str) -> str:
    """Convert plain text resume (section-labeled) to clean HTML for PDF."""
    sections = _parse_sections(text)

    body_parts = []
    for section, content in sections.items():
        body_parts.append(f'<div class="section"><h2>{section}</h2>')
        for line in content:
            if line.strip():
                body_parts.append(f'<p>{line.strip()}</p>')
        body_parts.append("</div>")

    body_html = "\n".join(body_parts)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{
    font-family: Arial, sans-serif;
    font-size: 10pt;
    margin: 0.6in;
    color: #1a1a1a;
    line-height: 1.4;
  }}
  h1 {{
    font-size: 16pt;
    margin-bottom: 2px;
    color: #1a1a2e;
  }}
  h2 {{
    font-size: 11pt;
    font-weight: bold;
    text-transform: uppercase;
    border-bottom: 1px solid #ccc;
    padding-bottom: 2px;
    margin-top: 12px;
    margin-bottom: 4px;
    letter-spacing: 0.5px;
    color: #1a1a2e;
  }}
  p {{
    margin: 2px 0;
    font-size: 10pt;
  }}
  .section {{
    margin-bottom: 8px;
  }}
  @page {{
    size: A4;
    margin: 0.6in;
  }}
</style>
</head>
<body>
<h1>{role_title}</h1>
{body_html}
</body>
</html>"""


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
