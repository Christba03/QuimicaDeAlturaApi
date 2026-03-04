"""
Webhook / event pub-sub service.

On key auth events, publishes a JSON payload to:
  1. Redis Pub/Sub channel (for in-process microservices)
  2. HTTP webhook URLs (for external integrations)

Usage:
    await webhook_service.publish(
        event_type="USER_REGISTERED",
        user_id=str(user.id),
        data={"email": user.email},
        redis_client=redis,
    )
"""
import json
import uuid
from datetime import datetime, timezone

import structlog

from src.config import settings

logger = structlog.get_logger()

# Events published to the pub-sub channel
PUBLISHABLE_EVENTS = {
    "USER_REGISTERED",
    "LOGIN_SUCCESS",
    "LOGIN_FAILED",
    "ACCOUNT_LOCKED",
    "ACCOUNT_UNLOCKED",
    "PASSWORD_CHANGED",
    "PASSWORD_RESET_COMPLETED",
    "TWO_FACTOR_ENABLED",
    "TWO_FACTOR_DISABLED",
    "SUSPICIOUS_ACTIVITY",
    "SESSION_REVOKED",
    "OAUTH_LOGIN",
    "API_KEY_CREATED",
    "API_KEY_REVOKED",
}


class WebhookService:
    async def publish(
        self,
        event_type: str,
        redis_client,
        user_id: str | None = None,
        data: dict | None = None,
    ) -> None:
        """
        Publish an auth event to Redis Pub/Sub and configured HTTP webhooks.
        Fails silently — never disrupts the main auth flow.
        """
        if not settings.WEBHOOK_ENABLED:
            return

        if event_type not in PUBLISHABLE_EVENTS:
            return

        payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "service": "auth-service",
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data or {},
        }
        message = json.dumps(payload)

        # --- Redis Pub/Sub ---
        try:
            await redis_client.publish(settings.WEBHOOK_REDIS_CHANNEL, message)
            logger.debug("webhook.redis_published", event_type=event_type, channel=settings.WEBHOOK_REDIS_CHANNEL)
        except Exception as e:
            logger.error("webhook.redis_publish_failed", event_type=event_type, error=str(e))

        # --- HTTP webhooks ---
        urls = settings.webhook_http_url_list
        if urls:
            await self._send_http_webhooks(urls, payload, message)

    async def _send_http_webhooks(self, urls: list[str], payload: dict, message: str) -> None:
        """POST the event payload to each configured HTTP webhook URL."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                for url in urls:
                    try:
                        resp = await client.post(
                            url,
                            content=message,
                            headers={
                                "Content-Type": "application/json",
                                "X-Auth-Event": payload["event_type"],
                                "X-Event-Id": payload["event_id"],
                            },
                        )
                        if resp.status_code >= 400:
                            logger.warning(
                                "webhook.http_error",
                                url=url,
                                status_code=resp.status_code,
                                event_type=payload["event_type"],
                            )
                        else:
                            logger.debug("webhook.http_sent", url=url, event_type=payload["event_type"])
                    except Exception as e:
                        logger.error("webhook.http_request_failed", url=url, error=str(e))
        except ImportError:
            logger.warning("webhook.httpx_not_available")


class _WebhookServiceWithState(WebhookService):
    """
    Singleton wrapper that stores the Redis client at startup so callers
    don't need to pass it explicitly.
    """
    _redis = None

    def initialize(self, redis_client) -> None:
        self._redis = redis_client

    async def emit(
        self,
        event_type: str,
        user_id: str | None = None,
        data: dict | None = None,
    ) -> None:
        """Publish using the module-level Redis client (set at startup)."""
        if self._redis is None:
            return
        await self.publish(event_type, self._redis, user_id=user_id, data=data)


# Singleton — call webhook_service.initialize(redis) at app startup
webhook_service = _WebhookServiceWithState()
