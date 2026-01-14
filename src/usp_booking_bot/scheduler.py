"""Scheduler for automated class monitoring and booking."""

import asyncio
from datetime import datetime
from typing import Optional

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .auth import USCAuth
from .config import Config, load_config
from .monitor import ClassMonitor
from .notifications import (
    NotificationManager,
    EmailNotifier,
    TelegramNotifier,
    DiscordNotifier,
)

logger = structlog.get_logger(__name__)


class BookingScheduler:
    """Schedules and manages automated class booking."""

    def __init__(self, config: Optional[Config] = None) -> None:
        """Initialize booking scheduler.

        Args:
            config: Configuration object. If None, loads from default path.
        """
        self.config = config or load_config()
        self.scheduler = AsyncIOScheduler()
        self.auth: Optional[USCAuth] = None
        self.monitor: Optional[ClassMonitor] = None
        self.notifier = NotificationManager()
        self._setup_notifications()
        self._running = False

    def _setup_notifications(self) -> None:
        """Set up notification providers based on configuration."""
        if self.config.notifications.email.enabled:
            self.notifier.add_provider(EmailNotifier())
            logger.info("Email notifications enabled")

        if self.config.notifications.telegram.enabled:
            self.notifier.add_provider(TelegramNotifier())
            logger.info("Telegram notifications enabled")

        if self.config.notifications.discord.enabled:
            self.notifier.add_provider(DiscordNotifier())
            logger.info("Discord notifications enabled")

    async def initialize(self) -> None:
        """Initialize authentication and monitor."""
        try:
            self.auth = USCAuth()
            await self.auth.login()
            self.monitor = ClassMonitor(self.auth, self.config)
            logger.info("Scheduler initialized successfully")

            await self.notifier.notify(
                "Booking Bot Started",
                f"The USC Booking Bot has started monitoring at {datetime.now().isoformat()}",
            )
        except Exception as e:
            logger.error("Failed to initialize scheduler", error=str(e))
            await self.notifier.notify(
                "Booking Bot Error",
                f"Failed to initialize: {str(e)}",
            )
            raise

    async def check_and_book(self) -> None:
        """Check for available classes and book if preferences match."""
        if not self.monitor:
            logger.error("Monitor not initialized")
            return

        try:
            logger.info("Checking for available classes...")
            matching_classes = await self.monitor.find_matching_classes()

            if not matching_classes:
                logger.debug("No matching classes found")
                return

            # Notify about found slots
            if "slot_found" in self.config.notifications.notify_on:
                classes_info = "\n".join(
                    [
                        f"- {cls.name} at {cls.location} ({cls.start_time.strftime('%Y-%m-%d %H:%M')})"
                        for cls in matching_classes
                    ]
                )
                await self.notifier.notify(
                    "Available Classes Found",
                    f"Found {len(matching_classes)} matching classes:\n\n{classes_info}",
                )

            # Auto-book if enabled
            if self.config.preferences.auto_book:
                for class_obj in matching_classes[
                    : self.config.preferences.max_bookings_per_week
                ]:
                    success = await self.monitor.book_class(class_obj)

                    if success and "booking_success" in self.config.notifications.notify_on:
                        await self.notifier.notify(
                            "Class Booked Successfully",
                            f"Successfully booked: {class_obj.name}\n"
                            f"Location: {class_obj.location}\n"
                            f"Time: {class_obj.start_time.strftime('%Y-%m-%d %H:%M')}",
                        )
                    elif not success and "booking_failure" in self.config.notifications.notify_on:
                        await self.notifier.notify(
                            "Booking Failed",
                            f"Failed to book: {class_obj.name}\n"
                            f"Location: {class_obj.location}\n"
                            f"Time: {class_obj.start_time.strftime('%Y-%m-%d %H:%M')}",
                        )

        except Exception as e:
            logger.error("Error during check and book", error=str(e))
            if "error" in self.config.notifications.notify_on:
                await self.notifier.notify(
                    "Booking Bot Error",
                    f"An error occurred: {str(e)}",
                )

    def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        self.scheduler.add_job(
            self.check_and_book,
            trigger=IntervalTrigger(minutes=self.config.monitoring.check_interval),
            id="check_and_book",
            name="Check for classes and book",
            replace_existing=True,
        )

        self.scheduler.start()
        self._running = True
        logger.info(
            "Scheduler started",
            check_interval=self.config.monitoring.check_interval,
        )

    def stop(self) -> None:
        """Stop the scheduler."""
        if not self._running:
            logger.warning("Scheduler is not running")
            return

        self.scheduler.shutdown()
        self._running = False
        logger.info("Scheduler stopped")

    async def run(self) -> None:
        """Run the scheduler (blocking)."""
        await self.initialize()
        self.start()

        try:
            # Keep the scheduler running
            while self._running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        finally:
            self.stop()
            if self.auth:
                await self.auth.close()
            await self.notifier.notify(
                "Booking Bot Stopped",
                f"The USC Booking Bot has stopped at {datetime.now().isoformat()}",
            )
