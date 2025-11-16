from django.contrib import admin
from .models import AuditLog, Case, CustomUser
from django import forms
from django.contrib.auth.hashers import make_password

class CustomUserCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'full_name', 'role')

    def save(self, commit=True, created_by=None):
        user = super().save(commit=False)
        user.created_by = created_by
        if commit:
            user.save(created_by=created_by)
        return user


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'full_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active')
    search_fields = ('email', 'full_name', 'username')
    readonly_fields = ('username', 'date_joined', 'last_login')
    add_form = CustomUserCreationForm
    add_fieldsets = (
        (None, {
            'fields': ('email', 'full_name', 'role'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Only on create
            obj.save(created_by=request.user)  # Pass created_by
        else:
            obj.save()
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'actor', 'target_object', 'created_at')
    list_filter = ('action', 'created_at', 'actor')
    search_fields = ('actor__email', 'target_object', 'details')
    readonly_fields = ('created_at', 'updated_at', 'actor', 'action', 'target_object', 'details', 'ip_address', 'user_agent')
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation
    
    def has_change_permission(self, request, obj=None):
        return False  # Prevent editing
    
    def has_delete_permission(self, request, obj=None):
        return False  # Prevent deletion

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('tracking_id', 'client_name', 'status', 'submitted_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('tracking_id', 'client_name', 'submitted_by__email')
    readonly_fields = ('tracking_id', 'created_at', 'updated_at', 'received_at')

