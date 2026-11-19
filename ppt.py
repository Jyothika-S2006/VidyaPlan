import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ==========================================================
# IBM CARBON-INSPIRED THEME PALETTE
# ==========================================================
WHITE         = RGBColor(0xFF, 0xFF, 0xFF)
BG_COOL       = RGBColor(0xF7, 0xF9, 0xFC)
SURFACE_GRAY  = RGBColor(0xF4, 0xF4, 0xF4)
BORDER_GRAY   = RGBColor(0xE0, 0xE0, 0xE0)

IBM_BLUE      = RGBColor(0x0F, 0x62, 0xFE)   # Primary IBM Blue 60
IBM_NAVY      = RGBColor(0x00, 0x2D, 0x9C)   # Deep IBM Blue 80
IBM_BLUE_DARK = RGBColor(0x00, 0x1D, 0x6C)   # IBM Blue 90
IBM_BLUE_10   = RGBColor(0xED, 0xF5, 0xFF)   # Soft Blue Tint

IBM_CYAN      = RGBColor(0x11, 0x92, 0xE8)
IBM_TEAL      = RGBColor(0x00, 0x7D, 0x79)
IBM_TEAL_10   = RGBColor(0xD9, 0xFB, 0xFB)
IBM_GREEN     = RGBColor(0x19, 0x80, 0x38)
IBM_GREEN_10  = RGBColor(0xDE, 0xFB, 0xE6)
IBM_PURPLE    = RGBColor(0x69, 0x29, 0xC4)
IBM_PURPLE_10 = RGBColor(0xF6, 0xF2, 0xFF)
IBM_RED       = RGBColor(0xDA, 0x1E, 0x28)
IBM_RED_10    = RGBColor(0xFF, 0xF1, 0xF1)
IBM_AMBER     = RGBColor(0xB2, 0x86, 0x00)
IBM_AMBER_10  = RGBColor(0xFF, 0xF8, 0xE1)

TEXT_PRIMARY  = RGBColor(0x16, 0x16, 0x16)   # Carbon Gray 100
TEXT_SECOND   = RGBColor(0x52, 0x52, 0x52)   # Carbon Gray 70
TEXT_MUTED    = RGBColor(0x6F, 0x6F, 0x6F)   # Carbon Gray 60

FONT = "Calibri"


def set_bg(slide, color=WHITE):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_rect(slide, x, y, w, h, fill_c, border_c=None, rounded=True, radius=0.05, line_w=1.0):
    stype = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(stype, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.shadow.inherit = False
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill_c
    if border_c:
        shp.line.color.rgb = border_c
        shp.line.width = Pt(line_w)
    else:
        shp.line.fill.background()
    if rounded:
        try:
            shp.adjustments[0] = radius
        except Exception:
            pass
    return shp


def add_text(
    slide, x, y, w, h, text, size=13, bold=False, italic=False,
    color=TEXT_PRIMARY, align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP
):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = valign
    tf.margin_left = Inches(0.04)
    tf.margin_right = Inches(0.04)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.name = FONT
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    return tb


def add_pill(slide, x, y, w, h, text, fill_c, text_c, size=10.5, border_c=None):
    shp = add_rect(slide, x, y, w, h, fill_c, border_c=border_c, rounded=True, radius=0.45) if border_c else add_rect(slide, x, y, w, h, fill_c, rounded=True, radius=0.45)
    tf = shp.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.04)
    tf.margin_right = Inches(0.04)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    r.font.name = FONT
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = text_c
    return shp


def add_header_footer(slide, eyebrow, title, subtitle, slide_num):
    set_bg(slide, WHITE)
    # Top IBM Blue Strip
    add_rect(slide, 0, 0, 13.333, 0.08, IBM_BLUE, rounded=False)
    add_text(slide, 0.60, 0.22, 9.5, 0.24, eyebrow.upper(), size=10.5, bold=True, color=IBM_BLUE)
    add_text(slide, 0.60, 0.45, 12.1, 0.48, title, size=24, bold=True, color=TEXT_PRIMARY)
    if subtitle:
        add_text(slide, 0.60, 0.94, 12.1, 0.34, subtitle, size=13, color=TEXT_SECOND)

    # Clean Footer
    add_rect(slide, 0.60, 6.98, 12.133, 0.012, BORDER_GRAY, rounded=False)
    add_text(
        slide, 0.60, 7.04, 9.5, 0.28,
        "VIDYAPLAN   |   PROBLEM STATEMENT 17   |   TEAM INNOV8_LABS   |   SAMBHRAM INSTITUTE OF TECHNOLOGY",
        size=9, bold=True, color=TEXT_MUTED
    )
    add_text(
        slide, 11.7, 7.04, 1.033, 0.28,
        f"{slide_num:02d} / 07", size=9.5, bold=True, color=IBM_BLUE, align=PP_ALIGN.RIGHT
    )


