"""
WSGI config for legaltrack project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application


def _load_env_file(path: str) -> None:
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
	base_dir = os.path.dirname(os.path.dirname(__file__))
	env_path = os.path.join(base_dir, ".env")
	try:
		from dotenv import load_dotenv  # type: ignore
	except Exception:
		_load_env_file(env_path)
		return
	load_dotenv(dotenv_path=env_path, override=False)


_load_dotenv_if_present()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "legaltrack.settings")
os.environ["DJANGO_SETTINGS_MODULE"] = "legaltrack.settings"

application = get_wsgi_application()

app = application
