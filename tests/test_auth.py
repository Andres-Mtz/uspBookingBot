"""Tests for authentication module."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientSession

from usp_booking_bot.auth import USCAuth, AuthenticationError


@pytest.fixture
def mock_env():
    """Mock environment variables."""
    with patch.dict(
        os.environ,
        {
            "USC_EMAIL": "test@example.com",
            "USC_PASSWORD": "testpass",
        },
    ):
        yield


@pytest.mark.asyncio
async def test_auth_initialization(mock_env):
    """Test authentication initialization."""
    auth = USCAuth()
    assert auth.email == "test@example.com"
    assert auth.password == "testpass"
    assert not auth.is_authenticated


@pytest.mark.asyncio
async def test_auth_missing_credentials():
    """Test authentication with missing credentials."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError):
            USCAuth()


@pytest.mark.asyncio
async def test_successful_login(mock_env):
    """Test successful login."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }
    )

    mock_session = MagicMock(spec=ClientSession)
    mock_session.post = MagicMock(return_value=AsyncMock().__aenter__.return_value)
    mock_session.post.return_value.__aenter__.return_value = mock_response

    auth = USCAuth()
    auth._session = mock_session

    await auth.login()

    assert auth.is_authenticated
    assert auth._access_token == "test_access_token"


@pytest.mark.asyncio
async def test_failed_login(mock_env):
    """Test failed login."""
    mock_response = MagicMock()
    mock_response.status = 401
    mock_response.text = AsyncMock(return_value="Invalid credentials")

    mock_session = MagicMock(spec=ClientSession)
    mock_session.post = MagicMock(return_value=AsyncMock().__aenter__.return_value)
    mock_session.post.return_value.__aenter__.return_value = mock_response

    auth = USCAuth()
    auth._session = mock_session

    with pytest.raises(AuthenticationError):
        await auth.login()


@pytest.mark.asyncio
async def test_get_headers_without_auth(mock_env):
    """Test getting headers without authentication."""
    auth = USCAuth()

    with pytest.raises(AuthenticationError):
        auth.get_headers()


@pytest.mark.asyncio
async def test_get_headers_with_auth(mock_env):
    """Test getting headers with authentication."""
    auth = USCAuth()
    auth._access_token = "test_token"

    headers = auth.get_headers()

    assert headers["Authorization"] == "Bearer test_token"
    assert headers["Content-Type"] == "application/json"
