#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Force our settings module even if the environment already defines DJANGO_SETTINGS_MODULE.
    # This avoids surprising runtime mismatches (e.g., missing MessageMiddleware) when running locally.
    os.environ['DJANGO_SETTINGS_MODULE'] = 'legaltrack.settings'
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
