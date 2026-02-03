import logging
import os

from sqlmodel import Session

from app.core.db import engine, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    with Session(engine) as session:
        init_db(session)


def seed_worklog_data() -> None:
    """Seed worklog demo data."""
    from scripts.seed_worklogs import seed_data
    seed_data()


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")

    # Seed worklog data if environment variable is set or always in development
    if os.getenv("SEED_WORKLOG_DATA", "true").lower() == "true":
        logger.info("Seeding worklog demo data...")
        seed_worklog_data()
        logger.info("Worklog data seeded")


if __name__ == "__main__":
    main()