def style_cell(cell, text, size=11, bold=False, color=TEXT_PRIMARY, fill_c=None, align=PP_ALIGN.LEFT):
    if fill_c:
        cell.fill.solid()
        cell.fill.fore_color.rgb = fill_c
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    cell.margin_left = Inches(0.10)
    cell.margin_right = Inches(0.08)
    cell.margin_top = Inches(0.04)
    cell.margin_bottom = Inches(0.04)
    tf = cell.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.name = FONT
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color


def build_ibm_pitch_deck(output_path="VidyaPlan_IBM_Pitch_7Slides.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # ==========================================================
    # SLIDE 1: TITLE & PROJECT INTRODUCTION
    # ==========================================================
    s1 = prs.slides.add_slide(blank)
    set_bg(s1, WHITE)
    # Left IBM Blue Accent Pillar & Top Bar
    add_rect(s1, 0, 0, 13.333, 0.08, IBM_BLUE, rounded=False)
    add_rect(s1, 0, 0.08, 0.20, 7.42, IBM_NAVY, rounded=False)

    # Eyebrow Pill
    add_pill(
        s1, 0.70, 0.65, 5.25, 0.38,
        "PROBLEM STATEMENT 17  •  INTER-INSTITUTE IBM BOB HACKATHON",
        IBM_BLUE_10, IBM_BLUE, size=10, border_c=IBM_BLUE
    )

    add_text(s1, 0.70, 1.25, 5.8, 0.85, "VIDYAPLAN", size=46, bold=True, color=TEXT_PRIMARY)
    add_text(
        s1, 0.70, 2.15, 5.8, 0.85,
        "Intelligent, Evidence-Driven School Infrastructure Planning",
        size=20, bold=False, color=IBM_BLUE
    )
    add_rect(s1, 0.70, 3.12, 1.35, 0.05, IBM_BLUE, rounded=False)

    # Team & Presenter Details Card
    add_rect(s1, 0.70, 3.42, 5.75, 2.55, BG_COOL, border_c=BORDER_GRAY, rounded=True, radius=0.05)
    add_rect(s1, 0.70, 3.42, 0.08, 2.55, IBM_BLUE, rounded=False)

    team_rows = [
        ("Team:", "Innov8_Labs"),
        ("Institute:", "Sambhram Institute of Technology"),
        ("Presented by:", "Jyothika S. & Aimanaz Sarwad"),
        ("Scope:", "40 Karnataka Schools  •  Library, Electricity & Computers"),
    ]
    for idx, (lbl, val) in enumerate(team_rows):
        ry = 3.62 + idx * 0.56
        add_text(s1, 0.95, ry, 1.50, 0.36, lbl, size=12, bold=True, color=IBM_NAVY)
        add_text(s1, 2.45, ry, 3.85, 0.36, val, size=12.5, bold=(idx < 3), color=TEXT_PRIMARY)

    add_text(
        s1, 0.70, 6.22, 5.8, 0.35,
        "Built with IBM Bob  •  IBM Granite (watsonx.ai)  •  OR-Tools CP-SAT  •  FastAPI  •  React",
        size=11, bold=True, color=TEXT_MUTED
    )

    # Right Side: Dashboard Visual / Auto-embed
    add_rect(s1, 6.80, 0.65, 5.90, 5.95, BG_COOL, border_c=BORDER_GRAY, rounded=True, radius=0.04)
    add_rect(s1, 6.80, 0.65, 5.90, 0.44, IBM_NAVY, rounded=False)
    add_text(s1, 7.02, 0.72, 5.45, 0.30, "VidyaPlan  —  Decision-Support Dashboard", size=11.5, bold=True, color=WHITE)

    if os.path.exists("screenshots/dashboard.png"):
        s1.shapes.add_picture("screenshots/dashboard.png", Inches(6.95), Inches(1.22), width=Inches(5.60), height=Inches(5.20))
    else:
        # Clean Vector UI Mockup representing VidyaPlan Recommended Plan screen
        add_rect(s1, 7.05, 1.28, 5.40, 0.55, WHITE, border_c=BORDER_GRAY, rounded=True, radius=0.10)
        add_pill(s1, 7.18, 1.40, 1.35, 0.30, "OFFICIAL 2017–18", IBM_GREEN_10, IBM_GREEN, size=9.5)
        add_text(s1, 8.62, 1.41, 3.70, 0.30, "Karnataka Schools Dataset  •  Provenance-tracked", size=10, color=TEXT_SECOND)

        add_text(s1, 7.05, 2.02, 4.0, 0.38, "Recommended Plan", size=18, bold=True, color=TEXT_PRIMARY)
        add_text(s1, 7.05, 2.40, 5.40, 0.30, "Budget: ₹50.0L  •  14 interventions funded  •  SIMULATED", size=11, color=TEXT_SECOND)

        for bx, btxt, bfill, btc in [
            (7.05, "Agent Trace", WHITE, TEXT_PRIMARY),
            (8.65, "Export Memo PDF", WHITE, TEXT_PRIMARY),
            (10.55, "Review →", IBM_BLUE, WHITE),
        ]:
            add_pill(s1, bx, 2.84, 1.48 if bx < 10 else 1.80, 0.36, btxt, bfill, btc, size=10, border_c=BORDER_GRAY if bfill == WHITE else None)

        # Mini KPI strip inside preview
        for i, (kv, kl, kc) in enumerate([("40", "Schools", IBM_BLUE), ("14", "Interventions", IBM_GREEN), ("94%", "Budget Used", IBM_PURPLE)]):
            kx = 7.05 + i * 1.85
            add_rect(s1, kx, 3.40, 1.70, 1.05, WHITE, border_c=BORDER_GRAY, rounded=True, radius=0.08)
            add_text(s1, kx + 0.14, 3.50, 1.42, 0.42, kv, size=20, bold=True, color=kc)
            add_text(s1, kx + 0.14, 3.98, 1.42, 0.30, kl, size=10.5, color=TEXT_SECOND)

        # Provenance & Human Review preview box
        add_rect(s1, 7.05, 4.65, 5.40, 1.70, IBM_BLUE_10, border_c=IBM_BLUE, rounded=True, radius=0.06)
        add_text(s1, 7.25, 4.82, 5.0, 0.28, "HUMAN REVIEW & PROVENANCE GUARDRAIL", size=10, bold=True, color=IBM_NAVY)
        add_text(
            s1, 7.25, 5.14, 5.0, 1.05,
            "• Missing & unreliable records are excluded from base funding.\n• Every recommendation carries IBM Granite explanation.\n• Replace this box with screenshots/dashboard.png if desired.",
            size=10.5, color=TEXT_PRIMARY
        )

    add_text(s1, 0.70, 7.05, 11.9, 0.25, "01 / 07  •  5–10 Minute Pitch + Live Demo", size=9.5, bold=True, color=TEXT_MUTED, align=PP_ALIGN.RIGHT)

    # ==========================================================
    # SLIDE 2: THE PROBLEM WE'RE SOLVING
    # ==========================================================
    s2 = prs.slides.add_slide(blank)
    add_header_footer(
        s2, "01 / Problem Statement",
        "The Problem We're Solving",
        "The Challenge: Making Better Infrastructure Decisions with Limited Budgets", 2
    )

    # Top Visual Row: 3 Simple Concept Icon Cards
    icons = [
        ("?", "Incomplete Data", "2017–18 records have blank & unreliable entries.", IBM_RED, IBM_RED_10),
        ("₹", "Limited Budget", "Scarce funds prevent fixing every gap at once.", IBM_BLUE, IBM_BLUE_10),
        ("⚡", "Dependencies", "Computers fail without reliable electricity.", IBM_TEAL, IBM_TEAL_10),
    ]
    for i, (sym, head, sub, col, fill) in enumerate(icons):
        ix = 0.60 + i * 4.11
        add_rect(s2, ix, 1.40, 3.91, 1.32, fill, border_c=BORDER_GRAY, rounded=True, radius=0.06)
        add_pill(s2, ix + 0.18, 1.72, 0.64, 0.64, sym, col, WHITE, size=20)
        add_text(s2, ix + 0.96, 1.60, 2.78, 0.32, head, size=14.5, bold=True, color=TEXT_PRIMARY)
        add_text(s2, ix + 0.96, 1.94, 2.78, 0.60, sub, size=11.5, color=TEXT_SECOND)

    # Middle 2x2 Challenge Detail Grid
    challenges = [
        ("Incomplete Data", "Karnataka Schools Facilities Census (2017–18) contains missing and unreliable facility records.", IBM_RED),
        ("Budget Constraints", "Limited funds make it difficult to prioritise infrastructure improvements across schools.", IBM_BLUE),
        ("Infrastructure Dependencies", "Computers require confirmed electricity or electricity provision in the same plan.", IBM_TEAL),
        ("Risk of Wrong Decisions", "Missing information should never be mistaken for a confirmed infrastructure gap.", IBM_PURPLE),
    ]
    for idx, (chead, cbody, ccol) in enumerate(challenges):
        r, c = divmod(idx, 2)
        cx = 0.60 + c * 6.16
        cy = 2.94 + r * 1.32
        add_rect(s2, cx, cy, 5.96, 1.16, WHITE, border_c=BORDER_GRAY, rounded=True, radius=0.05)
        add_rect(s2, cx, cy + 0.14, 0.08, 0.88, ccol, rounded=False)
        add_text(s2, cx + 0.24, cy + 0.16, 5.52, 0.30, chead, size=13.5, bold=True, color=TEXT_PRIMARY)
        add_text(s2, cx + 0.24, cy + 0.48, 5.52, 0.56, cbody, size=12, color=TEXT_SECOND)

    # Bottom Objective Banner
    add_rect(s2, 0.60, 5.72, 12.13, 1.05, IBM_NAVY, rounded=True, radius=0.06)
    add_text(s2, 0.90, 5.86, 11.53, 0.26, "OUR OBJECTIVE", size=10.5, bold=True, color=IBM_CYAN)
    add_text(
        s2, 0.90, 6.14, 11.53, 0.50,
        "Build a transparent decision-support system that analyses 40 schools across Library, Electricity and Computer infrastructure interventions.",
        size=14, bold=True, color=WHITE
    )

    # ==========================================================
    # SLIDE 3: OUR SOLUTION & HOW IT WORKS (5-STEP HORIZONTAL FLOW)
    # ==========================================================
    s3 = prs.slides.add_slide(blank)
    add_header_footer(
        s3, "02 / Our Solution",
        "Our Solution & How It Works",
        "VidyaPlan: From School Data to Actionable Infrastructure Plans", 3
    )

    workflow = [
        ("01", "School Data", "Karnataka 2017–18 records — 40 schools", IBM_BLUE, IBM_BLUE_10),
        ("02", "Evidence Classification", "Confirmed Gap · Confirmed OK · Missing · Unreliable", IBM_TEAL, IBM_TEAL_10),
        ("03", "Portfolio Optimisation", "OR-Tools CP-SAT — budget & dependency constraints", IBM_NAVY, IBM_BLUE_10),
        ("04", "AI-Powered Explanation", "IBM Granite explains selected & deferred interventions", IBM_PURPLE, IBM_PURPLE_10),
        ("05", "Human Review", "Officer reviews, approves or rejects recommendations", IBM_GREEN, IBM_GREEN_10),
    ]

    for i, (num, wtitle, wdesc, wcol, wfill) in enumerate(workflow):
        wx = 0.60 + i * 2.48
        add_rect(s3, wx, 1.55, 2.20, 3.55, BG_COOL, border_c=BORDER_GRAY, rounded=True, radius=0.06)
        add_rect(s3, wx, 1.55, 2.20, 0.10, wcol, rounded=False)
        add_pill(s3, wx + 0.78, 1.85, 0.64, 0.64, num, wcol, WHITE, size=16)
        add_text(s3, wx + 0.14, 2.66, 1.92, 0.65, wtitle, size=14.5, bold=True, color=TEXT_PRIMARY, align=PP_ALIGN.CENTER)
        add_rect(s3, wx + 0.16, 3.45, 1.88, 1.40, wfill, border_c=BORDER_GRAY, rounded=True, radius=0.08)
        add_text(s3, wx + 0.22, 3.55, 1.76, 1.20, wdesc, size=11.5, color=TEXT_PRIMARY, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
        if i < 4:
            add_text(s3, wx + 2.20, 3.05, 0.28, 0.45, "→", size=20, bold=True, color=IBM_BLUE, align=PP_ALIGN.CENTER)

    # Key Principle Callout
    add_rect(s3, 0.60, 5.42, 12.13, 1.25, IBM_BLUE_10, border_c=IBM_BLUE, rounded=True, radius=0.06)
    add_rect(s3, 0.60, 5.42, 0.10, 1.25, IBM_BLUE, rounded=False)
    add_text(s3, 0.92, 5.58, 11.5, 0.28, "KEY ARCHITECTURAL PRINCIPLE", size=11, bold=True, color=IBM_BLUE)
    add_text(
        s3, 0.92, 5.90, 11.5, 0.55,
        "Solver owns the numbers. AI explains the facts.",
        size=20, bold=True, color=IBM_BLUE_DARK
    )

    # ==========================================================
    # SLIDE 4: TECHNOLOGY & SYSTEM ARCHITECTURE
    # ==========================================================
    s4 = prs.slides.add_slide(blank)
    add_header_footer(
        s4, "03 / Architecture & IBM Stack",
        "Technology & System Architecture",
        "Built Using IBM Technologies & Intelligent Optimisation", 4
    )

    # Simple Architecture Diagram Strip (Frontend -> API -> Decision Engine -> Database & AI)
    diag_nodes = [
        ("Frontend", "React + Vite + TS", IBM_BLUE),
        ("API Layer", "Python + FastAPI", IBM_NAVY),
        ("Decision Engine", "OR-Tools CP-SAT + 3 Agents", IBM_TEAL),
        ("Database & AI", "SQLite + IBM Granite", IBM_PURPLE),
    ]
    for i, (dhead, dsub, dcol) in enumerate(diag_nodes):
        dx = 0.60 + i * 3.12
        add_rect(s4, dx, 1.38, 2.78, 0.86, dcol, rounded=True, radius=0.10)
        add_text(s4, dx + 0.12, 1.46, 2.54, 0.28, dhead.upper(), size=10, bold=True, color=IBM_BLUE_10, align=PP_ALIGN.CENTER)
        add_text(s4, dx + 0.12, 1.74, 2.54, 0.38, dsub, size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        if i < 3:
            add_text(s4, dx + 2.78, 1.56, 0.34, 0.45, "→", size=20, bold=True, color=IBM_BLUE, align=PP_ALIGN.CENTER)

    # Left: Native 6-Row Tech Table
    tbl_shape = s4.shapes.add_table(7, 3, Inches(0.60), Inches(2.44), Inches(7.45), Inches(4.32))
    tbl = tbl_shape.table
    tbl.columns[0].width = Inches(1.75)
    tbl.columns[1].width = Inches(2.45)
    tbl.columns[2].width = Inches(3.25)

    headers = ["Component", "Technology", "Responsibility"]
    for c_idx, htxt in enumerate(headers):
        style_cell(tbl.cell(0, c_idx), htxt, size=11.5, bold=True, color=WHITE, fill_c=IBM_NAVY)

    tech_rows = [
        ("Frontend", "React + Vite + TypeScript", "Interactive dashboard"),
        ("Backend", "Python + FastAPI", "API and orchestration"),
        ("Optimisation", "Google OR-Tools CP-SAT", "Budget and dependency optimisation"),
        ("Database", "SQLite", "Data and audit records"),
        ("AI explanations", "IBM Granite / watsonx.ai", "Natural-language explanations"),
        ("Development", "IBM Bob", "Planning, coding, testing and refinement"),
    ]
    for r_idx, row_vals in enumerate(tech_rows, start=1):
        row_bg = WHITE if r_idx % 2 == 1 else BG_COOL
        for c_idx, val in enumerate(row_vals):
            style_cell(
                tbl.cell(r_idx, c_idx), val, size=11,
                bold=(c_idx == 0), color=TEXT_PRIMARY if c_idx < 2 else TEXT_SECOND, fill_c=row_bg
            )

    # Right: Three Specialised Agents Panel
    add_rect(s4, 8.28, 2.44, 4.45, 4.32, BG_COOL, border_c=BORDER_GRAY, rounded=True, radius=0.05)
    add_text(s4, 8.52, 2.60, 4.0, 0.32, "THREE SPECIALISED AGENTS", size=11.5, bold=True, color=IBM_BLUE)

    agents = [
        ("1. Facility Evidence Agent", "Classifies school infrastructure records into Confirmed Gap, Confirmed OK, Missing, or Unreliable.", IBM_TEAL),
        ("2. Portfolio Planning Agent", "Optimises interventions within budget constraints while enforcing electricity dependencies.", IBM_BLUE),
        ("3. Trade-off Explanation Agent", "Explains why interventions were selected or deferred using IBM Granite.", IBM_PURPLE),
    ]
    for i, (atitle, adesc, acol) in enumerate(agents):
        ay = 3.04 + i * 1.20
        add_rect(s4, 8.50, ay, 4.01, 1.06, WHITE, border_c=BORDER_GRAY, rounded=True, radius=0.06)
        add_rect(s4, 8.50, ay + 0.12, 0.08, 0.82, acol, rounded=False)
        add_text(s4, 8.70, ay + 0.12, 3.68, 0.28, atitle, size=12, bold=True, color=TEXT_PRIMARY)
        add_text(s4, 8.70, ay + 0.42, 3.68, 0.56, adesc, size=10.8, color=TEXT_SECOND)

    # ==========================================================
    # SLIDE 5: WHAT MAKES VIDYAPLAN DIFFERENT?
    # ==========================================================
    s5 = prs.slides.add_slide(blank)
    add_header_footer(
        s5, "04 / Differentiation & Guardrails",
        "What Makes VidyaPlan Different?",
        "Beyond Basic Budget Allocation", 5
    )

    diffs = [
        ("01", "Evidence-First Planning", "Missing and unreliable records are not automatically treated as infrastructure gaps.", IBM_BLUE, IBM_BLUE_10),
        ("02", "Dependency-Aware Optimisation", "Prevents computer allocation without confirmed or co-funded electricity.", IBM_TEAL, IBM_TEAL_10),
        ("03", "Verify-First Ranking", "Helps identify which unknown records should be physically verified.", IBM_AMBER, IBM_AMBER_10),
        ("04", "AI with Guardrails", "Granite explains solver-generated facts; deterministic fallback is available.", IBM_PURPLE, IBM_PURPLE_10),
        ("05", "Human-in-the-Loop", "Officers retain final approval authority, with audit logs and PDF memo export.", IBM_GREEN, IBM_GREEN_10),
    ]

    # Top Row: 3 cards
    for i in range(3):
        num, dtitle, dbody, dcol, dfill = diffs[i]
        dx = 0.60 + i * 4.11
        add_rect(s5, dx, 1.42, 3.91, 1.82, WHITE, border_c=BORDER_GRAY, rounded=True, radius=0.05)
        add_rect(s5, dx, 1.42, 3.91, 0.08, dcol, rounded=False)
        add_pill(s5, dx + 0.18, 1.66, 0.46, 0.34, num, dfill, dcol, size=11)
        add_text(s5, dx + 0.74, 1.66, 3.00, 0.36, dtitle, size=14, bold=True, color=TEXT_PRIMARY)
        add_text(s5, dx + 0.18, 2.15, 3.55, 0.92, dbody, size=12, color=TEXT_SECOND)

    # Bottom Row: 2 cards (centered)
    for i in range(2):
        num, dtitle, dbody, dcol, dfill = diffs[3 + i]
        dx = 2.655 + i * 4.11
        add_rect(s5, dx, 3.46, 3.91, 1.82, WHITE, border_c=BORDER_GRAY, rounded=True, radius=0.05)
        add_rect(s5, dx, 3.46, 3.91, 0.08, dcol, rounded=False)
        add_pill(s5, dx + 0.18, 3.70, 0.46, 0.34, num, dfill, dcol, size=11)
        add_text(s5, dx + 0.74, 3.70, 3.00, 0.36, dtitle, size=14, bold=True, color=TEXT_PRIMARY)
        add_text(s5, dx + 0.18, 4.19, 3.55, 0.92, dbody, size=12, color=TEXT_SECOND)

    # Guardrail summary banner
    add_rect(s5, 0.60, 5.52, 12.13, 1.22, IBM_NAVY, rounded=True, radius=0.06)
    add_text(s5, 0.90, 5.66, 11.5, 0.26, "9 GUARDRAIL LAYERS", size=10.5, bold=True, color=IBM_CYAN)
    add_text(
        s5, 0.90, 5.96, 11.5, 0.60,
        "Input Validation  •  Output Provenance  •  Tool Execution  •  Data Integrity  •  Security  •  Operational  •  Human-in-the-Loop  •  Multi-Agent  •  Ethical",
        size=13, bold=False, color=WHITE
    )

    # ==========================================================
    # SLIDE 6: LIVE DEMO RESULTS
    # ==========================================================
    s6 = prs.slides.add_slide(blank)
    add_header_footer(
        s6, "05 / Live Demo Results",
        "Live Demo Results — Verified Local Run",
        "40 Karnataka Schools  •  Rs. 50 Lakh Budget  •  IBM Granite Explanations  •  Human Review Gate", 6
    )

    # KPI strip
    kpis = [
        ("14", "Interventions Funded", IBM_BLUE),
        ("12", "Schools Improved", IBM_GREEN),
        ("Rs.47L", "Budget Used (94%)", IBM_PURPLE),
        ("<1s", "Plan Response Time", IBM_TEAL),
    ]
    for i, (kval, klbl, kcol) in enumerate(kpis):
        kx = 0.60 + i * 3.08
        add_rect(s6, kx, 1.42, 2.84, 1.30, WHITE, border_c=BORDER_GRAY, rounded=True, radius=0.08)
        add_rect(s6, kx, 1.42, 2.84, 0.08, kcol, rounded=False)
        add_text(s6, kx + 0.14, 1.60, 2.56, 0.52, kval, size=28, bold=True, color=kcol)
        add_text(s6, kx + 0.14, 2.14, 2.56, 0.44, klbl, size=12, color=TEXT_SECOND)

    # 4-step workflow boxes
    steps = [
        ("01  DATA", "40-school cohort\nOFFICIAL 2017–18\nMISSING / UNRELIABLE\nflagged & excluded", IBM_BLUE),
        ("02  BUDGET", "Rs. 50L slider\nCost config (SIMULATED)\nWeight overrides\nConstraint preview", IBM_NAVY),
        ("03  PLAN", "14 interventions funded\nAgent Trace panel\nStress test (100 runs)\nMemo PDF export", IBM_TEAL),
        ("04  REVIEW", "Draft → In Review → Final\nApprove / Reject per item\nAudit log timestamped\nImmutable on FINAL", IBM_GREEN),
    ]
    for i, (stitle, sbody, scol) in enumerate(steps):
        sx = 0.60 + i * 3.08
        add_rect(s6, sx, 2.98, 2.84, 3.78, BG_COOL, border_c=BORDER_GRAY, rounded=True, radius=0.06)
        add_rect(s6, sx, 2.98, 2.84, 0.08, scol, rounded=False)
        add_text(s6, sx + 0.18, 3.12, 2.52, 0.38, stitle, size=13.5, bold=True, color=scol)
        add_text(s6, sx + 0.18, 3.56, 2.52, 3.00, sbody, size=12, color=TEXT_SECOND)
        if i < 3:
            add_text(s6, sx + 2.84, 4.52, 0.24, 0.42, "→", size=18, bold=True, color=IBM_BLUE, align=PP_ALIGN.CENTER)

    add_rect(s6, 0.60, 6.90, 12.13, 0.38, IBM_BLUE_10, border_c=IBM_BLUE, rounded=True, radius=0.04)
    add_text(
        s6, 0.80, 6.95, 11.7, 0.28,
        "OFFICIAL 2017–18 school facts  •  SIMULATED costs & weights  •  Provenance badge on every screen  •  Zero hardcoded secrets",
        size=11, bold=True, color=IBM_NAVY
    )

    # ==========================================================
    # SLIDE 7: NOVELTY, ROADMAP & LINKS
    # ==========================================================
    s7 = prs.slides.add_slide(blank)
    add_header_footer(
        s7, "06 / Novelty, Roadmap & Links",
        "Novelty, Roadmap & Project Links",
        "What Makes VidyaPlan Distinct and Where It Goes Next", 7
    )

    # Left: Novelty
    add_rect(s7, 0.60, 1.42, 5.90, 0.38, IBM_BLUE_10, border_c=IBM_BLUE, rounded=True, radius=0.04)
    add_text(s7, 0.80, 1.47, 5.5, 0.28, "NOVELTY & UNIQUENESS", size=11, bold=True, color=IBM_BLUE)

    novelty = [
        ("Evidence-First 4-State Model", "MISSING / UNRELIABLE are explicit states — never silently treated as gaps."),
        ("Solver-Grounded AI", "OR-Tools CP-SAT owns all arithmetic; Granite strictly explains verified facts."),
        ("Dependency Enforcement", "Computers cannot be funded without confirmed electricity."),
        ("Verify-First Prioritisation", "Ranks unknown fields by decision value to direct field-inspection visits."),
        ("Full Auditability", "Every rupee has a documented evidence trail and human sign-off."),
    ]
    for i, (ntitle, ndesc) in enumerate(novelty):
        ny = 1.96 + i * 0.84
        add_rect(s7, 0.60, ny, 5.90, 0.76, WHITE, border_c=BORDER_GRAY, rounded=True, radius=0.04)
        add_rect(s7, 0.60, ny + 0.10, 0.08, 0.56, IBM_BLUE, rounded=False)
        add_text(s7, 0.84, ny + 0.10, 5.50, 0.28, ntitle, size=13, bold=True, color=TEXT_PRIMARY)
        add_text(s7, 0.84, ny + 0.40, 5.50, 0.28, ndesc, size=11.5, color=TEXT_SECOND)

    # Right: Roadmap
    add_rect(s7, 7.08, 1.42, 5.65, 0.38, IBM_TEAL_10, border_c=IBM_TEAL, rounded=True, radius=0.04)
    add_text(s7, 7.28, 1.47, 5.25, 0.28, "ROADMAP", size=11, bold=True, color=IBM_TEAL)

    roadmap = [
        ("Live UDISE+ Integration", "Replace 2017–18 baseline with current records."),
        ("Field Verification Mobile App", "Block officers submit geo-tagged photo updates for MISSING records."),
        ("District-Scale GIS Planning", "Expand from 40-school cohorts to state-wide optimisation."),
        ("IBM Cloud Code Engine Pilot", "Role-based auth + verified live /health endpoint."),
    ]
    for i, (rtitle, rdesc) in enumerate(roadmap):
        ry = 1.96 + i * 1.00
        add_rect(s7, 7.08, ry, 5.65, 0.90, WHITE, border_c=BORDER_GRAY, rounded=True, radius=0.04)
        add_rect(s7, 7.08, ry + 0.10, 0.08, 0.70, IBM_TEAL, rounded=False)
        add_text(s7, 7.32, ry + 0.10, 5.25, 0.28, rtitle, size=13, bold=True, color=TEXT_PRIMARY)
        add_text(s7, 7.32, ry + 0.42, 5.25, 0.36, rdesc, size=11.5, color=TEXT_SECOND)

    # Links panel
    add_rect(s7, 0.60, 6.18, 12.13, 1.08, IBM_NAVY, rounded=True, radius=0.06)
    add_text(s7, 0.90, 6.26, 11.5, 0.26, "PROJECT LINKS", size=10.5, bold=True, color=IBM_CYAN)
    add_text(
        s7, 0.90, 6.54, 11.5, 0.56,
        "GitHub: [ PASTE GITHUB URL ]   |   Cloud: [ PASTE IBM CLOUD CODE ENGINE URL ]   |   Local: http://localhost:5173   |   API Docs: http://localhost:8000/docs",
        size=13, bold=False, color=WHITE
    )

    # ==========================================================
    # SAVE
    # ==========================================================
    prs.save(output_path)
    print(f"Saved: {output_path}")
    return output_path


if __name__ == "__main__":
    build_ibm_pitch_deck("VidyaPlan_IBM_Pitch_7Slides.pptx")
