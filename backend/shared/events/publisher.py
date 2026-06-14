import json
from datetime import datetime
from shared.database.connection import get_redis

class EventPublisher:
    @staticmethod
    async def publish(channel: str, event_type: str, payload: dict):
        redis = await get_redis()
        message = {
            "type": event_type,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await redis.publish(channel, json.dumps(message, default=str))

    @staticmethod
    async def subscribe(channel: str):
        redis = await get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)
        return pubsub
