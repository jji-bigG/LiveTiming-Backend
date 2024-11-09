from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class TimingData(BaseModel):
    device_id: str = Field(..., description="Unique identifier for the timing device")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    lap_time: float = Field(..., description="Lap time in seconds")
    sector: Optional[int] = Field(None, description="Sector number")
    segment: Optional[str] = Field(None, description="Segment identifier")


class SensorData(BaseModel):
    device_id: str = Field(..., description="Unique identifier for the sensor")
    sensor_type: str = Field(
        ..., description="Type of sensor (e.g., temperature, speed)"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    value: float = Field(..., description="Sensor reading value")
    unit: str = Field(..., description="Unit of measurement")


class TimingResponse(BaseModel):
    device_id: str
    latest_lap: float
    best_lap: Optional[float]
    last_update: datetime


class SensorResponse(BaseModel):
    device_id: str
    sensor_type: str
    latest_value: float
    unit: str
    last_update: datetime
