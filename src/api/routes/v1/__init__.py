from .rest import router as rest_router
from .websocket import router as websocket_router
from fastapi import APIRouter

# Create a main v1 router that combines both REST and WebSocket routers
router = APIRouter()
router.include_router(rest_router, tags=["rest"])
router.include_router(websocket_router, prefix="/ws", tags=["websocket"])
