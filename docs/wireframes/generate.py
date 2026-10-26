"""Generates the low-fidelity wireframes in this folder as SVG files.

Run from the repo root:  python docs/wireframes/generate.py
Standard library only. Edit a screen function and re-run to update its SVG.
"""

import html
from pathlib import Path

OUT = Path(__file__).parent
FONT = "Segoe UI, Helvetica, Arial, sans-serif"

INK, MUTED, LINE, PANEL, FILL, ACCENT = "#1f2328", "#656d76", "#d0d7de", "#f6f8fa", "#eaeef2", "#24292f"
TONES = {
    "grey": ("#eaeef2", "#424a53"),
    "dark": ("#24292f", "#ffffff"),
    "red": ("#ffebe9", "#a40e26"),
    "amber": ("#fff8c5", "#7d4e00"),
    "green": ("#dafbe1", "#116329"),
    "blue": ("#ddf4ff", "#0a3069"),
}


class Frame:
    def __init__(self, name, w, h, mobile=False):
        self.name, self.w, self.h, self.mobile = name, w, h, mobile
        self.els = []

    def add(self, el):
        self.els.append(el)

    @staticmethod
    def tw(text, size):
        return len(text) * size * 0.56

    def rect(self, x, y, w, h, fill="#ffffff", stroke=LINE, rx=6, sw=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, t, size=14, weight=400, fill=INK, anchor="start"):
        self.add(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
                 f'text-anchor="{anchor}">{html.escape(t)}</text>')

    def line(self, x1, y1, x2, y2, stroke=LINE, sw=1):
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"/>')

    def circle(self, cx, cy, r, fill="#ffffff", stroke=LINE, sw=1):
        self.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def chip(self, x, y, t, tone="grey", size=12):
        bg, fg = TONES[tone]
        w = self.tw(t, size) + 18
        self.rect(x, y, w, 22, bg, bg, 11)
        self.text(x + 9, y + 15, t, size, 600, fg)
        return w

    def button(self, x, y, w, t, kind="secondary", h=36, size=14):
        styles = {
            "primary": (ACCENT, ACCENT, "#ffffff"),
            "secondary": ("#ffffff", LINE, INK),
            "disabled": (FILL, LINE, "#8c959f"),
        }
        fill, stroke, fg = styles[kind]
        self.rect(x, y, w, h, fill, stroke, 6)
        self.text(x + w / 2, y + h / 2 + size * 0.36, t, size, 600, fg, "middle")

    def field(self, x, y, w, label, value="", h=36, hint=None, placeholder=False, select=False, lines=None):
        """Label at y, box below it. `lines` gives multi-line content for text areas."""
        self.text(x, y, label, 13, 600)
        self.rect(x, y + 8, w, h)
        colour = "#8c959f" if placeholder else INK
        if lines:
            for i, ln in enumerate(lines):
                self.text(x + 10, y + 30 + i * 20, ln, 14, 400, colour)
        elif value:
            self.text(x + 10, y + 8 + h / 2 + 5, value, 14, 400, colour)
        if select:
            self.text(x + w - 18, y + 8 + h / 2 + 5, "▾", 14, 400, MUTED)
        if hint:
            self.text(x, y + 8 + h + 17, hint, 12, 400, MUTED)

    def check(self, x, y, label, checked=False, size=14, fill=INK):
        if checked:
            self.rect(x, y, 16, 16, ACCENT, ACCENT, 3)
            self.add(f'<polyline points="{x+4},{y+8} {x+7},{y+11} {x+12},{y+5}" fill="none" '
                     f'stroke="#ffffff" stroke-width="2"/>')
        else:
            self.rect(x, y, 16, 16, "#ffffff", "#8c959f", 3)
        self.text(x + 24, y + 13, label, size, 400, fill)

    def radio(self, x, y, label, on=False, size=14):
        self.circle(x + 8, y + 8, 8, "#ffffff", ACCENT if on else "#8c959f", 1.5)
        if on:
            self.circle(x + 8, y + 8, 4, ACCENT, ACCENT)
        self.text(x + 24, y + 13, label, size)

    def image(self, x, y, w, h):
        self.rect(x, y, w, h, PANEL, LINE, 4)
        self.line(x, y, x + w, y + h)
        self.line(x + w, y, x, y + h)

    def add_box(self, x, y, w, h, label="+ Add"):
        self.rect(x, y, w, h, "#ffffff", "#8c959f", 4, dash="4 3")
        self.text(x + w / 2, y + h / 2 + 5, label, 13, 600, MUTED, "middle")

    def panel(self, x, y, w, h, title=None):
        self.rect(x, y, w, h, PANEL, LINE, 8)
        if title:
            self.text(x + 16, y + 26, title, 15, 700)

    def save(self):
        body = "\n  ".join(self.els)
        clip_open = clip_close = defs = ""
        border = ""
        if self.mobile:
            defs = (f'<defs><clipPath id="phone"><rect x="0" y="0" width="{self.w}" height="{self.h}" '
                    f'rx="28"/></clipPath></defs>')
            clip_open, clip_close = '<g clip-path="url(#phone)">', "</g>"
            border = (f'<rect x="1" y="1" width="{self.w-2}" height="{self.h-2}" rx="28" fill="none" '
                      f'stroke="{INK}" stroke-width="2"/>')
        else:
            border = (f'<rect x="0.5" y="0.5" width="{self.w-1}" height="{self.h-1}" fill="none" '
                      f'stroke="{LINE}"/>')
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
               f'viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">\n'
               f'  {defs}\n  {clip_open}<rect width="{self.w}" height="{self.h}" fill="#ffffff"/>\n'
               f'  {body}\n  {clip_close}\n  {border}\n</svg>\n')
        (OUT / f"{self.name}.svg").write_text(svg, encoding="utf-8")


