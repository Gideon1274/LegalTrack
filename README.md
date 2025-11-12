# LegalTrack - Django Scaffold

This scaffold provides a minimal but opinionated starting point for the LegalTrack application described in the specification.

## Quickstart (development)

1. Create virtualenv and install requirements:

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

2. Run migrations and create superuser:

python manage.py migrate
python manage.py createsuperuser

3. Start development server:

python manage.py runserver

## Notes

- This scaffold uses SQLite for convenience. Switch to PostgreSQL in production.
- Add environment variable based configuration for SECRET_KEY and DEBUG.
- Implement RBAC enforcement and more granular permissions in views and serializers.
- Add email/SMS gateways and rate-limiting for the public endpoint as required.

# .env.example

DJANGO_SECRET_KEY=replace-me
DJANGO_DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3

# Dockerfile (basic)

FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD ["gunicorn","legaltrack.wsgi:application","--bind","0.0.0.0:8000"]
