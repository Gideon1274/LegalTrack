import json
from typing import Any

from django import template

from core.models import Case

register = template.Library()


def _title_key(key: str) -> str:
    return key.replace("_", " ").strip().title()


def _status_display(status: str) -> str:
    for code, label in Case.STATUS_CHOICES:
        if code == status:
            return str(label)
    return status


@register.filter(name="format_audit_details")
def format_audit_details(details: Any) -> str:
    """Render AuditLog.details in a readable way for templates."""

    if details is None or details == "":
        return "—"

    # Django JSONField should already be a dict/list, but handle string JSON too.
    if isinstance(details, str):
        s = details.strip()
        if not s:
            return "—"
        try:
            details = json.loads(s)
        except Exception:
            return details

    if isinstance(details, dict):
        parts: list[str] = []

        if "reason" in details and details.get("reason"):
            parts.append(f"Reason: {details.get('reason')}")

        if "new_status" in details and details.get("new_status"):
            parts.append(f"New status: {_status_display(str(details.get('new_status')))}")

        # Add any remaining keys (stable order)
        for k in sorted(details.keys()):
            if k in {"reason", "new_status"}:
                continue
            v = details.get(k)
            if v is None or v == "":
                continue
            parts.append(f"{_title_key(str(k))}: {v}")

        return "\n".join(parts) if parts else "—"

    if isinstance(details, list):
        try:
            return "\n".join(str(x) for x in details if x is not None and str(x).strip() != "") or "—"
        except Exception:
            return str(details)

    return str(details)
