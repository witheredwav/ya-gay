# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini .

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Expose port (if needed for webhook, but we're using polling)
# EXPOSE 8000

# Run the bot
CMD ["python", "-m", "src.bot.main"]