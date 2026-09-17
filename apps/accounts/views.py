from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import LoginForm, SignUpForm


class SignUpView(CreateView):
    """
    Handles new-user registration. On success the user is logged in
    immediately (no email verification step -> keep it frictionless for
    people arriving from a Google Ad).
    """
    form_class = SignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('remover:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, f'Welcome to Xbg Remove, {self.object.username}!')
        return response


class XbgLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, 'Logged in successfully.')
        return super().form_valid(form)


class XbgLogoutView(LogoutView):
    next_page = reverse_lazy('remover:home')
