"""
PDF report generator.
Takes a person's numerology profile and AI interpretation, and produces
a polished, multi-page premium report — one dedicated page per life area.
"""

import re
from datetime import datetime
from fpdf import FPDF

# Brand palette (RGB)
PRIMARY = (88, 28, 135)          # deep purple
PRIMARY_LIGHT = (237, 225, 250)  # pale lavender background
ACCENT = (180, 140, 60)          # muted gold
TEXT_DARK = (35, 35, 40)
TEXT_MUTED = (110, 110, 120)
WHITE = (255, 255, 255)

# Order sections should appear in the report, with a short subtitle each
SECTION_ORDER = [
    ("Overview", "Your Numerology Snapshot"),
    ("Personality", "How You Show Up"),
    ("Strengths", "Your Natural Gifts"),
    ("Challenges", "Growth Edges"),
    ("Career", "Work & Purpose"),
    ("Love", "Romantic Connection"),
    ("Relationships", "Friends & Family"),
    ("Money", "Financial Mindset"),
    ("This Year's Theme", "Your Current Cycle"),
    ("Growth", "The Road Ahead"),
    ("Lucky Elements", "Traditional Associations"),
]


class NumerologyReportPDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return  # cover page has its own custom header
        self.set_fill_color(*PRIMARY)
        self.rect(0, 0, 210, 16, style="F")
        self.set_y(4)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*WHITE)
        self.cell(0, 8, "Numerology AI Insights", align="L")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 8, datetime.now().strftime("%B %d, %Y"), align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*TEXT_MUTED)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, text: str):
        self.ln(2)
        self.set_fill_color(*PRIMARY_LIGHT)
        self.set_text_color(*PRIMARY)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 9, f"  {text}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text: str, justify: bool = True):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(*TEXT_DARK)
        align = "J" if justify else "L"
        self.multi_cell(0, 6.3, text, align=align)
        self.ln(1)

    def page_header_banner(self, title: str, subtitle: str):
        """Large section-opening banner used at the top of each life-area page."""
        self.set_fill_color(*PRIMARY)
        self.rect(0, 16, 210, 26, style="F")
        self.set_xy(10, 22)
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*WHITE)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_x(10)
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, subtitle)
        self.set_y(50)


def _strip_markdown(text: str) -> str:
    """Removes markdown formatting characters for clean PDF text."""
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"^[-•]\s*", "", text, flags=re.MULTILINE)
    return text


def _clean_for_pdf(text: str) -> str:
    """Replaces characters fpdf2's default fonts can't render."""
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2026": "...",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _parse_sections(interpretation: str) -> dict:
    """Splits the AI interpretation (with ## headers) into a dict."""
    text = _clean_for_pdf(interpretation)
    parts = re.split(r"\n?##\s*", text)
    sections = {}
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.split("\n", 1)
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        sections[title] = body
    return sections


