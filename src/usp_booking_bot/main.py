"""Main entry point for the USP Booking Bot."""

import asyncio
import sys

import structlog

from usp_booking_bot.config import load_config
from usp_booking_bot.logging_config import setup_logging
from usp_booking_bot.scheduler import BookingScheduler

logger = structlog.get_logger(__name__)


async def main() -> None:
    """Main application entry point."""
    try:
        # Load configuration
        config = load_config()

        # Setup logging based on config
        setup_logging(
            log_level=config.logging.level,
            log_file=config.logging.file,
        )

        logger.info("Starting USC Booking Bot")

        # Create and run scheduler
        scheduler = BookingScheduler(config)
        await scheduler.run()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error("Fatal error", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
