from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

handler404 = 'apps.pages.views.custom_404'
handler500 = 'apps.pages.views.custom_500'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('', include('apps.pages.urls')),
    path('', include('apps.remover.urls')),
]

# Serve uploaded / processed images in development.
# In production this is handled by nginx / whitenoise / your CDN instead.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
