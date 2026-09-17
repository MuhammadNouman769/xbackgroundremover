from django import forms
from django.conf import settings

from .models import ProcessedImage

ALLOWED_CONTENT_TYPES = ('image/jpeg', 'image/jpg', 'image/png', 'image/webp')


class UploadImageForm(forms.ModelForm):
    background_color = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
    )

    class Meta:
        model = ProcessedImage
        fields = ['original_image', 'background_type', 'background_color', 'background_image']
        widgets = {
            'original_image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/png,image/jpeg,image/webp',
            }),
            'background_type': forms.RadioSelect,
            'background_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_original_image(self):
        image = self.cleaned_data['original_image']
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if image.size > max_size:
            raise forms.ValidationError(
                f'Image is too large. Max allowed size is {settings.MAX_UPLOAD_SIZE_MB} MB.'
            )
        content_type = getattr(image, 'content_type', '')
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            raise forms.ValidationError('Please upload a JPG, PNG or WEBP image.')
        return image
