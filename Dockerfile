# Use a lightweight Python image
FROM python:3.11-slim-bookworm

# Install LibreOffice and system dependencies for PDF conversion and images
RUN apt-get update && apt-get install -y \
    libreoffice-writer \
    libreoffice-java-common \
    libmagic1 \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

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
# Migrations are run at runtime to ensure DB is ready
CMD python manage.py migrate --noinput && \
    gunicorn legaltrack.wsgi:application --bind 0.0.0.0:$PORT --timeout 120
