#!/usr/bin/env python3
"""Quick validation script for USP Booking Bot setup."""

import sys
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✓ {description}")
        return True
    else:
        print(f"✗ {description} - MISSING")
        return False


def main() -> int:
    """Validate project setup."""
    print("=" * 60)
    print("USP Booking Bot - Setup Validation")
    print("=" * 60)
    print()

    checks = [
        ("config/config.yaml", "Configuration file"),
        (".env.example", "Environment template"),
        ("requirements.txt", "Python dependencies"),
        ("Dockerfile", "Docker configuration"),
        ("docker-compose.yml", "Docker Compose configuration"),
        ("src/usp_booking_bot/main.py", "Main application entry point"),
        ("src/usp_booking_bot/auth.py", "Authentication module"),
        ("src/usp_booking_bot/config.py", "Configuration module"),
        ("src/usp_booking_bot/monitor.py", "Class monitoring module"),
        ("src/usp_booking_bot/scheduler.py", "Scheduler module"),
        ("src/usp_booking_bot/notifications.py", "Notifications module"),
        ("tests/test_auth.py", "Authentication tests"),
        ("tests/test_config.py", "Configuration tests"),
        ("tests/test_monitor.py", "Monitor tests"),
    ]

    all_passed = all(check_file_exists(filepath, desc) for filepath, desc in checks)

    print()
    print("=" * 60)

    if all_passed:
        print("✓ All checks passed! Your setup is complete.")
        print()
        print("Next steps:")
        print("1. Copy .env.example to .env and fill in your credentials")
        print("2. Customize config/config.yaml with your preferences")
        print("3. Run: python -m src.usp_booking_bot.main")
        print("   or")
        print("   docker-compose up -d")
        return 0
    else:
        print("✗ Some checks failed. Please review the missing files.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
