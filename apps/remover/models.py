import uuid

from django.conf import settings
from django.db import models


def upload_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'uploads/{uuid.uuid4().hex}.{ext}'


def processed_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'processed/{uuid.uuid4().hex}.{ext}'


class ProcessedImage(models.Model):
    """
    One row per background-removal job. `user` is nullable so guests
    (not logged in) can still try the tool once — matching the
    removal.ai UX shown in the reference screenshot — while logged-in
    users build up a history under their account.
    """

    class BackgroundType(models.TextChoices):
        TRANSPARENT = 'transparent', 'Transparent'
        COLOR = 'color', 'Solid colour'
        IMAGE = 'image', 'Custom background image'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='processed_images',
        null=True,
        blank=True,
    )
    original_image = models.ImageField(upload_to=upload_path)
    processed_image = models.ImageField(upload_to=processed_path, blank=True, null=True)
    background_type = models.CharField(
        max_length=20, choices=BackgroundType.choices, default=BackgroundType.TRANSPARENT
    )
    background_color = models.CharField(max_length=7, blank=True, default='')  # hex, e.g. #FFFFFF
    background_image = models.ImageField(upload_to='backgrounds/', blank=True, null=True)
    is_successful = models.BooleanField(default=False)
    error_message = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        who = self.user.username if self.user_id else 'guest'
        return f'Job #{self.pk} ({who}) - {self.get_background_type_display()}'
