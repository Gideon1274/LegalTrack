from __future__ import annotations

# pyright: reportAttributeAccessIssue=false, reportOperatorIssue=false

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
from typing import ClassVar
from .models import Case
from .models import CustomUser

class CaseSubmissionForm(forms.ModelForm):
    class Meta:
        model = Case
        fields: ClassVar[list[str]] = ["client_name", "client_contact", "checklist"]
        widgets: ClassVar[dict] = {
            "checklist": forms.Textarea(attrs={"rows": 6, "placeholder": (
                'Enter JSON list, e.g.\n'
                '[\n'
                '  {"doc_type": "Land Title", "required": true},\n'
                '  {"doc_type": "Tax Declaration", "required": true}\n'
                ']'
            )}),
        }
    client_name = forms.CharField(max_length=100)
    client_contact = forms.CharField(max_length=15)
    checklist = forms.JSONField()

    def clean_checklist(self):
        cleaned = self.cleaned_data or {}
        data = cleaned.get("checklist")

        if not data:
            return []

        # data is ALREADY a list/dict from JSONField
        if not isinstance(data, list):
            raise forms.ValidationError("Checklist must be a list of documents.")

        for item in data:
            if not isinstance(item, dict):
                raise forms.ValidationError("Each item must be a document object.")
            if not all(k in item for k in ["doc_type", "required"]):
                raise forms.ValidationError("Each document must have 'doc_type' and 'required'.")
            if not isinstance(item["required"], bool):
                raise forms.ValidationError("'required' must be true or false.")

        return data


class CaseDetailsForm(forms.ModelForm):
    endorsement_letter = forms.FileField(required=False)

    class Meta:
        model = Case
        fields: ClassVar[list[str]] = ["client_name", "client_contact"]
        widgets: ClassVar[dict] = {
            "client_name": forms.TextInput(attrs={"placeholder": "Full name"}),
            "client_contact": forms.TextInput(attrs={"placeholder": "Phone number or email"}),
        }


class ChecklistItemForm(forms.Form):
    doc_type = forms.CharField(max_length=120, required=False)
    required = forms.BooleanField(required=False)
    file = forms.FileField(required=False)
    delete = forms.BooleanField(required=False)

    def clean(self):
        cleaned = super().clean() or {}
        doc_type = (cleaned.get("doc_type") or "").strip()
        if cleaned.get("delete"):
            return cleaned
        if not doc_type and (cleaned.get("required") or cleaned.get("file")):
            raise forms.ValidationError("Document type is required for this row.")
        cleaned["doc_type"] = doc_type
        return cleaned


class CaseRemarkForm(forms.Form):
    text = forms.CharField(
        label="Remark / Comment",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Add an internal note..."}),
    )

    def clean_text(self):
        cleaned = self.cleaned_data or {}
        text = (cleaned.get("text") or "").strip()
        if not text:
            raise ValidationError("Remark cannot be empty.")
        return text


def build_checklist_formset(*, initial=None, extra: int = 5):
    FormSet = forms.formset_factory(ChecklistItemForm, extra=extra)
    return FormSet(initial=initial or [])


class StaffAccountCreateForm(forms.ModelForm):
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
        fields: ClassVar[list[str]] = ["email", "first_name", "last_name"]

    def clean_email(self):
        cleaned = self.cleaned_data or {}
        email = (cleaned.get("email") or "").strip().lower()
        if not email:
            raise ValidationError("Email is required.")
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("This email is already in use.")
        return email

    def clean(self):
        cleaned = super().clean() or {}
        account_type = cleaned.get("account_type")
        capitol_role = cleaned.get("capitol_role")
        lgu_municipality = cleaned.get("lgu_municipality")

        if account_type == "capitol":
            if not capitol_role:
                raise ValidationError("Please select a Capitol position.")
        elif account_type == "lgu":
            if not lgu_municipality:
                raise ValidationError("Please select an LGU municipality.")
        else:
            raise ValidationError("Invalid account type.")

        return cleaned

    def save(self, commit=True):
        user: CustomUser = super().save(commit=False)
        cleaned = self.cleaned_data or {}

        account_type = cleaned.get("account_type")
        if account_type == "capitol":
            user.role = str(cleaned.get("capitol_role") or "")
            user.lgu_municipality = ""
        else:
            user.role = "lgu_admin"
            user.lgu_municipality = str(cleaned.get("lgu_municipality") or "")

        # Keep legacy full_name populated for existing templates.
        first_name = (cleaned.get("first_name") or "").strip()
        last_name = (cleaned.get("last_name") or "").strip()
        full_name = f"{first_name} {last_name}".strip()
        if full_name:
            user.full_name = full_name

        if commit:
            user.save()
        return user


class StaffSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Search users by name or ID"}),
    )
    role = forms.ChoiceField(
        required=False,
        choices=[("", "All Roles"), *CustomUser.ROLE_CHOICES],
        widget=forms.Select(),
    )


class AccountActivationForm(forms.Form):
    temp_password = forms.CharField(
        label="Temporary Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
    )

    def __init__(self, user: CustomUser, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_temp_password(self):
        cleaned = self.cleaned_data or {}
        temp_password = cleaned.get("temp_password") or ""
        if self.user.account_status != "pending":
            raise ValidationError("This account is not pending activation.")
        if self.user.temp_password_created_at:
            if timezone.now() - self.user.temp_password_created_at > timedelta(days=7):
                raise ValidationError("Temporary password expired. Contact the Super Admin for a resend.")
        if not self.user.check_password(temp_password):
            raise ValidationError("Temporary password is incorrect.")
        return temp_password

    def clean(self):
        cleaned = super().clean() or {}
        pw1 = cleaned.get("new_password1")
        pw2 = cleaned.get("new_password2")
        if pw1 and pw2 and pw1 != pw2:
            raise ValidationError("New passwords do not match.")
        if pw1:
            validate_password(pw1, self.user)
        return cleaned

    def save(self):
        cleaned = self.cleaned_data or {}
        pw1 = cleaned.get("new_password1")
        if not pw1:
            raise ValidationError("New password is required.")
        self.user.set_password(pw1)
        self.user.account_status = "active"
        self.user.must_change_password = False
        self.user.activated_at = timezone.now()
        self.user.save(update_fields=["password", "account_status", "must_change_password", "activated_at", "is_active"])
        return self.user


class StaffAccountUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields: ClassVar[list[str]] = ["full_name", "designation", "position"]

    def clean_full_name(self):
        cleaned = self.cleaned_data or {}
        return (cleaned.get("full_name") or "").strip()


class PublicCaseSearchForm(forms.Form):
    q = forms.CharField(
        label="Tracking Number",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "e.g., CEB251200001"}),
    )

    def clean_q(self):
        cleaned = self.cleaned_data or {}
        q = (cleaned.get("q") or "").strip().upper()
        if not q:
            raise ValidationError("Tracking number is required.")
        return q


class SupportFeedbackForm(forms.Form):
    name = forms.CharField(required=False, max_length=120)
    email = forms.EmailField(required=False)
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "Describe your concern..."}),
    )

    def clean_message(self):
        cleaned = self.cleaned_data or {}
        msg = (cleaned.get("message") or "").strip()
        if not msg:
            raise ValidationError("Message is required.")
        return msg


class ReportFilterForm(forms.Form):
    REPORT_CHOICES: ClassVar[list[tuple[str, str]]] = [
        ("status_breakdown", "Status Breakdown"),
        ("monthly_accomplishment", "Monthly Accomplishment"),
        ("processing_times", "Processing Times"),
    ]

    report_type = forms.ChoiceField(choices=REPORT_CHOICES, required=True)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All Statuses"), *Case.STATUS_CHOICES],
    )
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ("-created_at", "Newest"),
            ("created_at", "Oldest"),
            ("-updated_at", "Recently Updated"),
        ],
    )

    def clean(self):
        cleaned = super().clean() or {}
        d1 = cleaned.get("date_from")
        d2 = cleaned.get("date_to")
        if d1 and d2 and d1 > d2:
            raise ValidationError("Date From must be on or before Date To.")
        return cleaned
