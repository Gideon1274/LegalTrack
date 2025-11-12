from django.db import models
from django.contrib.auth.models import AbstractUser


class Role(models.TextChoices):
    SUPERADMIN = 'superadmin', 'Super Admin'
    LGU_ADMIN = 'lgu_admin', 'LGU Admin'
    RECEIVING = 'receiving', 'Receiving Staff'
    EXAMINER = 'examiner', 'Examiner'
    APPROVER = 'approver', 'Approver'


class User(AbstractUser):
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.LGU_ADMIN)
    lgu = models.CharField(max_length=128, blank=True, null=True)
    pass