# ---------- shells ----------

def staff_shell(f, active, persona, clock):
    f.rect(0, 0, f.w, 56, ACCENT, ACCENT, 0)
    f.text(24, 35, "PCP Staff", 18, 700, "#ffffff")
    x = 150
    for item in ["Concerns", "Cases", "Investigations", "Work orders", "Oversight"]:
        on = item == active
        f.text(x, 35, item, 14, 600 if on else 400, "#ffffff" if on else "#adbac7")
        if on:
            f.rect(x, 52, f.tw(item, 14), 4, "#ffffff", "#ffffff", 2)
        x += f.tw(item, 14) + 28
    f.rect(740, 12, 270, 32, "#373e47", "#373e47", 6)
    f.text(752, 33, f"Demo clock  {clock}", 12, 400, "#ffffff")
    f.text(998, 33, "x60  ||", 12, 600, "#adbac7", "end")
    f.rect(1020, 12, 236, 32, "#ffffff", "#ffffff", 6)
    f.text(1032, 33, f"Persona: {persona}", 13, 600)
    f.text(1244, 33, "▾", 13, 400, MUTED, "end")


def tenant_shell(f, title):
    f.rect(0, 0, f.w, 64, ACCENT, ACCENT, 0)
    f.text(20, 42, title, 18, 700, "#ffffff")
    f.text(f.w - 20, 42, "Menu", 14, 600, "#adbac7", "end")


# ---------- screens ----------

