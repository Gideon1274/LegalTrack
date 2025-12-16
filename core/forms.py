# core/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
from .models import Case, CaseDocument
from .models import CustomUser
import json

class CaseSubmissionForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ['client_name', 'client_contact', 'checklist']
        widgets = {
            'checklist': forms.Textarea(attrs={'rows': 6, 'placeholder': (
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
        # data = self.cleaned_data['checklist']
        # try:
        #     parsed = json.loads(data)
        #     if not isinstance(parsed, list):
        #         raise forms.ValidationError("Checklist must be a JSON list.")
        #     for item in parsed:
        #         if not isinstance(item, dict) or 'doc_type' not in item:
        #             raise forms.ValidationError("Each item must have 'doc_type'.")
        #     return parsed
        # except json.JSONDecodeError:
        #     raise forms.ValidationError("Invalid JSON in checklist.")

        data = self.cleaned_data.get('checklist')

        if not data:
            return []

        # data is ALREADY a list/dict from JSONField
        if not isinstance(data, list):
            raise forms.ValidationError("Checklist must be a list of documents.")

        for item in data:
            if not isinstance(item, dict):
                raise forms.ValidationError("Each item must be a document object.")
            if not all(k in item for k in ['doc_type', 'required']):
                raise forms.ValidationError("Each document must have 'doc_type' and 'required'.")
            if not isinstance(item['required'], bool):
                raise forms.ValidationError("'required' must be true or false.")

        return data


class CaseDetailsForm(forms.ModelForm):
    endorsement_letter = forms.FileField(required=False)

    class Meta:
        model = Case
        fields = ['client_name', 'client_contact']
        widgets = {
            'client_name': forms.TextInput(attrs={'placeholder': 'Full name'}),
            'client_contact': forms.TextInput(attrs={'placeholder': 'Phone number or email'}),
        }


class ChecklistItemForm(forms.Form):
    doc_type = forms.CharField(max_length=120, required=False)
    required = forms.BooleanField(required=False)
    file = forms.FileField(required=False)
    delete = forms.BooleanField(required=False)

    def clean(self):
        cleaned = super().clean()
        doc_type = (cleaned.get('doc_type') or '').strip()
        if cleaned.get('delete'):
            return cleaned
        if not doc_type and (cleaned.get('required') or cleaned.get('file')):
            raise forms.ValidationError('Document type is required for this row.')
        cleaned['doc_type'] = doc_type
        return cleaned


def build_checklist_formset(*, initial=None, extra: int = 5):
    FormSet = forms.formset_factory(ChecklistItemForm, extra=extra)
    return FormSet(initial=initial or [])


class StaffAccountCreateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'role', 'designation', 'position']

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise ValidationError('Email is required.')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('This email is already in use.')
        return email


class StaffSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search users by name or ID'}),
    )
    role = forms.ChoiceField(
        required=False,
        choices=[('', 'All Roles')] + CustomUser.ROLE_CHOICES,
        widget=forms.Select(),
    )


class AccountActivationForm(forms.Form):
    temp_password = forms.CharField(
        label='Temporary Password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
    )

    def __init__(self, user: CustomUser, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_temp_password(self):
        temp_password = self.cleaned_data.get('temp_password') or ''
        if self.user.account_status != 'pending':
            raise ValidationError('This account is not pending activation.')
        if self.user.temp_password_created_at:
            if timezone.now() - self.user.temp_password_created_at > timedelta(days=7):
                raise ValidationError('Temporary password expired. Contact the Super Admin for a resend.')
        if not self.user.check_password(temp_password):
            raise ValidationError('Temporary password is incorrect.')
        return temp_password

    def clean(self):
        cleaned = super().clean()
        pw1 = cleaned.get('new_password1')
        pw2 = cleaned.get('new_password2')
        if pw1 and pw2 and pw1 != pw2:
            raise ValidationError('New passwords do not match.')
        if pw1:
            validate_password(pw1, self.user)
        return cleaned

    def save(self):
        pw1 = self.cleaned_data['new_password1']
        self.user.set_password(pw1)
        self.user.account_status = 'active'
        self.user.must_change_password = False
        self.user.activated_at = timezone.now()
        self.user.save(update_fields=['password', 'account_status', 'must_change_password', 'activated_at', 'is_active'])
        return self.user


class StaffAccountUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['full_name', 'designation', 'position']

    def clean_full_name(self):
        name = (self.cleaned_data.get('full_name') or '').strip()
        return name