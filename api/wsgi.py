import os

# Ensure Django settings are discoverable in the serverless environment.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "legaltrack.settings")

# Vercel's Python runtime looks for a module-level WSGI callable named `app`.
from legaltrack.wsgi import application as app  # noqa: E402
