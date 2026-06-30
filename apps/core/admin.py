from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_id', 'ip_address', 'created_at']
    list_filter = ['action', 'model_name']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'changes', 'ip_address']
