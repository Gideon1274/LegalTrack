from django.db import models
from documents.models import Case
from django.utils import timezone


class CaseTransition(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='transitions')
    old_status = models.CharField(max_length=64)
    new_status = models.CharField(max_length=64)
    changed_by = models.CharField(max_length=128)
    notes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)


class Meta:
    ordering = ['-timestamp']