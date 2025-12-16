from __future__ import annotations

import secrets
import string
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

class CustomUser(AbstractUser):
    # Role choices based on spec
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
    designation = models.CharField(max_length=120, blank=True)
    position = models.CharField(max_length=120, blank=True)
    # role = models.CharField(max_length=50, choices=ROLE_CHOICES, blank=False, null=False)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, null=False)

    # Module 1.2: force password change on first login for admin-created accounts
    must_change_password = models.BooleanField(default=False)

    ACCOUNT_STATUS_CHOICES = [
        ('pending', 'Pending Activation'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUS_CHOICES, default='pending')
    activation_nonce = models.CharField(max_length=64, blank=True, default='')
    activation_sent_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    temp_password_created_at = models.DateTimeField(null=True, blank=True)

    # Security (Module 1): account lockout after consecutive failed logins
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    lockout_until = models.DateTimeField(null=True, blank=True)
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

    def issue_activation(self, *, request, temp_password: str, send_email: bool | None = None) -> str:
        """Issue a 1-hour activation link and record activation metadata.

        When email sending is disabled (common in local/dev), the activation link
        is returned so the caller can display it on-screen.

        The temp password itself expires after 7 days.
        """
        from django.core import signing
        from django.urls import reverse

        now = timezone.now()
        self.account_status = 'pending'
        self.is_active = False
        self.activation_sent_at = now
        self.activation_nonce = secrets.token_urlsafe(24)
        if not self.temp_password_created_at:
            self.temp_password_created_at = now
        self.save(update_fields=['account_status', 'is_active', 'activation_sent_at', 'activation_nonce', 'temp_password_created_at'])

        token = signing.dumps(
            {'uid': self.pk, 'nonce': self.activation_nonce},
            salt='core.activate',
        )
        activation_link = request.build_absolute_uri(reverse('activate_account', kwargs={'token': token}))

        if send_email is None:
            send_email = bool(getattr(settings, 'LEGALTRACK_SEND_EMAILS', True))

        subject = 'Activate Your LegalTrack Account'
        message = (
            f"Hello {self.full_name or self.email},\n\n"
            "Your LegalTrack account has been created.\n\n"
            f"Staff ID: {self.username}\n"
            f"Email: {self.email}\n"
            f"Temporary Password: {temp_password}\n\n"
            "Activate your account using this link (expires in 1 hour):\n"
            f"{activation_link}\n\n"
            "You will be required to set a new strong password during activation.\n\n"
            "If your temporary password expires (7 days), contact the Super Admin for a manual resend.\n"
        )

        if send_email:
            send_mail(
                subject,
                message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@cebu.gov.ph'),
                [self.email],
                fail_silently=False,
            )

        return activation_link

    def save(self, *args, **kwargs):
        created_by = kwargs.pop('created_by', None)
        is_new = self.pk is None

        if is_new:
            # Generate Staff ID
            self.username = self.generate_staff_id(self.role)

            # If password was already set by the creator workflow, keep it.
            # Otherwise, generate a temp password.
            temp_password = None
            if not self.password:
                temp_password = self.generate_temp_password()
                self.set_password(temp_password)
                self.must_change_password = True

            # Module 1: new accounts start in Pending Activation
            self.account_status = 'pending'
            self.is_active = False
            self.temp_password_created_at = self.temp_password_created_at or timezone.now()

        # Keep is_active consistent with account_status when not pending.
        if self.account_status == 'active':
            self.is_active = True
        elif self.account_status in {'pending', 'inactive'}:
            self.is_active = False

        super().save(*args, **kwargs)

        if is_new:
            # Optional: Log password in console for dev
            if settings.DEBUG and temp_password:
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
                    'account_status': self.account_status,
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
        ('login_failed', 'User Login Failed'),
        ('logout', 'User Logout'),
        ('create_user', 'Create User Account'),
        ('update_user', 'Update User Account'),
        ('deactivate_user', 'Deactivate User'),
        ('reactivate_user', 'Reactivate User'),
        ('reset_password', 'Reset Password'),
        ('activation_email_sent', 'Activation Email Sent'),
        ('activate_account', 'Account Activated'),
        ('password_reset_request', 'Password Reset Requested'),
        ('password_reset_complete', 'Password Reset Completed'),
        ('case_create', 'Case Created'),
        ('case_update', 'Case Updated'),
        ('case_status_change', 'Case Status Changed'),
        ('case_receipt', 'Case Physically Received'),
        ('case_assignment', 'Case Assigned'),
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


class PasswordResetRequest(models.Model):
    email = models.EmailField()
    requested_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['requested_at']),
        ]
    
    
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
    received_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_cases'
    )
    received_at = models.DateTimeField(null=True, blank=True)

    returned_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='returned_cases'
    )
    returned_at = models.DateTimeField(null=True, blank=True)
    return_reason = models.TextField(blank=True)

    # ---------- Assignment (Module 3.1) ----------
    assigned_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_cases'
    )
    assigned_at = models.DateTimeField(null=True, blank=True)

    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Case"
        verbose_name_plural = "Cases"

    def __str__(self):
        return f"{self.tracking_id} – {self.client_name}"

    # ------------------------------------------------------------------
    # Auto-generate tracking_id: CEB[YY][MM][#####]
    # - Example: CEB251200001
    # - Serial resets annually (YY)
    # ------------------------------------------------------------------
    def generate_tracking_id(self):
        now = timezone.localtime(timezone.now())
        yy = now.strftime('%y')
        mm = now.strftime('%m')

        year_prefix = f"CEB{yy}"
        full_prefix = f"CEB{yy}{mm}"

        existing_ids = Case.objects.filter(
            tracking_id__startswith=year_prefix
        ).values_list('tracking_id', flat=True)

        max_seq = 0
        for tid in existing_ids:
            if isinstance(tid, str) and len(tid) >= 5 and tid[-5:].isdigit():
                max_seq = max(max_seq, int(tid[-5:]))

        return f"{full_prefix}{max_seq + 1:05d}"

    # ------------------------------------------------------------------
    #  Save override
    # ------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.tracking_id:
            self.tracking_id = self.generate_tracking_id()
        super().save(*args, **kwargs)


def case_document_upload_to(instance, filename: str) -> str:
    tracking = getattr(getattr(instance, 'case', None), 'tracking_id', 'unknown')
    doc_type = slugify(getattr(instance, 'doc_type', '') or 'document')
    return f"cases/{tracking}/{doc_type}/{filename}"


class CaseDocument(TimestampedModel):
    case = models.ForeignKey('Case', on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=120)
    file = models.FileField(upload_to=case_document_upload_to)
    uploaded_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_case_documents',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        constraints = [
            models.UniqueConstraint(fields=['case', 'doc_type'], name='uniq_case_doc_type'),
        ]

    def __str__(self):
        return f"{self.case.tracking_id} – {self.doc_type}"