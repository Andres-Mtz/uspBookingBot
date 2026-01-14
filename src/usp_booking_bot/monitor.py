"""Class monitoring and booking functionality."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import structlog
from aiolimiter import AsyncLimiter

from .auth import USCAuth
from .config import Config, UserPreferences

logger = structlog.get_logger(__name__)


class Class:
    """Represents a sports class."""

    def __init__(self, data: Dict[str, Any]) -> None:
        """Initialize class from API data.

        Args:
            data: Raw class data from API.
        """
        self.id: str = data.get("id", "")
        self.name: str = data.get("name", "")
        self.location: str = data.get("location", "")
        self.activity: str = data.get("activity", "")
        self.start_time: datetime = self._parse_datetime(data.get("start_time"))
        self.end_time: datetime = self._parse_datetime(data.get("end_time"))
        self.available_slots: int = data.get("available_slots", 0)
        self.total_slots: int = data.get("total_slots", 0)
        self.instructor: str = data.get("instructor", "")

    @staticmethod
    def _parse_datetime(dt_str: Optional[str]) -> datetime:
        """Parse datetime string.

        Args:
            dt_str: ISO format datetime string.

        Returns:
            Parsed datetime object.
        """
        if not dt_str:
            return datetime.now()
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.now()

    def matches_preferences(self, preferences: UserPreferences) -> bool:
        """Check if class matches user preferences.

        Args:
            preferences: User preferences to match against.

        Returns:
            True if class matches preferences, False otherwise.
        """
        # Check location
        if preferences.locations and self.location not in preferences.locations:
            return False

        # Check activity
        if preferences.activities and self.activity not in preferences.activities:
            return False

        # Check day of week
        if preferences.days_of_week:
            weekday = self.start_time.weekday()
            if weekday not in preferences.days_of_week:
                return False

        # Check time slot
        class_time = self.start_time.strftime("%H:%M")
        if not (preferences.time_slots.start <= class_time <= preferences.time_slots.end):
            return False

        return True

    def __repr__(self) -> str:
        """String representation of class."""
        return (
            f"Class(id={self.id}, name={self.name}, location={self.location}, "
            f"start={self.start_time}, slots={self.available_slots}/{self.total_slots})"
        )


class ClassMonitor:
    """Monitors classes for available slots."""

    BASE_URL = "https://urbansportsclub.com/api"

    def __init__(
        self,
        auth: USCAuth,
        config: Config,
        rate_limiter: Optional[AsyncLimiter] = None,
    ) -> None:
        """Initialize class monitor.

        Args:
            auth: Authentication instance.
            config: Configuration object.
            rate_limiter: Optional rate limiter for API calls.
        """
        self.auth = auth
        self.config = config
        self.rate_limiter = rate_limiter or AsyncLimiter(
            max_rate=config.rate_limit.max_requests,
            time_period=config.rate_limit.period,
        )

    async def fetch_classes(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Class]:
        """Fetch available classes from API.

        Args:
            start_date: Start date for class search.
            end_date: End date for class search.

        Returns:
            List of available classes.
        """
        if start_date is None:
            start_date = datetime.now()
        if end_date is None:
            end_date = start_date + timedelta(days=self.config.monitoring.days_ahead)

        async with self.rate_limiter:
            try:
                params = {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                }

                async with self.auth.session.get(
                    f"{self.BASE_URL}/classes",
                    headers=self.auth.get_headers(),
                    params=params,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        classes = [Class(c) for c in data.get("classes", [])]
                        logger.info(f"Fetched {len(classes)} classes")
                        return classes
                    else:
                        error_text = await response.text()
                        logger.error(
                            "Failed to fetch classes",
                            status=response.status,
                            error=error_text,
                        )
                        return []
            except aiohttp.ClientError as e:
                logger.error("Network error fetching classes", error=str(e))
                return []

    async def find_matching_classes(self) -> List[Class]:
        """Find classes matching user preferences.

        Returns:
            List of classes matching preferences with available slots.
        """
        all_classes = await self.fetch_classes()
        matching_classes = [
            cls
            for cls in all_classes
            if cls.available_slots > 0
            and cls.matches_preferences(self.config.preferences)
        ]

        logger.info(
            f"Found {len(matching_classes)} matching classes with available slots"
        )
        return matching_classes

    async def book_class(self, class_obj: Class) -> bool:
        """Book a specific class.

        Args:
            class_obj: Class to book.

        Returns:
            True if booking successful, False otherwise.
        """
        async with self.rate_limiter:
            for attempt in range(self.config.monitoring.max_retries):
                try:
                    async with self.auth.session.post(
                        f"{self.BASE_URL}/bookings",
                        headers=self.auth.get_headers(),
                        json={"class_id": class_obj.id},
                    ) as response:
                        if response.status in (200, 201):
                            logger.info(
                                "Successfully booked class",
                                class_id=class_obj.id,
                                class_name=class_obj.name,
                            )
                            return True
                        elif response.status == 401:
                            # Token expired, try to refresh
                            logger.warning("Token expired, refreshing...")
                            await self.auth.refresh_session()
                        else:
                            error_text = await response.text()
                            logger.error(
                                "Booking failed",
                                status=response.status,
                                error=error_text,
                                attempt=attempt + 1,
                            )

                    if attempt < self.config.monitoring.max_retries - 1:
                        await asyncio.sleep(self.config.monitoring.retry_delay)

                except aiohttp.ClientError as e:
                    logger.error(
                        "Network error during booking",
                        error=str(e),
                        attempt=attempt + 1,
                    )
                    if attempt < self.config.monitoring.max_retries - 1:
                        await asyncio.sleep(self.config.monitoring.retry_delay)

        return False
