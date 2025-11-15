from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import secrets
import string
from django.core.mail import send_mail
from django.conf import settings

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
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, blank=False, null=False)

    # Use email for login instead of username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name', 'role']  # username still required by Django

    def __str__(self):
        return f"{self.full_name} ({self.email}) - {self.get_role_display()}"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
    def generate_staff_id(role_prefix):
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

    def generate_temp_password():
        """Generate strong 12-char temp password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(12))

    def send_activation_email(user, temp_password):
        subject = "Your LegalTrack Account Has Been Created"
        message = f"""
        Hello {user.full_name},

        Your account has been created.

        Staff ID: {user.username}
        Email: {user.email}
        Temporary Password: {temp_password}

        Please log in at: http://127.0.0.1:8000/accounts/login/
        You will be forced to change your password on first login.

        Thank you,
        Cebu Provincial Capitol
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            # Generate Staff ID as username
            self.username = self.generate_staff_id(self.role)
            
            # Generate temp password
            if not self.password or 'temp' in self.password:
                temp_password = self.generate_temp_password()
                self.set_password(temp_password)
                self.is_active = False  # Inactive until activation
            else:
                temp_password = None

        super().save(*args, **kwargs)

        if is_new and temp_password:
            # Send email after save
            self.send_activation_email(self, temp_password)
            
            # Log creation
            AuditLog.objects.create(
                actor=kwargs.get('created_by'),  # We'll pass this from view
                action='create_user',
                target_user=self,
                target_object=f"User: {self.email}",
                details={'staff_id': self.username}
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
    
