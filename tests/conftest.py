"""
Pytest Configuration and Fixtures
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "password": "Test@123456",
        "full_name": "Test User"
    }


@pytest.fixture
def test_event_data():
    """Sample authentication event for testing"""
    return {
        "user_identifier": "test@example.com",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0",
        "status": "success",
        "timestamp": "2026-11-15T10:00:00Z",
        "country": "USA",
        "city": "New York",
        "latitude": 40.7128,
        "longitude": -74.0060
    }


@pytest.fixture
def malicious_ip_event():
    """Malicious IP event for testing threat detection"""
    return {
        "user_identifier": "victim@example.com",
        "ip_address": "203.0.113.50",  # Known malicious
        "user_agent": "BadBot/1.0",
        "status": "failed",
        "timestamp": "2026-11-15T10:00:00Z",
        "country": "Russia",
        "city": "Moscow",
        "latitude": 55.7558,
        "longitude": 37.6173
    }


@pytest.fixture
def brute_force_events():
    """Multiple failed login attempts"""
    return [
        {
            "user_identifier": "admin@example.com",
            "ip_address": "203.0.113.50",
            "status": "failed",
            "timestamp": f"2026-11-15T10:00:{i:02d}Z"
        }
        for i in range(6)
    ]


@pytest.fixture
def impossible_travel_events():
    """Events showing impossible travel"""
    return [
        {
            "user_identifier": "user@example.com",
            "ip_address": "103.1.1.1",
            "country": "India",
            "city": "Mumbai",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "timestamp": "2026-11-15T10:00:00Z",
            "status": "success"
        },
        {
            "user_identifier": "user@example.com",
            "ip_address": "192.0.2.1",
            "country": "USA",
            "city": "New York",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "timestamp": "2026-11-15T10:05:00Z",
            "status": "success"
        }
    ]
