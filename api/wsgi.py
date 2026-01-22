import os

# Ensure Django settings are discoverable in the serverless environment.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "legaltrack.settings")

# Vercel's Python runtime looks for a module-level WSGI callable named `app`.
from legaltrack.wsgi import application as app  # noqa: E402


def _maybe_auto_migrate_sqlite() -> None:
	# If DATABASE_URL wasn't configured on Vercel, settings.py falls back to a
	# temporary SQLite DB. Run migrations once per cold start so the app can
	# actually serve pages instead of crashing on missing tables.
	try:
		if not (os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV")):
			return

		# Only run in explicit demo-mode fallback.
		if str(os.environ.get("LEGALTRACK_ENABLE_VERCEL_SQLITE_FALLBACK", "")).strip().lower() not in {"1", "true", "yes", "on"}:
			return

		# Allow opting out for advanced setups.
		if str(os.environ.get("LEGALTRACK_AUTO_MIGRATE", "true")).strip().lower() in {"0", "false", "no", "off"}:
			return

		from django.conf import settings

		default_db = getattr(settings, "DATABASES", {}).get("default", {})
		if (default_db.get("ENGINE") or "") != "django.db.backends.sqlite3":
			return

		from django.core.management import call_command

		call_command("migrate", interactive=False, verbosity=0)
	except Exception:
		# Never break the app import path if migrations fail.
		return


_maybe_auto_migrate_sqlite()
