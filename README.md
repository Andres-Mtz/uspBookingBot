# Urban Sports Club Booking Bot

An automated Python application that monitors Urban Sports Club (USC) classes and automatically books them when slots become available based on your preferences.

## Features

- **Secure Authentication**: Session management with environment variables
- **Async Scheduler**: Periodic monitoring using APScheduler
- **Smart Booking**: Auto-book classes matching your preferences (location, activity, time)
- **Multi-Channel Notifications**: Email, Telegram, and Discord support
- **YAML Configuration**: Easy-to-configure preferences
- **Rate Limiting**: Respects API limits with aiolimiter
- **Structured Logging**: JSON and console logging with structlog
- **Docker Support**: Containerized deployment ready
- **Type Safe**: Full type hints with mypy compatibility
- **PEP8 Compliant**: Follows Python best practices

## Project Structure

```
uspBookingBot/
├── src/
│   └── usp_booking_bot/
│       ├── __init__.py
│       ├── main.py              # Application entry point
│       ├── auth.py              # Authentication & session management
│       ├── config.py            # Configuration models
│       ├── monitor.py           # Class monitoring & booking
│       ├── scheduler.py         # Scheduling logic
│       ├── notifications.py     # Notification providers
│       └── logging_config.py    # Logging setup
├── tests/                       # Test files
├── config/
│   └── config.yaml             # User preferences & settings
├── logs/                       # Application logs
├── .env.example                # Environment variables template
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker Compose configuration
└── README.md                   # This file

```

## Installation

### Local Setup

1. **Clone the repository**:
```bash
git clone https://github.com/Andres-Mtz/uspBookingBot.git
cd uspBookingBot
```

2. **Create a virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Configure preferences**:
Edit `config/config.yaml` to set your preferred locations, activities, time slots, etc.

### Docker Setup

1. **Build the Docker image**:
```bash
docker-compose build
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Run the container**:
```bash
docker-compose up -d
```

## Configuration

### Environment Variables (.env)

Required credentials and settings:

```bash
# Urban Sports Club Credentials
USC_EMAIL=your-email@example.com
USC_PASSWORD=your-password

# Email Notifications (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
NOTIFICATION_EMAIL=recipient@example.com

# Telegram Notifications (optional)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Discord Notifications (optional)
DISCORD_WEBHOOK_URL=your-discord-webhook-url

# Monitoring Settings
CHECK_INTERVAL_MINUTES=5
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_PERIOD_SECONDS=60

# Logging
LOG_LEVEL=INFO
```

### User Preferences (config/config.yaml)

Customize your booking preferences:

```yaml
preferences:
  # Preferred locations
  locations:
    - "Berlin Mitte"
    - "Berlin Kreuzberg"
  
  # Preferred activities
  activities:
    - "Yoga"
    - "Pilates"
    - "CrossFit"
  
  # Preferred days of week (0=Monday, 6=Sunday)
  days_of_week:
    - 1  # Tuesday
    - 3  # Thursday
    - 5  # Saturday
  
  # Preferred time slots (HH:MM format)
  time_slots:
    start: "18:00"
    end: "21:00"
  
  # Auto-booking settings
  auto_book: true
  max_bookings_per_week: 3

monitoring:
  check_interval: 5  # minutes
  days_ahead: 7
  max_retries: 3
  retry_delay: 5

notifications:
  email:
    enabled: true
  telegram:
    enabled: true
  discord:
    enabled: false
```

## Usage

### Running Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Run the bot
python -m src.usp_booking_bot.main
```

### Running with Docker

```bash
# Start the bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

## Notification Setup

### Email

1. Use an app-specific password for Gmail (not your regular password)
2. Enable 2-factor authentication on your Google account
3. Generate an app password: https://myaccount.google.com/apppasswords
4. Set `SMTP_PASSWORD` to the generated app password

### Telegram

1. Create a bot with [@BotFather](https://t.me/botfather)
2. Copy the bot token to `TELEGRAM_BOT_TOKEN`
3. Start a chat with your bot
4. Get your chat ID by sending a message and visiting: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
5. Copy the chat ID to `TELEGRAM_CHAT_ID`

### Discord

1. Go to your Discord server settings
2. Navigate to Integrations → Webhooks
3. Create a new webhook
4. Copy the webhook URL to `DISCORD_WEBHOOK_URL`

## Development

### Code Style

This project follows PEP8 guidelines and uses:
- `black` for code formatting
- `flake8` for linting
- `mypy` for type checking

### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests with coverage
pytest --cov=src/usp_booking_bot tests/

# Type checking
mypy src/

# Linting
flake8 src/

# Format code
black src/
```

### Adding New Features

1. Create a new branch: `git checkout -b feature/your-feature`
2. Make your changes with type hints
3. Add tests for new functionality
4. Ensure code passes linting and type checking
5. Submit a pull request

## Logging

Logs are written to both console and file (`logs/booking_bot.log`). The logging format is JSON for easy parsing and analysis.

Log levels:
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for potentially problematic situations
- `ERROR`: Error messages for failures

## Rate Limiting

The bot implements rate limiting to respect USC API limits:
- Default: 10 requests per 60 seconds
- Configurable via `config.yaml`
- Uses `aiolimiter` for async rate limiting

## Security Notes

- Never commit `.env` file to version control
- Use environment variables for all credentials
- Rotate API tokens and passwords regularly
- Use app-specific passwords for email services
- Review notification permissions before enabling

## Troubleshooting

### Authentication Fails
- Verify credentials in `.env` file
- Check if USC changed their API endpoints
- Ensure your account is active

### No Classes Found
- Verify preferences in `config.yaml` match available classes
- Check if locations and activities are spelled correctly
- Adjust time slots and days of week

### Notifications Not Working
- Verify credentials for each notification provider
- Check notification provider settings in `config.yaml`
- Review logs for error messages

### Docker Issues
- Ensure Docker is running
- Check container logs: `docker-compose logs`
- Verify volume mounts in `docker-compose.yml`

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Follow PEP8 style guidelines
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Disclaimer

This bot is for educational purposes. Always ensure your usage complies with Urban Sports Club's terms of service. The authors are not responsible for any account suspension or other consequences resulting from the use of this bot.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.