def generate_pdf_report(
    full_name: str,
    profile: dict,
    interpretation: str,
    pinnacles: dict = None,
    challenges: dict = None,
    karmic_lessons: list = None,
) -> bytes:
    """
    Builds a complete, premium multi-page PDF report — one dedicated page
    per life area — and returns it as bytes for a Streamlit download button.
    """
    sections = _parse_sections(interpretation)
    clean_name = _clean_for_pdf(full_name)

    pdf = NumerologyReportPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    labels = {
        "life_path_number": "Life Path",
        "expression_number": "Expression",
        "soul_urge_number": "Soul Urge",
        "personality_number": "Personality",
        "birthday_number": "Birthday",
        "personal_year_number": "Personal Year",
    }

    # ================= COVER PAGE =================
    pdf.add_page()
    pdf.set_fill_color(*PRIMARY)
    pdf.rect(0, 0, 210, 90, style="F")

    pdf.set_y(30)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 14, "NUMEROLOGY", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 14, "AI INSIGHTS", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.ln(2)
    pdf.cell(0, 8, "Complete Personal Numerology Report", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(105)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*TEXT_DARK)
    pdf.cell(0, 12, clean_name, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*TEXT_MUTED)
    pdf.cell(0, 8, f"Generated on {datetime.now().strftime('%B %d, %Y')}", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(15)
    keys = [k for k in profile.keys() if k in labels]
    box_w = 60
    box_h = 26
    row_gap = 6
    start_x = (210 - box_w * 3) / 2
    grid_top_y = pdf.get_y()
    for row in range(2):
        row_y = grid_top_y + row * (box_h + row_gap)
        for col in range(3):
            idx = row * 3 + col
            if idx >= len(keys):
                continue
            key = keys[idx]
            x = start_x + col * box_w
            pdf.set_fill_color(*PRIMARY_LIGHT)
            pdf.rect(x + 2, row_y, box_w - 4, box_h, style="F")
            pdf.set_xy(x + 2, row_y + 4)
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(*PRIMARY)
            pdf.cell(box_w - 4, 10, str(profile[key]), align="C")
            pdf.set_xy(x + 2, row_y + 16)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*TEXT_MUTED)
            pdf.cell(box_w - 4, 6, labels.get(key, key), align="C")
    pdf.set_y(grid_top_y + 2 * (box_h + row_gap) + 10)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*TEXT_MUTED)
    pdf.cell(0, 8, "A complete breakdown of your numbers begins on the next page.", align="C")

    # ================= CORE PROFILE PAGE =================
    pdf.add_page()
    pdf.section_title("Your Core Profile")
    for key, value in profile.items():
        if key not in labels:
            continue
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(*TEXT_DARK)
        pdf.cell(60, 7, labels.get(key, key))
        pdf.set_font("Helvetica", "", 10.5)
        pdf.set_text_color(*TEXT_DARK)
        pdf.cell(0, 7, str(value), new_x="LMARGIN", new_y="NEXT")
    if "maturity_number" in profile:
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(*TEXT_DARK)
        pdf.cell(60, 7, "Maturity Number")
        pdf.set_font("Helvetica", "", 10.5)
        pdf.cell(0, 7, str(profile["maturity_number"]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # ================= PINNACLES PAGE =================
    if pinnacles:
        pdf.add_page()
        pdf.section_title("Pinnacle Cycles")
        pdf.body_text(
            "Four life phases, each with a dominant theme to build on as you move "
            "through different chapters of life.",
            justify=False,
        )
        pin_labels = ["1st Pinnacle", "2nd Pinnacle", "3rd Pinnacle", "4th Pinnacle"]
        for i, (key, value) in enumerate(pinnacles.items()):
            pdf.set_font("Helvetica", "B", 10.5)
            pdf.set_text_color(*TEXT_DARK)
            pdf.cell(55, 8, pin_labels[i])
            pdf.set_font("Helvetica", "", 10.5)
            pdf.set_text_color(*TEXT_DARK)
            pdf.cell(0, 8, f"Number {value['number']}   (Ages {_clean_for_pdf(value['age_range'])})", new_x="LMARGIN", new_y="NEXT")

    # ================= CHALLENGES PAGE =================
    if challenges:
        pdf.add_page()
        pdf.section_title("Challenge Cycles")
        pdf.body_text(
            "Recurring lessons or obstacles across the same four life phases as "
            "the Pinnacles above.",
            justify=False,
        )
        chal_labels = ["1st Challenge", "2nd Challenge", "3rd Challenge", "4th Challenge"]
        for i, (key, value) in enumerate(challenges.items()):
            pdf.set_font("Helvetica", "B", 10.5)
            pdf.set_text_color(*TEXT_DARK)
            pdf.cell(55, 8, chal_labels[i])
            pdf.set_font("Helvetica", "", 10.5)
            pdf.set_text_color(*TEXT_DARK)
            pdf.cell(0, 8, f"Number {value['number']}   (Ages {_clean_for_pdf(value['age_range'])})", new_x="LMARGIN", new_y="NEXT")

    # ================= KARMIC LESSONS PAGE =================
    if karmic_lessons is not None:
        pdf.add_page()
        pdf.section_title("Karmic Lessons")
        if karmic_lessons:
            pdf.body_text(
                f"The following numbers are missing from the letters of your name, "
                f"suggesting traits that may need conscious development: "
                f"{', '.join(map(str, karmic_lessons))}.",
                justify=False,
            )
        else:
            pdf.body_text(
                "All numbers 1 through 9 are present in your name — you have no "
                "missing Karmic Lessons.",
                justify=False,
            )

    # ================= ONE DEDICATED PAGE PER LIFE AREA =================
    for section_name, subtitle in SECTION_ORDER:
        if section_name not in sections:
            continue
        pdf.add_page()
        pdf.page_header_banner(section_name.upper(), subtitle)
        body = _strip_markdown(sections[section_name])
        pdf.body_text(body, justify=True)

    # Include any AI-returned sections not in our expected order (fallback safety)
    known_names = {name for name, _ in SECTION_ORDER}
    for section_name, body in sections.items():
        if section_name not in known_names:
            pdf.add_page()
            pdf.page_header_banner(section_name.upper(), "")
            pdf.body_text(_strip_markdown(body), justify=True)

    # ================= CLOSING / DISCLAIMER PAGE =================
    pdf.add_page()
    pdf.set_fill_color(*PRIMARY)
    pdf.rect(0, 0, 210, 60, style="F")
    pdf.set_y(20)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 10, "Thank You", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, "This concludes your personal numerology report.", align="C")

    pdf.set_y(75)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*TEXT_MUTED)
    pdf.multi_cell(
        0, 6,
        "Numerology is an interpretive, reflective practice for self-discovery "
        "- not a scientific or predictive science, nor a substitute for "
        "professional medical, legal, or financial advice. The insights in "
        "this report are intended to support self-reflection and personal "
        "growth, not to serve as definitive statements about your life, "
        "relationships, or decisions."
    )

    return bytes(pdf.output())