"""Setup script for USP Booking Bot."""

from setuptools import setup, find_packages

setup(
    name="usp-booking-bot",
    version="0.1.0",
    description="Automated booking bot for Urban Sports Club",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "aiohttp>=3.9.0",
        "pydantic>=2.5.0",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
        "apscheduler>=3.10.4",
        "aiosmtplib>=3.0.1",
        "python-telegram-bot>=20.7",
        "discord-webhook>=1.3.0",
        "aiolimiter>=1.1.0",
        "typing-extensions>=4.9.0",
        "structlog>=24.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "mypy>=1.7.0",
            "flake8>=6.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "usp-booking-bot=usp_booking_bot.main:main",
        ],
    },
)
