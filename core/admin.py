from django.contrib import admin
from .models import AuditLog, CustomUser
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
        if not change:
            form.created_by = request.user
        super().save_model(request, obj, form, change)
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


