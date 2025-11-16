# core/forms.py
from django import forms
from .models import Case
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