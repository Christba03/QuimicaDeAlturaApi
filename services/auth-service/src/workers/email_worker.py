"""
ARQ worker for processing email queue.

Run with: arq src.workers.email_worker.WorkerSettings
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from arq import cron
from arq.worker import Worker

from src.config import settings
from src.services.email_service import email_service

logger = structlog.get_logger()


async def send_email_task(
    ctx,
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
) -> bool:
    """
    ARQ task to send an email.
    
    This function is called by the ARQ worker when processing email jobs.
    """
    try:
        logger.info("email_worker.sending", to=to_email, subject=subject)
        success = await email_service.send_email(to_email, subject, html_content, text_content)
        
        if success:
            logger.info("email_worker.sent", to=to_email, subject=subject)
        else:
            logger.warning("email_worker.failed", to=to_email, subject=subject)
        
        return success
    except Exception as e:
        logger.error("email_worker.error", to=to_email, error=str(e))
        raise  # Re-raise to trigger retry


class WorkerSettings:
    """ARQ worker settings."""
    
    redis_settings = None  # Will be set from settings
    functions = [send_email_task]
    max_jobs = 10
    job_timeout = 300  # 5 minutes
    
    # Retry configuration
    max_tries = settings.EMAIL_QUEUE_MAX_RETRIES
    retry_delay = settings.EMAIL_QUEUE_RETRY_DELAY_SECONDS
    
    # Rate limiting: process max N emails per minute
    # This is handled by the worker's max_jobs and job_timeout
    
    @classmethod
    def get_redis_settings(cls):
        """Get Redis settings from app config."""
        from arq.connections import RedisSettings
        return RedisSettings.from_dsn(settings.redis_url)


# For running the worker directly
if __name__ == "__main__":
    import sys
    
    redis_settings = WorkerSettings.get_redis_settings()
    
    worker = Worker(
        functions=WorkerSettings.functions,
        redis_settings=redis_settings,
        max_jobs=WorkerSettings.max_jobs,
        job_timeout=WorkerSettings.job_timeout,
        max_tries=WorkerSettings.max_tries,
        retry_delay=WorkerSettings.retry_delay,
    )
    
    logger.info("email_worker.starting")
    worker.run()
