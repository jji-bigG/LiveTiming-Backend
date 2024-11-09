# src/services/redis_service.py
import redis.asyncio as redis
import logging
import json
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)


class RedisService:
    def __init__(self):
        self.redis_url = (
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        )
        self.redis: Optional[redis.Redis] = None

    async def get_connection(self) -> redis.Redis:
        """Get or create Redis connection"""
        if self.redis is None:
            try:
                self.redis = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                )
                await self.redis.ping()
                logger.info("Successfully connected to Redis")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return self.redis

    async def get_pubsub(self) -> redis.client.PubSub:
        """Get Redis Pub/Sub client"""
        redis_client = await self.get_connection()
        return redis_client.pubsub()

    async def publish(self, channel: str, message: dict) -> None:
        """Publish message to a channel"""
        try:
            redis_client = await self.get_connection()
            await redis_client.publish(channel, json.dumps(message))
            logger.debug(f"Published message to {channel}: {message}")
        except Exception as e:
            logger.error(f"Error publishing to {channel}: {e}")
            raise

    async def close(self) -> None:
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.get_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
