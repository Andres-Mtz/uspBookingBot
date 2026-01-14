"""Notification system for booking events."""

import os
from abc import ABC, abstractmethod
from typing import List, Optional

import aiosmtplib
import structlog
from aiohttp import ClientSession
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Bot
from telegram.error import TelegramError

logger = structlog.get_logger(__name__)


class NotificationProvider(ABC):
    """Abstract base class for notification providers."""

    @abstractmethod
    async def send(self, subject: str, message: str) -> bool:
        """Send notification.

        Args:
            subject: Notification subject/title.
            message: Notification message body.

        Returns:
            True if notification was sent successfully, False otherwise.
        """
        pass


class EmailNotifier(NotificationProvider):
    """Email notification provider."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        recipient: Optional[str] = None,
    ) -> None:
        """Initialize email notifier.

        Args:
            smtp_host: SMTP server host.
            smtp_port: SMTP server port.
            username: SMTP username.
            password: SMTP password.
            recipient: Email recipient address.
        """
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.username = username or os.getenv("SMTP_USERNAME", "")
        self.password = password or os.getenv("SMTP_PASSWORD", "")
        self.recipient = recipient or os.getenv("NOTIFICATION_EMAIL", "")

    async def send(self, subject: str, message: str) -> bool:
        """Send email notification."""
        if not all([self.username, self.password, self.recipient]):
            logger.warning(
                "Email credentials not configured, skipping email notification"
            )
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["To"] = self.recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "plain"))

            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                start_tls=True,
            )

            logger.info("Email notification sent", subject=subject)
            return True
        except Exception as e:
            logger.error("Failed to send email notification", error=str(e))
            return False


class TelegramNotifier(NotificationProvider):
    """Telegram notification provider."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ) -> None:
        """Initialize Telegram notifier.

        Args:
            bot_token: Telegram bot token.
            chat_id: Telegram chat ID.
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self.bot: Optional[Bot] = None

        if self.bot_token:
            self.bot = Bot(token=self.bot_token)

    async def send(self, subject: str, message: str) -> bool:
        """Send Telegram notification."""
        if not self.bot or not self.chat_id:
            logger.warning("Telegram not configured, skipping notification")
            return False

        try:
            full_message = f"*{subject}*\n\n{message}"
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=full_message,
                parse_mode="Markdown",
            )
            logger.info("Telegram notification sent", subject=subject)
            return True
        except TelegramError as e:
            logger.error("Failed to send Telegram notification", error=str(e))
            return False


class DiscordNotifier(NotificationProvider):
    """Discord webhook notification provider."""

    def __init__(self, webhook_url: Optional[str] = None) -> None:
        """Initialize Discord notifier.

        Args:
            webhook_url: Discord webhook URL.
        """
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL", "")

    async def send(self, subject: str, message: str) -> bool:
        """Send Discord notification."""
        if not self.webhook_url:
            logger.warning("Discord webhook not configured, skipping notification")
            return False

        try:
            async with ClientSession() as session:
                payload = {
                    "content": f"**{subject}**\n\n{message}",
                }
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status in (200, 204):
                        logger.info("Discord notification sent", subject=subject)
                        return True
                    else:
                        logger.error(
                            "Discord notification failed",
                            status=response.status,
                        )
                        return False
        except Exception as e:
            logger.error("Failed to send Discord notification", error=str(e))
            return False


class NotificationManager:
    """Manages multiple notification providers."""

    def __init__(self) -> None:
        """Initialize notification manager."""
        self.providers: List[NotificationProvider] = []

    def add_provider(self, provider: NotificationProvider) -> None:
        """Add a notification provider.

        Args:
            provider: Notification provider to add.
        """
        self.providers.append(provider)

    async def notify(self, subject: str, message: str) -> None:
        """Send notification through all configured providers.

        Args:
            subject: Notification subject/title.
            message: Notification message body.
        """
        if not self.providers:
            logger.warning("No notification providers configured")
            return

        for provider in self.providers:
            await provider.send(subject, message)
