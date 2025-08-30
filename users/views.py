import logging

from axes.handlers.proxy import AxesProxyHandler
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetConfirmView, INTERNAL_RESET_SESSION_TOKEN, PasswordResetView, \
    PasswordResetCompleteView, PasswordChangeView, PasswordChangeDoneView
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_GET
from django_otp.plugins.otp_totp.models import TOTPDevice
from two_factor.plugins.registry import GeneratorMethod, registry
from two_factor.views import LoginView, DisableView
from two_factor.views.utils import class_view_decorator

from .forms import CustomPasswordResetForm, CustomSetPasswordForm, \
    CustomAuthenticationForm, CreateAccountForm, UserProfileFormDisabled, \
    UserProfileForm, CustomPasswordChangeForm, CustomAuthenticationTokenForm, \
    CustomBackupTokenForm
from .tokens import account_activation_token_generator

logger = logging.getLogger(__name__)
User = get_user_model()


@require_GET
@login_required(login_url='login')
def user_profile(request):
    user = request.user

    form = UserProfileFormDisabled(instance=user)

    context = {'user': user, 'form': form, }
    return render(request, 'users/profile.html', context)


@login_required(login_url='login')
def edit_user_profile(request):
    user = request.user

    if request.method == 'POST':
        logger.debug(request.POST)
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, _('User profile updated successfully'))
            return redirect('users:profile')
        else:
            logger.debug(form.errors)
            messages.error(request, _('Failed to update user profile.'))
    else:
        form = UserProfileForm(instance=user)

    context = {'user': user, 'form': form, 'edit': True}
    return render(request, 'users/profile.html', context)


class CustomLoginView(LoginView):
    """
    Custom LoginView that implements two-factor authentication. This view handles three steps: authentication,
    token verification and backup token verification.
    """
    AUTH_STEP = "auth"
    TOKEN_STEP = "token"
    BACKUP_STEP = "backup"

    form_list = (
        (AUTH_STEP, CustomAuthenticationForm),
        (TOKEN_STEP, CustomAuthenticationTokenForm),
        (BACKUP_STEP, CustomBackupTokenForm),
    )

    def get_form(self, step=None, **kwargs):
        """
        Returns the form for the current step or the specified step. The form for the token step is determined
        dynamically based on the two-factor method of the user's device. If the session has timed out, an error is added
        to the form.

        Args:
            step (str, optional): The key of the step for which to return the form. If not specified, the current step
                                  of the view is used.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            form: The form for the specified step.

        Raises:
            ValidationError: If the session has timed out.
        """
        if (step or self.steps.current) == self.TOKEN_STEP:
            method = registry.method_from_device(self.get_device())
            logger.debug(f'{method=}')
            if not isinstance(method, GeneratorMethod):
                self.form_list[self.TOKEN_STEP] = method.get_token_form_class()

        form = super(LoginView, self).get_form(step=step, **kwargs)
        if self.show_timeout_error:
            form.cleaned_data = getattr(form, 'cleaned_data', {})
            form.add_error(None, ValidationError(_('Your session has timed out. Please login again.')))
        return form


@class_view_decorator(never_cache)
class CustomDisableView(DisableView):
    form_class = CustomAuthenticationTokenForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.request.user
        kwargs['user'] = user
        # The current implementation assumes only one TOTP device.
        kwargs['initial_device'] = TOTPDevice.objects.devices_for_user(user, confirmed=True).last()
        return kwargs


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'registration/password_reset.html'

    def form_valid(self, form):
        axes_handler = AxesProxyHandler()
        email = form.cleaned_data.get('email')  # Assuming you are using email as the identifier
        target_user = User.objects.filter(email=email).first()
        logger.debug(f'{target_user=}')

        if target_user:
            # Check if the user is already locked
            # if axes_handler.is_locked(self.request, credentials={'username': f'{target_user.username}_pwdreset'}):
            #     # handle your rate limit case here, for example:
            #     return HttpResponse('You have been rate limited.', status=429)

            # If reset password was successful, increment attempts
            axes_handler.user_login_failed(sender=self.__class__,
                                           credentials={'username': f'{target_user.username}_pwdreset'},
                                           request=self.request)

        return super().form_valid(form)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomSetPasswordForm
    template_name = 'registration/password_reset_confirm.html'

    # success_url = reverse_lazy('two_factor:setup')

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        if "uidb64" not in kwargs or "token" not in kwargs:
            raise ImproperlyConfigured(
                "The URL path must contain 'uidb64' and 'token' parameters."
            )

        self.validlink = False
        self.user = self.get_user(kwargs["uidb64"])

        if self.user is not None:
            token = kwargs["token"]

            if token == self.reset_url_token:
                session_token = self.request.session.get(INTERNAL_RESET_SESSION_TOKEN)
                if self.token_generator.check_token(self.user, session_token):
                    # If the token is valid, display the password reset form.
                    self.validlink = True
                    return super().dispatch(*args, **kwargs)
            else:
                ### My modification ###
                # Check if user's token in link is active. If yes, continue with validation.
                # Be aware that if the token is invalidated after this check, token is stored in the session
                # and user is able to finish the password reset.
                if self.user.active_token == token:
                    #######################

                    if self.token_generator.check_token(self.user, token):
                        # Store the token in the session and redirect to the
                        # password reset form at a URL without the token. That
                        # avoids the possibility of leaking the token in the
                        # HTTP Referer header.
                        self.request.session[INTERNAL_RESET_SESSION_TOKEN] = token
                        redirect_url = self.request.path.replace(
                            token, self.reset_url_token
                        )
                        return HttpResponseRedirect(redirect_url)

        # Display the "Password reset unsuccessful" page.
        return self.render_to_response(self.get_context_data())


class ActivationConfirmView(CustomPasswordResetConfirmView):
    form_class = CreateAccountForm
    reset_url_token = "set-account-information"
    success_url = reverse_lazy("account_activation_complete")
    title = _("Create account")
    token_generator = account_activation_token_generator


class ActivationCompleteView(PasswordResetCompleteView):
    title = _("Activation complete")


class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    success_url = reverse_lazy('users:profile')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Your password was successfully updated!'))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # user_domains = get_objects_for_user(self.request.user, perm='domains.read_domain')
        # context['user_domains'] = user_domains
        return context


class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # user_domains = get_objects_for_user(self.request.user, perm='domains.read_domain')
        # context['user_domains'] = user_domains
        context['user'] = self.request.user
        return context
