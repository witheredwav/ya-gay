# Final Instructions for Deploying the Recording Studio Bot

## Summary of Fixes
All import errors, syntax errors, and migration issues have been fixed. The bot should now start successfully if the database is fresh.

## Key Changes Made
1. Fixed all Python import and syntax errors in the codebase
2. Corrected migration files and environment configuration
3. Updated Docker and Docker-Compose to handle database health checks and run migrations on startup
4. Added troubleshooting steps for common issues

## How to Deploy

### Option 1: Local Development with Docker Compose (Recommended)
1. Copy `.env.example` to `.env` and fill in your values:
   ```env
   BOT_TOKEN=your_actual_bot_token_here
   DATABASE_URL=postgresql+asyncpg://user:password@localhost/recording_studio
   ADMIN_IDS=123456789,987654321  # Optional
   ```
2. Run:
   ```bash
   docker-compose up --build
   ```
   **If you see "Multiple head revisions" or "column users.last_name does not exist" error:**
   ```bash
   docker-compose down -v   # Removes database volume and starts fresh
   docker-compose up --build
   ```

### Option 2: Railway Deployment
1. Push your repository to GitHub
2. In Railway:
   - Create new project → Connect GitHub repository
   - Railway auto-detects Dockerfile and builds image
   - Set environment variables in Railway dashboard:
     - `BOT_TOKEN` (your bot token)
     - `DATABASE_URL` (add PostgreSQL plugin first, then use its connection string)
     - `ADMIN_IDS` (optional, comma-separated Telegram IDs)
3. Deploy!
   **If you see "Multiple head revisions" or "column users.last_name does not exist" error:**
   - Reset/delete your PostgreSQL plugin in Railway and re-add it to start with a clean database
   - Then redeploy

### Option 3: Local Development without Docker
1. Set up a PostgreSQL database and update `.env` with the correct `DATABASE_URL`
2. Install dependencies: `pip install -r requirements.txt`
3. Apply migrations: `alembic upgrade head`
   **If you see "Multiple head revisions" error:**
   - Drop your database and recreate it, then run `alembic upgrade head`
4. Run the bot: `python -m src.bot.main`

## Verification
After successful deployment, you should see logs indicating:
- Database connection established
- Migrations applied
- Bot started and polling for updates

The bot will then respond to the `/start` command in Telegram.

## Support
If you encounter any issues not covered here, please check:
1. That your `.env` file is correctly formatted
2. That your PostgreSQL database is accessible and running
3. That you have followed the troubleshooting steps for "Multiple head revisions" or missing columns

Happy booking! 🎙️