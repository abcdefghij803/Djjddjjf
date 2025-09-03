# ---------- Base: slim, faster builds ----------
FROM python:3.11-slim AS base

# Avoid Python buffering & create a non-root user
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOME=/app

WORKDIR $APP_HOME

# System deps (certs, tzdata optional), then clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates tzdata tini \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt ./

RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app source
COPY . .

# Use an unprivileged user
RUN useradd -m appuser && chown -R appuser:appuser $APP_HOME
USER appuser

# (Optional) Set timezone – change if needed
ENV TZ=Asia/Kolkata

# No ports to expose (Telethon client), Northflank will run as a worker
# HEALTHCHECK is optional for workers; you can omit it if you prefer
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD python -c "import sys; sys.exit(0)"

# Start with Tini as init for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Run the bot
CMD ["python", "bot.py"]
