import redis
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from config import settings
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

    def _test_connection(self):
        try:
            self.redis_client.ping()
            logger.info("Successfully connected to Redis")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def store_timing_data(self, device_id: str, data: Dict[str, Any]):
        """Store timing data in Redis"""
        key = f"timing:{device_id}"
        try:
            # Store latest lap time
            self.redis_client.hset(
                key,
                mapping={
                    "latest_lap": data["lap_time"],
                    "last_update": datetime.utcnow().isoformat(),
                },
            )

            # Update best lap if necessary
            current_best = self.redis_client.hget(key, "best_lap")
            if not current_best or float(data["lap_time"]) < float(current_best):
                self.redis_client.hset(key, "best_lap", data["lap_time"])

        except Exception as e:
            logger.error(f"Error storing timing data: {e}")
            raise

    async def store_sensor_data(self, device_id: str, data: Dict[str, Any]):
        """Store sensor data in Redis"""
        key = f"sensor:{device_id}:{data['sensor_type']}"
        try:
            self.redis_client.hset(
                key,
                mapping={
                    "latest_value": data["value"],
                    "unit": data["unit"],
                    "last_update": datetime.utcnow().isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"Error storing sensor data: {e}")
            raise

    async def get_timing_data(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve timing data for a specific device"""
        key = f"timing:{device_id}"
        try:
            data = self.redis_client.hgetall(key)
            if not data:
                return None
            return {
                "device_id": device_id,
                "latest_lap": float(data["latest_lap"]),
                "best_lap": float(data["best_lap"]) if "best_lap" in data else None,
                "last_update": datetime.fromisoformat(data["last_update"]),
            }
        except Exception as e:
            logger.error(f"Error retrieving timing data: {e}")
            raise

    async def get_all_timing_data(self) -> List[Dict[str, Any]]:
        """Retrieve timing data for all devices"""
        try:
            keys = self.redis_client.keys("timing:*")
            result = []
            for key in keys:
                device_id = key.split(":")[1]
                data = await self.get_timing_data(device_id)
                if data:
                    result.append(data)
            return result
        except Exception as e:
            logger.error(f"Error retrieving all timing data: {e}")
            raise
