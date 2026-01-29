import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session

from app.core.db import engine
from app.financials.models import TaskStatus
from app.financials.service import FinancialService

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def finalize_payouts_job():
    logger.info("Starting scheduled job: Finalize Pending Payouts")
    with Session(engine) as session:
        FinancialService.finalize_pending_payouts(session)


def retry_funding_job():
    logger.info("Starting scheduled job: Retry Awaiting Funding")
    with Session(engine) as session:
        FinancialService.retry_awaiting_funding(session)


def monthly_settlement_job():
    logger.info("Starting scheduled job: Monthly Settlement Run")
    with Session(engine) as session:
        # Create a TaskStatus for the automated run
        task_status = TaskStatus(task_type="AUTOMATED_MONTHLY_SETTLEMENT")
        session.add(task_status)
        session.commit()
        session.refresh(task_status)

        FinancialService.run_settlement_process(session, task_status.id)


def start_scheduler():
    if not scheduler.running:
        # 1. Finalize payouts every hour
        scheduler.add_job(
            finalize_payouts_job,
            trigger="interval",
            hours=1,
            id="finalize_payouts",
            replace_existing=True,
        )

        # 2. Retry funding every 30 minutes
        scheduler.add_job(
            retry_funding_job,
            trigger="interval",
            minutes=30,
            id="retry_funding",
            replace_existing=True,
        )

        # 3. Monthly settlement run (1st of every month at midnight)
        scheduler.add_job(
            monthly_settlement_job,
            trigger=CronTrigger(day=1, hour=0, minute=0),
            id="monthly_settlement",
            replace_existing=True,
        )

        scheduler.start()
        logger.info("Financial Scheduler started.")


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Financial Scheduler shut down.")
