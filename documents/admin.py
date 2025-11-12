from django.contrib import admin
from .models import Case


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('case_id','submitted_by_lgu','document_type','status','created_at')