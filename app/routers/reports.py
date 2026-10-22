from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import Assignment, User, utcnow
from ..pdf_report import build_weekly_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/weekly.pdf", response_class=Response, responses={200: {"content": {"application/pdf": {}}}})
def weekly_pdf(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = list(db.scalars(select(Assignment).where(Assignment.user_id == user.id)))
    pdf = build_weekly_report(user, items, utcnow())
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="weekly-report.pdf"'},
    )
