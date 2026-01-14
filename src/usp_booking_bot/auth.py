"""Authentication and session management for Urban Sports Club."""

from __future__ import annotations

import os
from typing import Optional

import aiohttp
import structlog
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = structlog.get_logger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class USCAuth:
    """Urban Sports Club authentication and session management."""

    BASE_URL = "https://urbansportsclub.com/api"
    LOGIN_ENDPOINT = "/auth/login"

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        """Initialize USC authentication.

        Args:
            email: User email. If None, reads from USC_EMAIL env var.
            password: User password. If None, reads from USC_PASSWORD env var.
            session: Optional aiohttp session. If None, creates new session.
        """
        self.email = email or os.getenv("USC_EMAIL")
        self.password = password or os.getenv("USC_PASSWORD")

        if not self.email or not self.password:
            raise ValueError("Email and password must be provided or set in .env file")

        self._session = session
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self._access_token is not None

    async def login(self) -> None:
        """Authenticate with Urban Sports Club.

        Raises:
            AuthenticationError: If authentication fails.
        """
        logger.info("Attempting to authenticate", email=self.email)

        try:
            async with self.session.post(
                f"{self.BASE_URL}{self.LOGIN_ENDPOINT}",
                json={"email": self.email, "password": self.password},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self._access_token = data.get("access_token")
                    self._refresh_token = data.get("refresh_token")
                    logger.info("Authentication successful")
                else:
                    error_text = await response.text()
                    logger.error(
                        "Authentication failed",
                        status=response.status,
                        error=error_text,
                    )
                    raise AuthenticationError(
                        f"Authentication failed: {response.status} - {error_text}"
                    )
        except aiohttp.ClientError as e:
            logger.error("Network error during authentication", error=str(e))
            raise AuthenticationError(f"Network error: {e}") from e

    async def refresh_session(self) -> None:
        """Refresh authentication token.

        Raises:
            AuthenticationError: If token refresh fails.
        """
        if not self._refresh_token:
            raise AuthenticationError("No refresh token available")

        logger.info("Refreshing authentication token")

        try:
            async with self.session.post(
                f"{self.BASE_URL}/auth/refresh",
                json={"refresh_token": self._refresh_token},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self._access_token = data.get("access_token")
                    logger.info("Token refresh successful")
                else:
                    error_text = await response.text()
                    logger.error(
                        "Token refresh failed",
                        status=response.status,
                        error=error_text,
                    )
                    raise AuthenticationError(f"Token refresh failed: {error_text}")
        except aiohttp.ClientError as e:
            logger.error("Network error during token refresh", error=str(e))
            raise AuthenticationError(f"Network error: {e}") from e

    def get_headers(self) -> dict[str, str]:
        """Get authorization headers for API requests.

        Returns:
            Dictionary with authorization headers.

        Raises:
            AuthenticationError: If not authenticated.
        """
        if not self.is_authenticated:
            raise AuthenticationError("Not authenticated. Call login() first.")

        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session is not None:
            await self._session.close()
            logger.info("Session closed")

    async def __aenter__(self) -> "USCAuth":
        """Async context manager entry."""
        await self.login()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
