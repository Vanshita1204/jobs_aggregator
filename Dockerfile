# ── What is a Dockerfile? ─────────────────────────────────────────────────────
# A Dockerfile is a recipe for building a Docker image.
# An image is a snapshot of a filesystem + metadata (what command to run, etc).
# A container is a running instance of that image.
# Each instruction (FROM, RUN, COPY...) creates a new layer on top of the last.
# Layers are cached: if a layer hasn't changed, Docker reuses it on rebuild.
# This is why we copy requirements.txt BEFORE copying code — pip install is slow
# and we don't want to redo it every time we change a .py file.
# ─────────────────────────────────────────────────────────────────────────────

# FROM: start from an existing base image.
# python:3.12-slim is Debian-based with Python 3.12, stripped of extras (~130MB vs ~1GB full).
FROM python:3.12-slim

# WORKDIR: sets the working directory for all subsequent instructions.
# Creates the directory if it doesn't exist.
# Like doing `mkdir -p /app && cd /app` in every following step.
WORKDIR /app

# RUN: executes a shell command inside the image during the build.
# We install system libraries that Playwright's Chromium browser needs at runtime.
# --no-install-recommends: skip optional packages (keeps the image smaller).
# The final `rm -rf /var/lib/apt/lists/*` clears apt's cache — also saves space.
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools: needed to compile C extensions (cryptography, cffi, greenlet, etc.)
    # The slim image ships without gcc/make — packages that lack pre-built wheels will fail without these.
    build-essential \
    libffi-dev \
    libssl-dev \
    # Runtime utilities
    ca-certificates \
    wget \
    # Chromium runtime dependencies
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

# COPY requirements.txt first — cache trick explained above.
# This layer only rebuilds if requirements.txt changes.
COPY requirements.txt .

# Install Python dependencies.
# --no-cache-dir: don't cache downloaded packages inside the image (saves space).
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright's Chromium browser binary.
# The `playwright` Python package is just the API wrapper.
# The actual browser binary must be downloaded separately with this command.
# `--with-deps` also installs any missing OS-level deps for Chromium.
RUN playwright install --with-deps chromium

# COPY the rest of the application code.
# This happens last so that code changes don't invalidate the pip/playwright cache layers above.
COPY . .

# Create the data directory for SQLite.
RUN mkdir -p /app/data

# CMD: the default command to run when the container starts.
# This can be overridden in docker-compose.yml (e.g. to run celery instead).
# --host 0.0.0.0 is required: inside Docker, the default 127.0.0.1 binding
# is only reachable within the container, not from the outside world.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
