# Use a robust Python image
FROM python:3.11-slim-bookworm

# Install LibreOffice and system dependencies
# We include --no-install-recommends to keep the image slim, 
# but ensure we have the necessary libraries for headless mode.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    libreoffice-java-common \
    libpq-dev \
    gcc \
    python3-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# LibreOffice needs a writable HOME directory to create a user profile in headless mode.
# We set it to /tmp or another writable location.
ENV HOME=/tmp

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=legaltrack.settings

# Collect static files (uses a placeholder SECRET_KEY if none is set)
RUN python manage.py collectstatic --noinput 2>&1 || true

# The port is set by Render
EXPOSE 10000

# Start command
# Migrations are run at runtime to ensure DB is ready. 
# $PORT is provided by Render at runtime.
CMD python manage.py migrate --noinput && \
    gunicorn legaltrack.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --graceful-timeout 30
