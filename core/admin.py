from typing import ClassVar

from django.contrib import admin
from .models import AuditLog, Case, CaseDocument, CustomUser
from django import forms

class CustomUserCreationForm(forms.ModelForm):
    account_type = forms.ChoiceField(
        choices=[("capitol", "Capitol Admin"), ("lgu", "LGU Admin")],
        initial="capitol",
        widget=forms.Select(),
    )
    capitol_role = forms.ChoiceField(
        required=False,
        choices=[
            ("capitol_receiving", "Capitol Receiving Staff"),
            ("capitol_examiner", "Capitol Examiner"),
            ("capitol_approver", "Capitol Approver"),
            ("capitol_numberer", "Capitol Numberer"),
            ("capitol_releaser", "Capitol Releaser"),
        ],
        widget=forms.Select(),
    )
    lgu_municipality = forms.ChoiceField(
        required=False,
        choices=CustomUser.LGU_MUNICIPALITY_CHOICES,
        widget=forms.Select(),
    )

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name")

    def clean(self):
        cleaned = super().clean() or {}
        account_type = cleaned.get("account_type")
        if account_type == "capitol":
            if not cleaned.get("capitol_role"):
                raise forms.ValidationError("Please select a Capitol position.")
        elif account_type == "lgu":
            if not cleaned.get("lgu_municipality"):
                raise forms.ValidationError("Please select an LGU municipality.")
        else:
            raise forms.ValidationError("Invalid account type.")
        return cleaned

    def save(self, commit=True, created_by=None):
        user = super().save(commit=False)

        account_type = (self.cleaned_data.get("account_type") or "").strip()
        if account_type == "capitol":
            user.role = str(self.cleaned_data.get("capitol_role") or "")
            user.lgu_municipality = ""
        else:
            user.role = "lgu_admin"
            user.lgu_municipality = str(self.cleaned_data.get("lgu_municipality") or "")

        full_name = f"{(user.first_name or '').strip()} {(user.last_name or '').strip()}".strip()
        if full_name:
            user.full_name = full_name

        if commit:
            user.save(created_by=created_by)
        return user


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "full_name", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active")
    search_fields = ("email", "full_name", "username")
    readonly_fields = ("username", "date_joined", "last_login")
    add_form = CustomUserCreationForm
    add_fieldsets = (
        (None, {
            "fields": ("email", "first_name", "last_name", "account_type", "capitol_role", "lgu_municipality"),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Only on create
            obj.save(created_by=request.user)  # Pass created_by
        else:
            obj.save()
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "target_object", "created_at")
    list_filter = ("action", "created_at", "actor")
    search_fields = ("actor__email", "target_object", "details")
    readonly_fields = ("created_at", "updated_at", "actor", "action", "target_object", "details", "ip_address", "user_agent")

    def has_add_permission(self, request):
        return False  # Prevent manual creation

    def has_change_permission(self, request, obj=None):
        return False  # Prevent editing

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent deletion


class CaseDocumentInline(admin.TabularInline):
    model = CaseDocument
    extra = 0
    fields = ("doc_type", "file", "uploaded_by", "uploaded_at")
    readonly_fields = ("uploaded_by", "uploaded_at")

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("tracking_id", "client_name", "status", "submitted_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("tracking_id", "client_name", "submitted_by__email")
    inlines: ClassVar[list] = [CaseDocumentInline]
    readonly_fields = (
        "tracking_id",
        "created_at",
        "updated_at",
        "received_at",
        "received_by",
        "returned_at",
        "returned_by",
        "assigned_to",
        "assigned_at",
    )

