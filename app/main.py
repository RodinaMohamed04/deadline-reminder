import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from .config import settings
from .database import init_db
from .reminders import scheduled_scan
from .routers import assignments, auth, reminders, reports

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler = None
    if settings.ENABLE_SCHEDULER:
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            scheduled_scan,
            "interval",
            minutes=settings.SCAN_INTERVAL_MINUTES,
            id="reminder-scan",
            max_instances=1,
            coalesce=True,
        )  # first run happens after one interval; POST /reminders/run triggers it on demand
        scheduler.start()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="Deadline Reminder",
    description="Never miss an assignment deadline: track assignments, get reminders, get a weekly PDF.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(assignments.router)
app.include_router(reminders.router)
app.include_router(reports.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
