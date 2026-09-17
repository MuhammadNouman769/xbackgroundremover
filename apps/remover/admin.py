from django.contrib import admin

from .models import ProcessedImage


@admin.register(ProcessedImage)
class ProcessedImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'background_type', 'is_successful', 'created_at')
    list_filter = ('background_type', 'is_successful', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at',)
