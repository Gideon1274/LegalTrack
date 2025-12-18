#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def _load_env_file(path: str) -> None:
    """Minimal .env loader (fallback when python-dotenv isn't installed)."""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if not key:
                    continue
                if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                    value = value[1:-1]
                os.environ.setdefault(key, value)
    except FileNotFoundError:
        return


def _load_dotenv_if_present() -> None:
    """Load variables from .env for local/dev convenience.

    This is optional: in production, environment variables should be provided
    by the host. If python-dotenv isn't installed, this is a no-op.
    """
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        _load_env_file(env_path)
        return
    # Do not override variables already set in the environment.
    load_dotenv(dotenv_path=env_path, override=False)


def main():
    """Run administrative tasks."""
    _load_dotenv_if_present()
    # Force our settings module even if the environment already defines DJANGO_SETTINGS_MODULE.
    # This avoids surprising runtime mismatches (e.g., missing MessageMiddleware) when running locally.
    os.environ["DJANGO_SETTINGS_MODULE"] = "legaltrack.settings"
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
