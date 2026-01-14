"""Tests for monitor module."""

from unittest.mock import MagicMock, AsyncMock

import pytest

from usp_booking_bot.auth import USCAuth
from usp_booking_bot.config import Config, UserPreferences, TimeSlot, MonitoringConfig
from usp_booking_bot.monitor import Class, ClassMonitor


def test_class_initialization():
    """Test Class object initialization."""
    data = {
        "id": "123",
        "name": "Yoga Flow",
        "location": "Berlin Mitte",
        "activity": "Yoga",
        "start_time": "2024-01-15T18:00:00Z",
        "end_time": "2024-01-15T19:00:00Z",
        "available_slots": 5,
        "total_slots": 20,
        "instructor": "Jane Doe",
    }

    cls = Class(data)
    assert cls.id == "123"
    assert cls.name == "Yoga Flow"
    assert cls.location == "Berlin Mitte"
    assert cls.available_slots == 5


def test_class_matches_preferences():
    """Test class matching against preferences."""
    data = {
        "id": "123",
        "name": "Yoga Flow",
        "location": "Berlin Mitte",
        "activity": "Yoga",
        "start_time": "2024-01-16T18:30:00Z",  # Tuesday
        "available_slots": 5,
    }

    cls = Class(data)

    preferences = UserPreferences(
        locations=["Berlin Mitte"],
        activities=["Yoga"],
        days_of_week=[1],  # Tuesday
        time_slots=TimeSlot(start="18:00", end="21:00"),
    )

    assert cls.matches_preferences(preferences)


def test_class_does_not_match_location():
    """Test class not matching location preference."""
    data = {
        "id": "123",
        "name": "Yoga Flow",
        "location": "Berlin Kreuzberg",
        "activity": "Yoga",
        "start_time": "2024-01-16T18:30:00Z",
        "available_slots": 5,
    }

    cls = Class(data)

    preferences = UserPreferences(
        locations=["Berlin Mitte"],
        activities=["Yoga"],
        days_of_week=[1],
        time_slots=TimeSlot(start="18:00", end="21:00"),
    )

    assert not cls.matches_preferences(preferences)


@pytest.mark.asyncio
async def test_monitor_fetch_classes():
    """Test fetching classes from API."""
    mock_auth = MagicMock(spec=USCAuth)
    mock_auth.session = MagicMock()
    mock_auth.get_headers = MagicMock(return_value={"Authorization": "Bearer token"})

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={
            "classes": [
                {
                    "id": "1",
                    "name": "Yoga",
                    "location": "Berlin",
                    "start_time": "2024-01-15T18:00:00Z",
                    "available_slots": 5,
                }
            ]
        }
    )

    mock_auth.session.get = MagicMock(return_value=AsyncMock().__aenter__.return_value)
    mock_auth.session.get.return_value.__aenter__.return_value = mock_response

    config = Config(
        preferences=UserPreferences(
            locations=["Berlin"],
            activities=["Yoga"],
            days_of_week=[0, 1, 2, 3, 4, 5, 6],
            time_slots=TimeSlot(start="00:00", end="23:59"),
        ),
        monitoring=MonitoringConfig(),
    )

    monitor = ClassMonitor(mock_auth, config)
    classes = await monitor.fetch_classes()

    assert len(classes) == 1
    assert classes[0].name == "Yoga"


@pytest.mark.asyncio
async def test_monitor_book_class():
    """Test booking a class."""
    mock_auth = MagicMock(spec=USCAuth)
    mock_auth.session = MagicMock()
    mock_auth.get_headers = MagicMock(return_value={"Authorization": "Bearer token"})

    mock_response = MagicMock()
    mock_response.status = 201

    mock_auth.session.post = MagicMock(return_value=AsyncMock().__aenter__.return_value)
    mock_auth.session.post.return_value.__aenter__.return_value = mock_response

    config = Config(
        preferences=UserPreferences(
            locations=[],
            activities=[],
            days_of_week=[],
            time_slots=TimeSlot(start="00:00", end="23:59"),
        ),
        monitoring=MonitoringConfig(max_retries=1),
    )

    monitor = ClassMonitor(mock_auth, config)

    class_obj = Class(
        {
            "id": "123",
            "name": "Yoga",
            "location": "Berlin",
            "start_time": "2024-01-15T18:00:00Z",
        }
    )

    result = await monitor.book_class(class_obj)
    assert result is True
