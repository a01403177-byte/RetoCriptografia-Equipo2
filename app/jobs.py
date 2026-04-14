from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.db import SessionLocal
from app.services import ExpirationService


scheduler = BackgroundScheduler()


def run_expiration_job() -> None:
    db = SessionLocal()
    try:
        ExpirationService.expire_users(db)
    finally:
        db.close()


def start_scheduler() -> None:
    if scheduler.running:
        return

    scheduler.add_job(run_expiration_job, "interval", minutes=settings.expiration_job_minutes)
    scheduler.start()
