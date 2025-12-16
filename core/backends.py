from __future__ import annotations

from django.contrib.auth.backends import ModelBackend


class AdminEmailAliasBackend(ModelBackend):
    """Allow only one email to authenticate via the username field.

    Requirement: typing `admin@gmail.com` in the Staff ID field should log in as the
    user with that email. All other users must log in with Staff ID.
    """

    ADMIN_EMAIL = "admin@gmail.com"

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or username.strip().lower() != self.ADMIN_EMAIL:
            return None

        from django.contrib.auth import get_user_model

        UserModel = get_user_model()
        user = UserModel._default_manager.filter(email__iexact=self.ADMIN_EMAIL).first()
        if not user:
            return None

        if password and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
