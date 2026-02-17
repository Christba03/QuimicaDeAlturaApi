import json
from typing import Any

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger()


class EventPublisher:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.channel_prefix = "plant-service"

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        channel = f"{self.channel_prefix}:{event_type}"
        message = json.dumps(
            {
                "event_type": event_type,
                "source": "plant-service",
                "payload": payload,
            }
        )
        try:
            await self.redis.publish(channel, message)
            logger.info("event_published", event_type=event_type, channel=channel)
        except Exception as exc:
            logger.error(
                "event_publish_failed",
                event_type=event_type,
                error=str(exc),
            )

    async def publish_batch(
        self, events: list[tuple[str, dict[str, Any]]]
    ) -> None:
        async with self.redis.pipeline() as pipe:
            for event_type, payload in events:
                channel = f"{self.channel_prefix}:{event_type}"
                message = json.dumps(
                    {
                        "event_type": event_type,
                        "source": "plant-service",
                        "payload": payload,
                    }
                )
                pipe.publish(channel, message)
            await pipe.execute()
        logger.info("events_batch_published", count=len(events))
