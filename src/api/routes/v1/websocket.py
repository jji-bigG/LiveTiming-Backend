# src/api/routes/v1/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
import logging
from services.redis_service import RedisService

# from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "timing": set(),
            "sensor": set(),
        }
        self.redis = RedisService()
        self._running = False

    async def connect(self, websocket: WebSocket, client_type: str):
        await websocket.accept()
        self.active_connections[client_type].add(websocket)
        logger.info(
            f"New {client_type} client connected. Total {client_type} clients: {len(self.active_connections[client_type])}"
        )

    def disconnect(self, websocket: WebSocket, client_type: str):
        self.active_connections[client_type].remove(websocket)
        logger.info(
            f"{client_type} client disconnected. Total {client_type} clients: {len(self.active_connections[client_type])}"
        )

    async def broadcast_to_clients(self, client_type: str, message: str):
        disconnected = set()
        for connection in self.active_connections[client_type]:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                disconnected.add(connection)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_type} client: {e}")
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn, client_type)

    async def subscribe_to_redis(self, channel: str, client_type: str):
        """Subscribe to Redis channel and broadcast messages to WebSocket clients"""
        try:
            pubsub = await self.redis.get_pubsub()
            await pubsub.subscribe(channel)
            logger.info(f"Subscribed to Redis channel: {channel}")

            while self._running:
                try:
                    message = await pubsub.get_message(ignore_subscribe_messages=True)
                    if message and message["type"] == "message":
                        await self.broadcast_to_clients(client_type, message["data"])
                except Exception as e:
                    logger.error(f"Error processing message from {channel}: {e}")
                    await asyncio.sleep(1)  # Prevent tight loop on errors
        except Exception as e:
            logger.error(f"Error in Redis subscription to {channel}: {e}")
        finally:
            await pubsub.unsubscribe(channel)
            logger.info(f"Unsubscribed from Redis channel: {channel}")

    async def start_redis_subscribers(self):
        """Start Redis pub/sub listeners for all channels"""
        self._running = True
        try:
            await asyncio.gather(
                self.subscribe_to_redis("timing_updates", "timing"),
                self.subscribe_to_redis("sensor_updates", "sensor"),
            )
        except Exception as e:
            logger.error(f"Error starting Redis subscribers: {e}")
            self._running = False

    async def shutdown(self):
        """Gracefully shutdown the connection manager"""
        self._running = False
        # Close all websocket connections
        for client_type in self.active_connections:
            for connection in self.active_connections[client_type].copy():
                try:
                    await connection.close()
                except Exception:
                    pass
            self.active_connections[client_type].clear()
        # Close Redis connection
        await self.redis.close()


manager = ConnectionManager()


@router.websocket("/timing")
async def websocket_timing_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "timing")
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, "timing")


@router.websocket("/sensor/{sensor_type}")
async def websocket_sensor_endpoint(websocket: WebSocket, sensor_type: str):
    await manager.connect(websocket, "sensor")
    try:
        while True:
            data = await websocket.receive_text()
            # Handle sensor-specific messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, "sensor")


# Startup and shutdown events
@router.on_event("startup")
async def startup_event():
    await manager.redis.get_connection()  # Initialize Redis connection
    asyncio.create_task(manager.start_redis_subscribers())


@router.on_event("shutdown")
async def shutdown_event():
    await manager.shutdown()
