"""Tests for configuration module."""

import tempfile
from pathlib import Path

import pytest
import yaml

from usp_booking_bot.config import (
    load_config,
    TimeSlot,
    UserPreferences,
)


def test_time_slot_validation():
    """Test time slot validation."""
    # Valid time slot
    ts = TimeSlot(start="09:00", end="18:00")
    assert ts.start == "09:00"
    assert ts.end == "18:00"

    # Invalid format
    with pytest.raises(ValueError):
        TimeSlot(start="9:00", end="18:00")


def test_user_preferences_days_validation():
    """Test days of week validation."""
    ts = TimeSlot(start="09:00", end="18:00")

    # Valid days
    prefs = UserPreferences(
        days_of_week=[0, 1, 6],
        time_slots=ts,
    )
    assert prefs.days_of_week == [0, 1, 6]

    # Invalid day
    with pytest.raises(ValueError):
        UserPreferences(
            days_of_week=[0, 7],  # 7 is invalid
            time_slots=ts,
        )


def test_load_config():
    """Test loading configuration from YAML file."""
    config_data = {
        "preferences": {
            "locations": ["Berlin Mitte"],
            "activities": ["Yoga"],
            "days_of_week": [1, 3],
            "time_slots": {"start": "18:00", "end": "21:00"},
            "auto_book": True,
            "max_bookings_per_week": 3,
        },
        "monitoring": {
            "check_interval": 5,
            "days_ahead": 7,
        },
    }

    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = Path(f.name)

    try:
        config = load_config(temp_path)
        assert config.preferences.locations == ["Berlin Mitte"]
        assert config.preferences.activities == ["Yoga"]
        assert config.preferences.auto_book is True
        assert config.monitoring.check_interval == 5
    finally:
        temp_path.unlink()


def test_config_defaults():
    """Test default configuration values."""
    config_data = {
        "preferences": {
            "locations": [],
            "activities": [],
            "days_of_week": [],
            "time_slots": {"start": "00:00", "end": "23:59"},
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = Path(f.name)

    try:
        config = load_config(temp_path)
        assert config.monitoring.check_interval == 5
        assert config.rate_limit.max_requests == 10
        assert config.notifications.email.enabled is False
    finally:
        temp_path.unlink()
