from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import secrets
import string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .utils import create_activation_link
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
import json

class CustomUser(AbstractUser):
    # roles
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('lgu_admin', 'LGU Admin'),
        ('capitol_receiving', 'Capitol Receiving Staff'),
        ('capitol_examiner', 'Capitol Examiner'),
        ('capitol_approver', 'Capitol Approver'),
        ('capitol_numberer', 'Capitol Numberer'),
        ('capitol_releaser', 'Capitol Releaser'),
    ]

    email = models.EmailField(unique=True, blank=False, null=False)
    full_name = models.CharField(max_length=255, blank=True)
    # role = models.CharField(max_length=50, choices=ROLE_CHOICES, blank=False, null=False)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, null=False)
    # Use email for login instead of username
    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['username', 'full_name', 'role'] 
    REQUIRED_FIELDS = [] 

    def __str__(self):
        return f"{self.full_name} ({self.email}) - {self.get_role_display()}"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
    def generate_staff_id(self, role_prefix):
        """Generate Staff ID: 25-CEB-0001"""
        from .models import CustomUser
        prefix_map = {
            'super_admin': 'ADM',
            'lgu_admin': 'LGU',
            'capitol_receiving': 'REC',
            'capitol_examiner': 'EXM',
            'capitol_approver': 'APR',
            'capitol_numberer': 'NUM',
            'capitol_releaser': 'REL',
        }
        prefix = prefix_map.get(role_prefix, 'USR')
        last_user = CustomUser.objects.filter(
            role=role_prefix
        ).order_by('id').last()
        seq = (last_user.id + 1) if last_user else 1
        return f"25-{prefix}-{seq:04d}"

    def generate_temp_password(self):
        """Generate strong 12-char temp password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(12))

    def send_activation_email(self, temp_password):
        activation_link = create_activation_link(self)
        subject = "Activate Your LegalTrack Account"
        message = f"""
        Hello {self.full_name},

        Your account has been created.

        Staff ID: {self.username}
        Email: {self.email}
        Temporary Password: {temp_password}

        Activate your account here:
        {activation_link}

        This link expires in 24 hours.

        After activation, you will be prompted to set a new password.

        Thank you,
        Cebu Provincial Capitol
        """
        send_mail(
            subject,
            message,
            'no-reply@cebu.gov.ph',
            [self.email],
            fail_silently=False,
        )

    def save(self, *args, **kwargs):
        created_by = kwargs.pop('created_by', None)
        is_new = self.pk is None

        if is_new:
            # Generate Staff ID
            self.username = self.generate_staff_id(self.role)

            # Generate temp password
            temp_password = self.generate_temp_password()
            self.set_password(temp_password)

            # AUTO-ACTIVATE (skip email)
            self.is_active = True

        super().save(*args, **kwargs)

        if is_new:
            # Optional: Log password in console for dev
            if settings.DEBUG:
                print(f"\n=== NEW USER CREATED ===")
                print(f"Email: {self.email}")
                print(f"Staff ID: {self.username}")
                print(f"Password: {temp_password}")
                print(f"Login: http://127.0.0.1:8000/accounts/login/")
                print("========================\n")

            # Audit log
            AuditLog.objects.create(
                actor=created_by,
                action='create_user',
                target_user=self,
                target_object=f"User: {self.email}",
                details={
                    'staff_id': self.username,
                    'role': self.get_role_display(),
                    'auto_activated': True
                }
            )

# Base model for audit trails and timestamps
class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )

    class Meta:
        abstract = True

class AuditLog(TimestampedModel):
    ACTION_CHOICES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('create_user', 'Create User Account'),
        ('update_user', 'Update User Account'),
        ('deactivate_user', 'Deactivate User'),
        ('reactivate_user', 'Reactivate User'),
        ('reset_password', 'Reset Password'),
        ('case_create', 'Case Created'),
        ('case_update', 'Case Updated'),
        ('case_status_change', 'Case Status Changed'),
        ('case_receipt', 'Case Physically Received'),
        ('case_approval', 'Case Approved'),
        ('case_rejection', 'Case Rejected'),
        ('case_release', 'Case Released'),
    ]

    actor = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='target_audit_logs'
    )
    target_object = models.CharField(max_length=255, blank=True, help_text="e.g., Case ID: CEB-2025...")
    details = models.JSONField(default=dict, blank=True, help_text="Extra context in JSON")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action']),
            models.Index(fields=['created_at']),
            models.Index(fields=['actor']),
        ]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        return f"{self.get_action_display()} by {self.actor} at {self.created_at}"
    
    
class Case(TimestampedModel):
    # ---------- Tracking ID ----------
    tracking_id = models.CharField(max_length=30, unique=True, editable=False)

    # ---------- Status ----------
    STATUS_CHOICES = [
        ('not_received', 'Not Received'),          # LGU created, still editable
        ('received', 'Received'),                  # Capitol marked receipt
        ('in_review', 'In Review'),
        ('for_approval', 'For Approval'),
        ('approved', 'Approved'),
        ('for_numbering', 'For Numbering'),
        ('for_release', 'For Release'),
        ('released', 'Released'),
        ('returned', 'Returned for Correction'),
        ('withdrawn', 'Withdrawn'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_received')

    # ---------- Client info ----------
    client_name = models.CharField(max_length=255)
    client_contact = models.CharField(max_length=100, blank=True)   # phone / email

    # ---------- LGU who submitted ----------
    submitted_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='submitted_cases'
    )

    # ---------- Checklist (JSON) ----------
    checklist = models.JSONField(
        default=list,
        help_text="List of dicts: [{'doc_type': 'Land Title', 'required': True, 'uploaded': False}]"
    )

    # ---------- Optional scanned files ----------
    # We'll store files in media/cases/<tracking_id>/
    # (FileField will be added later when MEDIA is configured)

    # ---------- Timestamps ----------
    received_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Case"
        verbose_name_plural = "Cases"

    def __str__(self):
        return f"{self.tracking_id} – {self.client_name}"

    # ------------------------------------------------------------------
    #  Auto-generate tracking_id: CEB-YYYYMMDD-#####
    # ------------------------------------------------------------------
    def generate_tracking_id(self):
        today = timezone.now().strftime('%Y%m%d')
        prefix = f"CEB-{today}"
        last = Case.objects.filter(tracking_id__startswith=prefix).count()
        return f"{prefix}-{last+1:05d}"

    # ------------------------------------------------------------------
    #  Save override
    # ------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.tracking_id:
            self.tracking_id = self.generate_tracking_id()
        super().save(*args, **kwargs)