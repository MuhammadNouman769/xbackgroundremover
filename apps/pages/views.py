from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from .forms import ContactForm


def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    return render(request, 'errors/500.html', status=500)


class AboutView(TemplateView):
    template_name = 'pages/about.html'


class TermsView(TemplateView):
    template_name = 'pages/terms.html'


class PrivacyView(TemplateView):
    template_name = 'pages/privacy.html'


class ContactView(FormView):
    template_name = 'pages/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('pages:contact')

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            "Thanks! Your message has been received — we'll get back to you soon.",
        )
        return super().form_valid(form)
