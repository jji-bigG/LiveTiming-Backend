from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Welcome to API v1"}


@router.get("/status")
async def status():
    return {"status": "operational"}
