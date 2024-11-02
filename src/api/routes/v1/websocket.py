from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set, Optional
import json
import asyncio
import logging
from services.redis_service import RedisService
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "timing": set(),
            "sensor": set(),
        }
        self.redis = RedisService()

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

    async def broadcast_to_timing_clients(self, message: str):
        disconnected = set()
        for connection in self.active_connections["timing"]:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn, "timing")

    async def broadcast_to_sensor_clients(self, message: str):
        disconnected = set()
        for connection in self.active_connections["sensor"]:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn, "sensor")

    async def start_redis_subscribers(self):
        """Start Redis pub/sub listeners for all channels"""
        await asyncio.gather(
            self.subscribe_to_redis("timing_updates"),
            self.subscribe_to_redis("sensor_updates"),
        )

    async def subscribe_to_redis(self, channel: str):
        """Subscribe to Redis channel and broadcast messages to WebSocket clients"""
        pubsub = self.redis.get_pubsub()
        await pubsub.subscribe(channel)

        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message and message["type"] == "message":
                    data = message["data"]
                    if channel == "timing_updates":
                        await self.broadcast_to_timing_clients(data)
                    elif channel == "sensor_updates":
                        await self.broadcast_to_sensor_clients(data)
        except Exception as e:
            logger.error(f"Error in Redis subscription: {e}")
        finally:
            await pubsub.unsubscribe(channel)


manager = ConnectionManager()


@router.websocket("/ws/timing")
async def websocket_timing_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "timing")
    try:
        while True:
            # Keep connection alive and handle incoming messages if needed
            data = await websocket.receive_text()
            # You can handle incoming messages here if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, "timing")


@router.websocket("/ws/sensor/{sensor_type}")
async def websocket_sensor_endpoint(websocket: WebSocket, sensor_type: str):
    await manager.connect(websocket, "sensor")
    try:
        while True:
            data = await websocket.receive_text()
            # Handle any specific sensor type filtering here
    except WebSocketDisconnect:
        manager.disconnect(websocket, "sensor")


# Start Redis subscribers when the application starts
@router.on_event("startup")
async def startup_event():
    asyncio.create_task(manager.start_redis_subscribers())
