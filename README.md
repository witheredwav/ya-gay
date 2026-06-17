# Telegram Bot for Recording Studio

A Telegram bot for managing bookings in a recording studio, built with aiogram 3.x, SQLAlchemy, and PostgreSQL.

## Features

- Client booking flow with inline keyboards
- Engineer and admin roles
- Bonus and referral system
- Schedule management
- Automatic notifications
- Dockerized for easy deployment

## Technology Stack

- Python 3.12
- aiogram 3.x
- PostgreSQL
- SQLAlchemy 2.0
- Alembic for migrations
- Docker
- Railway for deployment

## Setup

### Local Development

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in the required values:
   - `BOT_TOKEN`: Your Telegram bot token
   - `DATABASE_URL`: PostgreSQL connection string (e.g., `postgresql+asyncpg://user:password@localhost/db_name`)
   - `ADMIN_IDS`: Comma-separated list of Telegram IDs for admins (optional)
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Apply database migrations:
   ```bash
   alembic upgrade head
   ```
5. Run the bot:
   ```bash
   python -m src.bot.main
   ```

### Using Docker Compose

1. Copy `.env.example` to `.env` and fill in the values
2. Start the services:
   ```bash
   docker-compose up --build
   ```

### Deployment to Railway

1. Push the repository to GitHub
2. In Railway, create a new project and connect your GitHub repository
3. Railway will automatically detect the Dockerfile and build the image
4. Set the environment variables in the Railway dashboard:
   - `BOT_TOKEN`
   - `DATABASE_URL` (you can add a PostgreSQL plugin)
   - `ADMIN_IDS`
5. Deploy!

## Project Structure

```
src/
├── bot/
│   ├── main.py          # Entry point
│   ├── config.py        # Configuration loading
│   ├── database.py      # Database setup
│   ├── handlers/        # Message and callback handlers
│   │   ├── client.py    # Client-facing handlers
│   │   ├── engineer.py  # Engineer-facing handlers
│   │   └── admin.py     # Admin-facing handlers
│   ├── keyboards/       # Keyboard builders
│   │   ├── common.py    # Common keyboards (confirm, back, main menus)
│   │   ├── client.py    # Client-specific keyboards
│   │   ├── engineer.py  # Engineer-specific keyboards
│   │   └── admin.py     # Admin-specific keyboards
│   ├── middlewares/     # Custom middlewares
│   │   └── role_middleware.py  # Role-based middleware
│   └── states.py        # FSM states
├── models/              # SQLAlchemy models
│   ├── user.py
│   ├── booking.py
│   ├── bonus.py
│   ├── referral.py
│   ├── schedule.py
│   └── day_off.py
└── migrations/          # Alembic migration scripts
    ├── env.py
    └── versions/
        └── 2026_06_18_000000_initial_migration.py
```

## Database Models

- **User**: Represents a user (client, engineer, or admin)
- **Booking**: Represents a booking session
- **BonusTransaction**: Tracks bonus earnings and spending
- **Referral**: Tracks referral relationships
- **Schedule**: Defines weekly working hours for engineers
- **DayOff**: Marks specific days as unavailable for engineers

## How It Works

### Client Flow

1. Client starts the bot and sees the main menu
2. To book a session:
   - Select month → date → engineer → time → duration
   - Enter name and phone number (with confirmation)
   - For bookings ≤ 2 hours: request goes to engineer for instant confirmation
   - For bookings ≥ 3 hours: request requires manual confirmation from engineer or admin
3. Client can view their recordings, bonuses, and referral link

### Engineer Flow

1. Engineer sees new requests in the "Новые заявки" menu
2. Can confirm or reject requests (with reason for rejection)
3. Can manage their schedule and days off
4. Can view their upcoming sessions

### Admin Flow

1. Admin has full access to:
   - View and manage clients, engineers, and other admins
   - View all bookings and bonus transactions
   - Manage the bonus and referral systems
   - View statistics and generate reports
   - Adjust settings

## License

MIT