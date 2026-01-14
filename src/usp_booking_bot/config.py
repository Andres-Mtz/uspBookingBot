"""Configuration management module for USP Booking Bot."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class TimeSlot(BaseModel):
    """Time slot configuration."""

    start: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end: str = Field(..., pattern=r"^\d{2}:\d{2}$")


class UserPreferences(BaseModel):
    """User preferences for class booking."""

    locations: list[str] = Field(default_factory=list)
    activities: list[str] = Field(default_factory=list)
    days_of_week: list[int] = Field(default_factory=list)
    time_slots: TimeSlot
    auto_book: bool = True
    max_bookings_per_week: int = 3

    @field_validator("days_of_week")
    @classmethod
    def validate_days(cls, v: list[int]) -> list[int]:
        """Validate days of week are between 0-6."""
        if not all(0 <= day <= 6 for day in v):
            raise ValueError("Days of week must be between 0 (Monday) and 6 (Sunday)")
        return v


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""

    check_interval: int = 5
    days_ahead: int = 7
    max_retries: int = 3
    retry_delay: int = 5


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    max_requests: int = 10
    period: int = 60


class NotificationChannel(BaseModel):
    """Individual notification channel settings."""

    enabled: bool = False


class NotificationsConfig(BaseModel):
    """Notifications configuration."""

    email: NotificationChannel = Field(default_factory=NotificationChannel)
    telegram: NotificationChannel = Field(default_factory=NotificationChannel)
    discord: NotificationChannel = Field(default_factory=NotificationChannel)
    notify_on: list[str] = Field(
        default_factory=lambda: [
            "slot_found",
            "booking_success",
            "booking_failure",
            "error",
        ]
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    format: str = "json"
    file: str = "logs/booking_bot.log"


class Config(BaseModel):
    """Main configuration model."""

    preferences: UserPreferences
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file. If None, uses default path.

    Returns:
        Parsed configuration object.

    Raises:
        FileNotFoundError: If configuration file doesn't exist.
        ValueError: If configuration is invalid.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config_dict: dict[str, Any] = yaml.safe_load(f)

    return Config(**config_dict)
