from django.test import SimpleTestCase, override_settings
from django.urls import path


def trigger_500_view(request):
    raise RuntimeError('Simulated server error for testing custom 500 page.')


urlpatterns = [
    path('trigger-500/', trigger_500_view),
]


@override_settings(DEBUG=False)
class ErrorPagesTests(SimpleTestCase):
    def test_404_uses_custom_template(self):
        response = self.client.get('/this-page-does-not-exist/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'errors/404.html')

    @override_settings(ROOT_URLCONF=__name__)
    def test_500_uses_custom_template(self):
        response = self.client.get('/trigger-500/')
        self.assertEqual(response.status_code, 500)
        self.assertTemplateUsed(response, 'errors/500.html')