def tenant_report():
    f = Frame("01-tenant-report-problem", 390, 844, mobile=True)
    tenant_shell(f, "Your home")
    f.text(20, 98, "Report a problem", 22, 700)
    f.text(20, 122, "Step 2 of 4", 13, 400, MUTED)
    for i in range(4):
        f.rect(20 + i * 89, 132, 83, 5, ACCENT if i < 2 else FILL, ACCENT if i < 2 else FILL, 2)

    f.rect(20, 152, 350, 62, TONES["red"][0], "#ff8182", 8)
    f.text(34, 176, "Immediate danger? Gas, electrics, flooding", 13, 700, TONES["red"][1])
    f.text(34, 198, "Call our emergency repairs line now.", 13, 400, TONES["red"][1])

    f.text(20, 244, "What's the problem?", 15, 700)
    tiles = ["Damp or mould", "Leak or water", "Heating", "Electrics", "Something else"]
    for i, t in enumerate(tiles):
        x, y = 20 + (i % 2) * 180, 256 + (i // 2) * 62
        on = i == 0
        f.rect(x, y, 170, 52, PANEL if on else "#ffffff", ACCENT if on else LINE, 8, 2 if on else 1)
        f.text(x + 14, y + 31, t, 14, 600 if on else 400)

    f.text(20, 462, "Which room?", 15, 700)
    x = 20
    for t, on in [("Child's bedroom", True), ("Bathroom", False), ("Kitchen", False)]:
        x += f.chip(x, 474, t, "dark" if on else "grey", 13) + 8
    x = 20
    for t in ["Living room", "Other"]:
        x += f.chip(x, 504, t, "grey", 13) + 8

    f.text(20, 558, "Is anyone's health affected?", 15, 700)
    f.radio(20, 570, "Yes", on=True)
    f.radio(90, 570, "No")
    f.radio(150, 570, "Not sure")
    f.rect(20, 598, 350, 70)
    f.text(30, 622, "My baby has been wheezing at night", 14)
    f.text(30, 642, "since the mould came back.", 14)

    f.text(20, 698, "Photos (optional)", 15, 700)
    f.image(20, 710, 64, 52)
    f.image(92, 710, 64, 52)
    f.add_box(164, 710, 64, 52)

    f.button(20, 782, 350, "Continue", "primary", 44, 15)
    f.save()


def tenant_case():
    f = Frame("02-tenant-case-timeline", 390, 844, mobile=True)
    tenant_shell(f, "Your home")
    f.text(20, 92, "‹ My cases", 13, 600, MUTED)
    f.text(20, 122, "Damp and mould", 22, 700)
    f.text(20, 144, "Bedroom · Ref HC-2026-0457", 13, 400, MUTED)
    f.chip(20, 154, "Repair booked", "amber", 12)

    f.panel(20, 190, 350, 100)
    f.text(36, 216, "What happens next", 13, 600, MUTED)
    f.text(36, 240, "Repair visit: Tue 29 Dec, 10:00 to 12:00", 14, 700)
    f.text(36, 262, "We must finish this by Wed 30 Dec.", 13, 400, MUTED)
    f.text(354, 216, "Change", 13, 600, "#0969da", "end")

    f.text(20, 322, "Timeline", 15, 700)
    events = [
        ("Tue 22 Dec", "Repair booked for Tue 29 Dec", None),
        ("Tue 22 Dec", "Letter: what we found and what we'll do", "View letter"),
        ("Mon 21 Dec", "Inspection done: hazard found", None),
        ("Fri 18 Dec", "Inspection booked for Mon 21 Dec", None),
        ("Fri 18 Dec", "You reported the problem", None),
    ]
    f.line(29, 340, 29, 340 + 64 * (len(events) - 1), LINE, 2)
    for i, (d, t, link) in enumerate(events):
        y = 340 + i * 64
        f.circle(29, y, 6, ACCENT if i == 0 else "#ffffff", ACCENT, 2)
        f.text(48, y - 2, d, 12, 400, MUTED)
        f.text(48, y + 17, t, 13, 600 if i == 0 else 400)
        if link:
            f.text(48, y + 36, link, 13, 600, "#0969da")

    f.button(20, 668, 350, "Add information or photos", "secondary", 40)
    f.button(20, 718, 350, "Ask for an in-person inspection", "disabled", 40)
    f.text(20, 776, "Not needed: an inspector visited on 21 Dec.", 12, 400, MUTED)
    f.text(195, 812, "Contact us", 14, 600, "#0969da", "middle")
    f.save()


def contact_centre_intake():
    f = Frame("03-contact-centre-intake-triage", 1280, 800)
    staff_shell(f, "Concerns", "Contact centre", "Tue 22 Dec 10:34")
    f.text(24, 96, "New concern", 22, 700)
    f.text(24, 118, "Any report, from any source, starts the legal clock.", 13, 400, MUTED)

    f.text(24, 152, "Source", 13, 600)
    x = 24
    for t in ["Tenant phone", "Tenant portal", "Advocate", "Operative", "Housing officer", "Env. health",
              "GP letter"]:
        x += f.chip(x, 162, t, "dark" if t == "Tenant phone" else "grey") + 8

    f.field(24, 210, 720, "Property", "22 Fir Lane, Flat 1, Newtown NT4 1XX",
            hint="Tenancy: Mr D. Mensah · 3 occupants")
    f.field(24, 290, 350, "Landlord became aware", "Tue 22 Dec 2026, 10:31",
            hint="Clocks run from this time, not from when it's typed in")
    f.field(394, 290, 350, "Hazard category", "Damp and mould growth", select=True)
    f.field(24, 370, 350, "Location in home", "Child's bedroom")
    f.field(394, 370, 350, "Reported by", "Mr D. Mensah (tenant)")
    f.field(24, 440, 720, "Description", h=56,
            lines=["Black mould on the outside wall behind the cot.",
                   "Came back two weeks after cleaning."])
    f.field(24, 530, 720, "Impact on health (tenant's words)", h=56,
            lines=["Baby (7 months) wheezing at night. GP appointment booked."])
    f.text(24, 620, "Photos", 13, 600)
    for i in range(3):
        f.image(24 + i * 108, 630, 96, 72)
    f.add_box(348, 630, 96, 72, "+ Add photo")

    f.panel(768, 76, 488, 700)
    f.text(784, 104, "Household", 15, 700)
    x = 784
    for t in ["Child under 5", "Respiratory condition"]:
        x += f.chip(x, 116, t, "blue") + 8
    f.text(784, 160, "Flags only. Medical details stay in Tenancies.", 12, 400, MUTED)
    f.line(784, 178, 1240, 178)

    f.text(784, 206, "Suggested triage", 15, 700)
    f.rect(784, 218, 456, 128, TONES["red"][0], "#ff8182", 8)
    f.text(800, 246, "EMERGENCY: 24 hour clock", 16, 700, TONES["red"][1])
    f.text(800, 270, "Why:", 13, 600, TONES["red"][1])
    f.text(800, 292, "• Mould in a bedroom used by a child under 5", 13, 400, INK)
    f.text(800, 312, "• Tenant reports breathing problems", 13, 400, INK)
    f.text(800, 334, "Rule: damp-child-bedroom v1 · a suggestion, not a decision", 12, 400, MUTED)

    f.text(784, 376, "Your decision", 15, 700)
    f.radio(784, 390, "Accept: emergency, 24 hour clock starts now", on=True)
    f.radio(784, 420, "Override: standard, 10 working day clock")
    f.field(784, 462, 456, "Reason for override", "Required if you override the suggestion",
            h=60, placeholder=True)
    f.button(784, 560, 220, "Open hazard case", "primary")
    f.button(1020, 560, 220, "Save as repair only")
    f.text(784, 626, "Previous cases at this property: none", 12, 400, MUTED)
    f.save()


def investigator_finding():
    f = Frame("04-investigator-record-finding", 1280, 800)
    staff_shell(f, "Investigations", "Investigator", "Tue 22 Dec 13:20")
    f.text(24, 96, "HC-2026-0463 · 22 Fir Lane, Flat 1", 20, 700)
    f.text(24, 120, "Damp and mould · Child's bedroom · Triage: Emergency (accepted 10:33)", 13, 400, MUTED)
    f.chip(1046, 82, "Emergency clock: 21h 11m left", "red")

    f.panel(24, 140, 600, 236, "Must be considered before you conclude")
    f.text(608, 166, "3 of 4 considered", 12, 600, MUTED, "end")
    items = [
        ("Vulnerability: child under 5", True),
        ("Vulnerability: respiratory condition", True),
        ("Tenant statement: \"Baby wheezing at night since mould came back\"", True),
        ("GP letter received 22 Dec (evidence E-3)", False),
    ]
    for i, (t, on) in enumerate(items):
        f.check(40, 186 + i * 34, t, on, 13)
    f.text(40, 344, "Conclude stays disabled until every item is ticked.", 12, 400, MUTED)

    f.panel(24, 392, 600, 216, "Evidence")
    for i in range(4):
        f.image(40 + i * 140, 428, 128, 80)
    for i, (k, v) in enumerate([("External wall, behind cot", "22% WME"), ("Window reveal", "19% WME"),
                                ("Relative humidity", "68%")]):
        f.text(40, 536 + i * 22, k, 13)
        f.text(600, 536 + i * 22, v, 13, 600, INK, "end")

    f.panel(24, 624, 600, 152, "Visit")
    f.text(40, 676, "Investigation type: Emergency", 13)
    f.text(40, 700, "Physical inspection: Tue 22 Dec, 12:05", 13)
    f.text(40, 724, "Investigator: R. Patel", 13)
    f.chip(40, 736, "Competent: damp and mould", "green")

    f.panel(648, 140, 608, 636, "Finding")
    f.text(664, 196, "Severity", 13, 600)
    for i, t in enumerate(["Emergency", "Significant", "Not relevant"]):
        f.button(664 + i * 192, 206, 184, t, "primary" if t == "Significant" else "secondary")
    f.rect(664, 254, 576, 34, TONES["amber"][0], "#d4a72c", 6)
    f.text(678, 276, "Lower than triage (Emergency): a rationale is required.", 13, 600, TONES["amber"][1])

    f.field(664, 312, 284, "HHSRS hazard category", "Damp and mould growth", select=True)
    f.field(956, 312, 284, "Exclusion", "None", select=True,
            hint="Tenant breach needs evidence + second sign-off")

    f.text(664, 400, "Required work", 13, 600)
    rows = [("Make safe", "Treat mould, replace failed extractor fan", "By Thu 31 Dec", "amber"),
            ("Preventative", "Insulate external wall, add trickle vents", "Start in 5 WD", "grey")]
    for i, (kind, what, due, tone) in enumerate(rows):
        y = 410 + i * 42
        f.rect(664, y, 576, 36)
        f.chip(672, y + 7, kind, "dark")
        f.text(790, y + 23, what, 13)
        f.chip(1240 - f.tw(due, 12) - 26, y + 7, due, tone)
    f.text(664, 514, "+ Add work item", 13, 600, "#0969da")
    f.check(664, 530, "Further investigation needed to scope the work")

    f.field(664, 576, 576, "Rationale", h=64,
            lines=["0.4 m² of mould, not on the cot side; RH 68%. Infant wheeze and GP letter considered.",
                   "Risk tolerable for 5 working days with the fan replaced. Make safe by Thu 31 Dec."])
    f.check(664, 670, "Can't make safe by the deadline: start rehousing")
    f.button(664, 716, 140, "Save draft")
    f.button(816, 716, 220, "Conclude investigation", "disabled")
    f.text(1050, 739, "1 item still to consider", 12, 600, TONES["amber"][1])
    f.save()


def scheduler_board():
    f = Frame("05-scheduler-work-orders", 1280, 800)
    staff_shell(f, "Work orders", "Scheduler", "Tue 22 Dec 09:25")
    f.text(24, 96, "Work orders", 22, 700)
    x = 200
    for t, on in [("All work", False), ("Awaab's Law only", True), ("Due this week", False)]:
        x += f.chip(x, 79, t, "dark" if on else "grey") + 8

    cols = {
        "To schedule (3)": [
            ("WO-1179", "Make safe · Electrics", "2 Ash Court", "Due today 17:40", "red", False),
            ("WO-1182", "Make safe · Damp and mould", "14 Elm Row, Flat 3", "Due Wed 30 Dec", "amber", True),
            ("WO-1185", "Preventative · Insulation", "14 Elm Row, Flat 3", "Start by 30 Dec", "grey", False),
        ],
        "Booked (2)": [
            ("WO-1170", "Make safe · Damp and mould", "9 Birch Way", "Wed 23 Dec 08:00", "grey", False),
            ("WO-1168", "Preventative · Ventilation", "5 Cedar Close", "Mon 4 Jan 13:00", "grey", False),
        ],
        "In progress (1)": [
            ("WO-1161", "Make safe · Falls (stair rail)", "31 Oak Street", "Due Wed 23 Dec", "amber", False),
        ],
        "Done today (1)": [
            ("WO-1150", "Make safe · Damp and mould", "5 Cedar Close", "Completed 08:40", "green", False),
        ],
    }
    for c, (title, cards) in enumerate(cols.items()):
        x = 24 + c * 208
        f.panel(x, 120, 200, 656)
        f.text(x + 12, 146, title, 14, 700)
        for i, (wo, kind, addr, due, tone, sel) in enumerate(cards):
            y = 160 + i * 112
            f.rect(x + 8, y, 184, 102, "#ffffff", ACCENT if sel else LINE, 6, 2 if sel else 1)
            f.text(x + 20, y + 24, wo, 14, 700)
            f.text(x + 20, y + 46, kind, 12)
            f.text(x + 20, y + 64, addr, 12, 400, MUTED)
            f.chip(x + 20, y + 72, due, tone, 11)

    f.panel(872, 120, 384, 656)
    f.text(888, 148, "Book WO-1182", 17, 700)
    f.text(888, 170, "Make safe · 14 Elm Row, Flat 3 · Due Wed 30 Dec", 12, 400, MUTED)
    f.field(888, 200, 352, "Contractor", "Dampfix Ltd (damp and mould)", select=True,
            hint="Only contractors competent for this hazard")
    f.field(888, 284, 168, "Date", "Tue 29 Dec", select=True)
    f.field(1072, 284, 168, "Slot", "10:00 to 12:00", select=True)
    f.text(888, 356, "Entry", 13, 600)
    f.radio(888, 368, "Tenant has agreed this time", on=True)
    f.radio(888, 396, "Entry without consent (24h written notice)")
    f.rect(888, 428, 352, 66, TONES["blue"][0], "#54aeff", 6)
    f.text(902, 450, "Notice rule", 13, 700, TONES["blue"][1])
    f.text(902, 470, "Without consent, written notice must be", 12, 400, TONES["blue"][1])
    f.text(902, 486, "served by Mon 28 Dec 10:00 for this slot.", 12, 400, TONES["blue"][1])

    f.text(888, 524, "Dampfix availability", 13, 600)
    days = [("Mon 28", "Bank hol.", None), ("Tue 29", "AM", "PM"), ("Wed 30", "AM", "PM"), ("Thu 31", "AM", "PM")]
    for i, (d, am, pm) in enumerate(days):
        x = 888 + i * 90
        f.text(x, 548, d, 12, 600)
        if pm is None:
            f.rect(x, 556, 82, 72, FILL, LINE, 4)
            f.text(x + 41, 597, am, 11, 600, MUTED, "middle")
        else:
            sel = d == "Tue 29"
            f.rect(x, 556, 82, 34, ACCENT if sel else "#ffffff", ACCENT if sel else LINE, 4)
            f.text(x + 41, 578, am, 12, 600, "#ffffff" if sel else INK, "middle")
            f.rect(x, 594, 82, 34, FILL if d == "Wed 30" else "#ffffff", LINE, 4)
            f.text(x + 41, 616, "Full" if d == "Wed 30" else pm, 12, 600, MUTED if d == "Wed 30" else INK,
                   "middle")
    f.button(888, 716, 352, "Book and notify tenant", "primary", 40)
    f.save()


def contractor_job():
    f = Frame("06-contractor-job", 390, 844, mobile=True)
    tenant_shell(f, "Jobs · Dampfix Ltd")
    f.text(20, 92, "‹ Today, Tue 29 Dec · 5 jobs", 13, 600, MUTED)
    f.text(20, 122, "WO-1182 · Make safe", 22, 700)
    f.text(20, 144, "Damp and mould · Awaab's Law", 13, 400, MUTED)
    f.chip(20, 154, "Legal deadline: Wed 30 Dec", "red")

    f.panel(20, 190, 350, 112)
    f.text(36, 216, "14 Elm Row, Flat 3, NT6 2XX", 14, 700)
    f.text(354, 216, "Navigate", 13, 600, "#0969da", "end")
    f.text(36, 240, "10:00 to 12:00 · tenant agreed", 13)
    f.text(36, 264, "Household: child under 5", 13)
    f.text(36, 286, "No medical details are shared with contractors.", 11, 400, MUTED)

    f.text(20, 334, "Work to do", 15, 700)
    f.check(20, 346, "Treat mould (bedroom wall, 1.2 m²)", True)
    f.check(20, 376, "Replace failed extractor fan", False)

    f.text(20, 426, "Photos before and after", 15, 700)
    f.image(20, 438, 76, 60)
    f.image(104, 438, 76, 60)
    f.add_box(188, 438, 76, 60)

    f.chip(20, 520, "Arrived 10:07", "green")
    f.button(20, 560, 350, "Work complete", "primary", 44, 15)
    f.button(20, 614, 350, "Couldn't get in (no access)", "secondary", 44, 15)
    f.button(20, 668, 350, "More work or investigation needed", "secondary", 44, 15)
    f.text(20, 740, "No access records the time, your location and a", 12, 400, MUTED)
    f.text(20, 758, "photo of the card you left. Repeated attempts", 12, 400, MUTED)
    f.text(20, 776, "help show reasonable endeavours.", 12, 400, MUTED)
    f.save()


def oversight_dashboard():
    f = Frame("07-compliance-oversight-dashboard", 1280, 800)
    staff_shell(f, "Oversight", "Compliance manager", "Tue 22 Dec 14:12")
    f.text(24, 96, "Compliance overview", 22, 700)
    x = 760
    for t, on in [("All hazards", True), ("Phase 2 hazards", False), ("All contractors", False)]:
        x += f.chip(x, 79, t, "dark" if on else "grey") + 8

    tiles = [("Open hazard cases", "42", None), ("Clocks at risk", "7", "amber"), ("Breached", "1", "red"),
             ("In temporary accommodation", "2", None), ("Avg working days to make safe", "3.4", None)]
    for i, (label, value, tone) in enumerate(tiles):
        x = 24 + i * 250
        fill, stroke = (TONES[tone][0], TONES[tone][0]) if tone else (PANEL, LINE)
        f.rect(x, 116, 232, 88, fill, stroke, 8)
        f.text(x + 16, 142, label, 13, 600, TONES[tone][1] if tone else MUTED)
        f.text(x + 16, 186, value, 32, 700, TONES[tone][1] if tone else INK)

    f.panel(24, 224, 848, 552, "Clocks at risk")
    f.text(856, 250, "Sorted by time left", 12, 400, MUTED, "end")
    cols = [40, 150, 330, 510, 640, 760]
    for x, h in zip(cols, ["Case", "Property", "Clock", "Due", "Time left", "Owner"]):
        f.text(x, 288, h, 12, 700, MUTED)
    f.line(40, 298, 856, 298)
    rows = [
        ("HC-0430", "18 Pine Road", "Investigation", "Fri 18 Dec", "Breached", "red", "A. Shah", True),
        ("HC-0461", "2 Ash Court", "Make safe (24h)", "Today 17:40", "3h 28m", "red", "Sparkwell", False),
        ("HC-0449", "31 Oak Street", "Make safe", "Wed 23 Dec", "1 WD", "amber", "Stairsafe", False),
        ("HC-0463", "22 Fir Lane, Flat 1", "Written summary", "Tue 29 Dec", "3 WD", "amber", "R. Patel", False),
        ("HC-0457", "14 Elm Row, Flat 3", "Make safe", "Wed 30 Dec", "4 WD", "grey", "Dampfix", False),
        ("HC-0452", "9 Birch Way", "Investigation", "Wed 6 Jan", "8 WD", "grey", "A. Shah", False),
        ("HC-0438", "5 Cedar Close", "Preventative start", "Mon 15 Mar", "11 wks", "grey", "Dampfix", False),
    ]
    for i, (case, prop, clock, due, left, tone, owner, breach) in enumerate(rows):
        y = 306 + i * 48
        if breach:
            f.rect(32, y, 832, 44, TONES["red"][0], TONES["red"][0], 4)
        for x, t in zip(cols, [case, prop, clock, due]):
            f.text(x, y + 27, t, 13, 600 if x == 40 else 400)
        f.chip(cols[4], y + 11, left, tone)
        f.text(cols[5], y + 27, owner, 13)
        if not breach:
            f.line(40, y + 44, 856, y + 44, FILL)

    f.panel(888, 224, 368, 352, "Live events")
    f.chip(1184, 232, "LIVE", "green", 11)
    events = [("14:12", "DeadlineApproaching", "HC-0461 · make safe, 3h 28m left"),
              ("14:02", "InvestigationConcluded", "HC-0463 · significant"),
              ("13:55", "NoAccessRecorded", "WO-1158 · third attempt"),
              ("13:40", "ConcernReported", "via housing officer · 7 Larch Grove"),
              ("13:31", "RehousingStarted", "HC-0444 · household of 2"),
              ("13:09", "WorkCompleted", "WO-1150 · 5 Cedar Close")]
    for i, (t, name, detail) in enumerate(events):
        y = 270 + i * 50
        f.text(904, y, t, 12, 400, MUTED)
        f.text(950, y, name, 13, 700)
        f.text(950, y + 19, detail, 12, 400, MUTED)

    f.panel(888, 592, 368, 184, "Breaches by week")
    values = [0, 1, 0, 2, 1, 0, 0, 1]
    for i, v in enumerate(values):
        x = 912 + i * 40
        h = v * 40
        if h:
            f.rect(x, 744 - h, 24, h, TONES["red"][1], TONES["red"][1], 3)
        f.line(x - 4, 744, x + 28, 744, LINE)
        f.text(x + 12, 762, f"W{45 + i}", 10, 400, MUTED, "middle")
    f.save()


def case_history():
    f = Frame("08-case-history-audit", 1280, 800)
    staff_shell(f, "Cases", "Compliance manager", "Tue 22 Dec 14:20")
    f.text(24, 96, "HC-2026-0457 · Case history", 22, 700)
    f.text(24, 118, "14 Elm Row, Flat 3 · Damp and mould · Append-only event stream", 13, 400, MUTED)
    f.chip(890, 80, "Hash chain verified", "green")
    f.button(1056, 74, 200, "Export evidence pack", "primary")

    x = 24
    for t in ["Summary", "History", "Letters", "Work orders", "Evidence"]:
        on = t == "History"
        f.text(x, 154, t, 14, 700 if on else 400, INK if on else MUTED)
        if on:
            f.rect(x, 162, f.tw(t, 14), 3, ACCENT, ACCENT, 1)
        x += f.tw(t, 14) + 32
    f.line(24, 166, 1256, 166)

    cols = [40, 76, 226, 330, 900, 1110]
    for c, h in zip(cols, ["#", "Occurred", "Recorded", "Event", "By", "Source"]):
        f.text(c, 196, h, 12, 700, MUTED)
    f.line(24, 206, 1256, 206)
    rows = [
        ("Fri 18 Dec 16:31", "16:44", "ConcernReported", "tenant phoned, damp in bedroom", "J. Lee, contact centre", "staff app"),
        ("Fri 18 Dec 16:46", "16:46", "TriageDecided", "standard (suggestion accepted)", "J. Lee", "staff app"),
        ("Fri 18 Dec 16:46", "16:46", "ClockStarted", "investigation, due Wed 6 Jan", "system", "hazard case"),
        ("Fri 18 Dec 17:02", "17:02", "InvestigationScheduled", "Mon 21 Dec, R. Patel", "S. Ward, scheduler", "staff app"),
        ("Mon 21 Dec 11:10", "11:58", "PhysicalInspectionCompleted", "photos E-1 to E-4", "R. Patel", "mobile"),
        ("Mon 21 Dec 15:30", "15:30", "InvestigationConcluded", "significant hazard", "R. Patel", "staff app"),
        ("Mon 21 Dec 15:30", "15:30", "ClockMet", "investigation, 9 working days early", "system", "hazard case"),
        ("Mon 21 Dec 15:30", "15:30", "ClockStarted", "written summary, due Thu 24 Dec", "system", "hazard case"),
        ("Mon 21 Dec 15:30", "15:30", "ClockStarted", "safety work, due Wed 30 Dec", "system", "hazard case"),
        ("Tue 22 Dec 09:12", "09:12", "WorkOrderRequested", "make safe, WO-1182", "system", "outbox"),
        ("Tue 22 Dec 09:40", "09:40", "WrittenSummarySent", "by email, letter L-2207", "Communications", "outbox"),
        ("Tue 22 Dec 09:40", "09:40", "ClockMet", "written summary", "system", "hazard case"),
    ]
    for i, (occ, rec, name, detail, by, src) in enumerate(rows):
        y = 214 + i * 44
        if i % 2:
            f.rect(24, y, 1232, 44, PANEL, PANEL, 0)
        f.text(cols[0], y + 27, str(i + 1), 13, 400, MUTED)
        f.text(cols[1], y + 27, occ, 13)
        if rec != occ.split()[-1]:
            f.chip(cols[2], y + 11, rec, "amber")
        else:
            f.text(cols[2], y + 27, rec, 13)
        f.text(cols[3], y + 27, name, 13, 700)
        f.text(cols[3] + f.tw(name, 13) + 10, y + 27, detail, 13, 400, MUTED)
        f.text(cols[4], y + 27, by, 13)
        f.text(cols[5], y + 27, src, 13, 400, MUTED)
    f.text(24, 756, "Amber = recorded later than it happened. Legal clocks run from 'Occurred'.", 12, 400, MUTED)
    f.text(24, 776, "Events are never edited or deleted; corrections are new events.", 12, 400, MUTED)
    f.save()


if __name__ == "__main__":
    for screen in [tenant_report, tenant_case, contact_centre_intake, investigator_finding,
                   scheduler_board, contractor_job, oversight_dashboard, case_history]:
        screen()
    print("Wrote", len(list(OUT.glob("*.svg"))), "SVG files to", OUT)
