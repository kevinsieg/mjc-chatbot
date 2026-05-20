import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db_util import get_connection
from app.settings import get_retention_days

_scheduler = AsyncIOScheduler()


def _purge_old_logs() -> None:
    try:
        days = get_retention_days()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM chat_logs WHERE timestamp < NOW() - make_interval(days => %s)",
                    (days,),
                )
                deleted = cur.rowcount
            conn.commit()
        if deleted:
            print(f"Retention purge: removed {deleted} chat_log rows older than {days} days", flush=True)
    except Exception as exc:
        print(f"Retention purge FAILED: {exc}", file=sys.stderr, flush=True)


def start_scheduler() -> None:
    _scheduler.add_job(_purge_old_logs, "cron", hour=2, minute=0)
    _scheduler.start()


def stop_scheduler() -> None:
    _scheduler.shutdown(wait=False)
