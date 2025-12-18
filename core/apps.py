# pyright: reportIncompatibleVariableOverride=false, reportUnusedImport=false

from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field: str = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        import core.signals  # noqa: F401
