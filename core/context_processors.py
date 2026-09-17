from django.conf import settings


def site_settings(request):
    """
    Makes SITE_NAME, SITE_DOMAIN and the Google Analytics / AdSense IDs
    available in every template (base.html / header / footer) without
    passing them from each view manually.
    """
    return {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_DOMAIN': settings.SITE_DOMAIN,
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
        'GOOGLE_ADSENSE_CLIENT_ID': settings.GOOGLE_ADSENSE_CLIENT_ID,
    }
