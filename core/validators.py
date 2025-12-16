import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class StrongPasswordComplexityValidator:
    """Enforce Module 1 password complexity:

    - minimum 12 characters (handled by MinimumLengthValidator)
    - at least one uppercase, one lowercase, one digit, and one special character
    """

    def validate(self, password, user=None):
        if not re.search(r"[A-Z]", password):
            raise ValidationError(_("Password must contain at least one uppercase letter."), code="password_no_upper")
        if not re.search(r"[a-z]", password):
            raise ValidationError(_("Password must contain at least one lowercase letter."), code="password_no_lower")
        if not re.search(r"\d", password):
            raise ValidationError(_("Password must contain at least one number."), code="password_no_number")
        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValidationError(_("Password must contain at least one special character."), code="password_no_special")

    def get_help_text(self):
        return _("Your password must include uppercase, lowercase, number, and special character.")
