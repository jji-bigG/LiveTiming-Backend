import redis.asyncio as redis
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class RedisService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
        self._test_connection()

    async def _test_connection(self):
        try:
            await self.redis_client.ping()
            logger.info("Successfully connected to Redis")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def get_pubsub(self):
        """Get Redis Pub/Sub connection"""
        return self.redis_client.pubsub()

    async def publish_timing_update(self, data: Dict[str, Any]):
        """Publish timing update to Redis channel"""
        try:
            message = json.dumps(data)
            await self.redis_client.publish("timing_updates", message)
        except Exception as e:
            logger.error(f"Error publishing timing update: {e}")
            raise

    async def publish_sensor_update(self, data: Dict[str, Any]):
        """Publish sensor update to Redis channel"""
        try:
            message = json.dumps(data)
            await self.redis_client.publish("sensor_updates", message)
        except Exception as e:
            logger.error(f"Error publishing sensor update: {e}")
            raise

    async def store_timing_data(self, device_id: str, data: Dict[str, Any]):
        """Store timing data and publish update"""
        try:
            key = f"timing:{device_id}"
            # Store latest lap time
            await self.redis_client.hset(
                key,
                mapping={
                    "latest_lap": data["lap_time"],
                    "last_update": datetime.utcnow().isoformat(),
                },
            )

            # Update best lap if necessary
            current_best = await self.redis_client.hget(key, "best_lap")
            if not current_best or float(data["lap_time"]) < float(current_best):
                await self.redis_client.hset(key, "best_lap", data["lap_time"])

            # Publish update
            await self.publish_timing_update(
                {"device_id": device_id, "type": "timing_update", "data": data}
            )

        except Exception as e:
            logger.error(f"Error storing timing data: {e}")
            raise

    async def store_sensor_data(self, device_id: str, data: Dict[str, Any]):
        """Store sensor data and publish update"""
        try:
            key = f"sensor:{device_id}:{data['sensor_type']}"
            await self.redis_client.hset(
                key,
                mapping={
                    "latest_value": data["value"],
                    "unit": data["unit"],
                    "last_update": datetime.utcnow().isoformat(),
                },
            )

            # Publish update
            await self.publish_sensor_update(
                {"device_id": device_id, "type": "sensor_update", "data": data}
            )

        except Exception as e:
            logger.error(f"Error storing sensor data: {e}")
            raise

    # ... rest of the Redis service methods ...
