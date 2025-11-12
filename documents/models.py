from django.db import models
from django.utils import timezone


class DocumentType(models.TextChoices):
    LAND_TITLE = 'land_title','Land Title'
    TAX_DECLARATION = 'tax_declaration','Tax Declaration'


class CaseStatus(models.TextChoices):
    PENDING = 'pending','Pending Assignment'
    UNDER_REVIEW = 'under_review','Under Review'
    APPROVED = 'approved','Approved'
    RELEASED = 'released','Released'
    RETURNED = 'returned','Returned for Correction'
    WITHDRAWN = 'withdrawn','Withdrawn'


class Case(models.Model):
    case_id = models.CharField(max_length=64, unique=True)
    submitted_by_lgu = models.CharField(max_length=128)
    client_name = models.CharField(max_length=256)
    client_contact = models.CharField(max_length=128, blank=True, null=True)
    document_type = models.CharField(max_length=64, choices=DocumentType.choices)
    checklist = models.JSONField(default=dict)
    status = models.CharField(max_length=32, choices=CaseStatus.choices, default=CaseStatus.PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)


def __str__(self):
    return self.case_id