"""Weekly PDF report for one student, built with reportlab."""
from datetime import datetime, timedelta
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import Assignment, User


def _table(rows: list[list[str]], header_color) -> Table:
    t = Table([["Course", "Assignment", "Due (UTC)"]] + rows, colWidths=[4 * cm, 8 * cm, 4.5 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), header_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return t


def build_weekly_report(user: User, assignments: list[Assignment], now: datetime) -> bytes:
    week = now + timedelta(days=7)
    overdue = sorted((a for a in assignments if not a.completed_at and a.due_at < now), key=lambda a: a.due_at)
    upcoming = sorted(
        (a for a in assignments if not a.completed_at and now <= a.due_at <= week), key=lambda a: a.due_at
    )
    done = sorted(
        (a for a in assignments if a.completed_at and a.completed_at >= now - timedelta(days=7)),
        key=lambda a: a.completed_at,
    )

    def rows(items):
        return [[a.course, a.title, a.due_at.strftime("%a %d %b %Y %H:%M")] for a in items]

    styles = getSampleStyleSheet()
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="Weekly deadline report", author="Deadline Reminder")
    story = [
        Paragraph("Weekly Deadline Report", styles["Title"]),
        Paragraph(f"{user.name} &middot; generated {now.strftime('%d %b %Y %H:%M')} UTC", styles["Normal"]),
        Spacer(1, 0.5 * cm),
        Paragraph(
            f"<b>{len(overdue)}</b> overdue &nbsp;|&nbsp; <b>{len(upcoming)}</b> due in the next 7 days "
            f"&nbsp;|&nbsp; <b>{len(done)}</b> completed this week",
            styles["Normal"],
        ),
        Spacer(1, 0.6 * cm),
    ]
    for heading, items, color in [
        ("Overdue", overdue, colors.HexColor("#b3261e")),
        ("Due in the next 7 days", upcoming, colors.HexColor("#1a5fb4")),
        ("Completed this week", done, colors.HexColor("#2e7d32")),
    ]:
        story.append(Paragraph(heading, styles["Heading2"]))
        if items:
            story.append(_table(rows(items), color))
        else:
            story.append(Paragraph("Nothing here.", styles["Italic"]))
        story.append(Spacer(1, 0.4 * cm))
    doc.build(story)
    return buf.getvalue()
