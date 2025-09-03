# Use a full-featured base image that has better compatibility
FROM python:3.11

# Install all necessary system dependencies for Playwright/Chromium
# This is a more robust list than using playwright install-deps
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the Playwright browser itself
RUN playwright install chromium

# Copy the rest of the application code
COPY . .

# Expose the port Cloud Run will listen on
EXPOSE 8080

# Use Gunicorn to start the application. This is the production-ready way.
# -w 1: Use a single worker. This is CRITICAL because we have one global browser instance.
# -b 0.0.0.0:$PORT: Bind to the port provided by Cloud Run.
# --timeout 120: Give workers 2 minutes to handle a request.
# main:app: The 'app' object in the 'main.py' file.
CMD ["gunicorn", "--workers", "1", "--threads", "8", "--timeout", "120", "-b", "0.0.0.0:8080", "main:app"]
