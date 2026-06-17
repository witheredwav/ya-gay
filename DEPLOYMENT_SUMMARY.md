# Deployment Summary for Recording Studio Bot

## To Get the Bot Running

### If using Docker Compose (Recommended for Local Development)
1. Prepare environment:
   ```bash
   cp .env.example .env
   # Edit .env with your BOT_TOKEN and ADMIN_IDS
   # Note: DATABASE_URL in .env is ignored when using Docker Compose (it is overridden to point to the db service)
   ```
2. **Critical first step**: Remove any old database volume to avoid migration conflicts:
   ```bash
   docker-compose down -v
   # If problem persists, try:
   docker-compose down --volumes --remove-orphans
   docker volume ls -qf dangling=true | xargs -r docker volume rm
   ```
3. Start the services:
   ```bash
   docker-compose up --build
   ```

### If using Railway
1. Push your code to GitHub
2. In Railway dashboard:
   - Create new project → Connect GitHub repository
   - Add PostgreSQL plugin
   - Set environment variables:
     - `BOT_TOKEN`: Your bot token
     - `DATABASE_URL`: Use the connection string from the PostgreSQL plugin
     - `ADMIN_IDS`: Optional, comma-separated Telegram IDs for admins
3. Deploy
4. **If you see migration errors**: Reset/delete your PostgreSQL plugin and re-add it, then redeploy

### If running locally without Docker
1. Prepare environment:
   ```bash
   cp .env.example .env
   # Edit .env with your BOT_TOKEN, DATABASE_URL, and ADMIN_IDS
   ```
2. Install dependencies: `pip install -r requirements.txt`
3. **Critical first step**: Drop and recreate your database to avoid migration conflicts
4. Apply migrations: `alembic upgrade head`
5. Run the bot: `python -m src.bot.main`

## Troubleshooting Common Errors

### "Multiple head revisions are present for given argument 'head'"
**Cause**: Your database has an old migration stamp from a previous run with a different migration history.
**Solution**: Start with a fresh database (see critical first steps above).

### "column users.last_name does not exist"
**Cause**: Your database schema is out of date (missing columns from the latest migration).
**Solution**: Start with a fresh database (see critical first steps above).

### "TelegramConflictError: Conflict: terminated by other getUpdates request"
**Cause**: Another instance of your bot is still running.
**Solution**: Stop all other bot instances (check Task Manager for Python/phone.exe processes) or wait a minute for the previous instance to terminate.

## Verification of Success
After successful startup, you should see logs ending with:
```
INFO  [aiogram.dispatcher] - Start polling
INFO  [aiogram.dispatcher] - Run polling for bot @YourBotName id=123456789 - 'YourBotName'
```
The bot will then respond to the `/start` command in Telegram.

## Notes
- The `docker-compose down -v` command is **only needed for the first run** or when you encounter migration conflicts
- After successful initial deployment, subsequent `docker-compose up` will preserve your data
- All bot features (booking, bonuses, referrals, schedules, etc.) are implemented with placeholder logic ready for your customization
- The Dockerfile has been updated to migrate to a specific revision (0001_initial) to avoid the "Multiple head revisions" error
- When using Docker Compose, the DATABASE_URL for the bot service is overridden to point to the db service (postgresql+asyncpg://user:password@db:5432/recording_studio), so the user only needs to set BOT_TOKEN and ADMIN_IDS in the .env file