import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.services.redis_service import RedisService
from datetime import datetime

client = TestClient(app)


@pytest.fixture
def redis_service():
    return RedisService()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_timing_data_not_found():
    response = client.get("/api/v1/timing/nonexistent-device")
    assert response.status_code == 404


def test_get_timing_data(redis_service):
    # Setup test data
    device_id = "test-device"
    test_data = {
        "lap_time": 123.456,
        "sector": 1,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Store test data in Redis
    redis_service.store_timing_data(device_id, test_data)

    # Test API endpoint
    response = client.get(f"/api/v1/timing/{device_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == device_id
    assert data["latest_lap"] == test_data["lap_time"]


def test_get_sensor_data(redis_service):
    # Setup test data
    device_id = "test-sensor"
    test_data = {
        "sensor_type": "temperature",
        "value": 75.5,
        "unit": "C",
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Store test data in Redis
    redis_service.store_sensor_data(device_id, test_data)

    # Test API endpoint
    response = client.get(f"/api/v1/sensor/{device_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["device_id"] == device_id
    assert data[0]["sensor_type"] == test_data["sensor_type"]
    assert data[0]["latest_value"] == test_data["value"]
