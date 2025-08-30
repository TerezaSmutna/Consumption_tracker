import logging

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm, AuthenticationForm, \
    PasswordChangeForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserChangeForm

from two_factor.forms import AuthenticationTokenForm


logger = logging.getLogger(__name__)
User = get_user_model()


class CustomAdminUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        self.fields['password1'].widget = forms.HiddenInput()
        self.fields['password2'].widget = forms.HiddenInput()


class CustomAdminUserChangeForm(UserChangeForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = "__all__"


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super(CustomAuthenticationForm, self).__init__(request=request, *args, **kwargs)

        self.fields['username'].widget.attrs.update({'class': 'form-control form-control-xl',
                                                     'placeholder': 'Username / E-mail'})

        self.fields['password'].widget.attrs.update({'class': 'form-control form-control-xl',
                                                     'placeholder': 'Password'})


class CustomAuthenticationTokenForm(AuthenticationTokenForm):

    def _chosen_device(self, user):
        device = super()._chosen_device(user)
        if not device:
            device = self.initial_device
        return device


class CustomBackupTokenForm(CustomAuthenticationTokenForm):
    otp_token = forms.CharField(label=_("Token"))


class CustomPasswordResetForm(PasswordResetForm):
    def save(
            self,
            domain_override=None,
            subject_template_name="registration/password_reset_subject.txt",
            email_template_name="registration/password_reset_email.html",
            use_https=False,
            token_generator=default_token_generator,
            from_email=None,
            request=None,
            html_email_template_name=None,
            extra_email_context=None,
    ):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        email = self.cleaned_data["email"]
        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override
        email_field_name = User.get_email_field_name()
        for user in self.get_users(email):
            user_email = getattr(user, email_field_name)

            ### I am modifying here to save a token ###
            token = token_generator.make_token(user)
            user.active_token = token
            ###########################################

            context = {
                "email": user_email,
                "domain": domain,
                "site_name": site_name,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                "token": token,
                "protocol": "https" if use_https else "http",
                **(extra_email_context or {}),
            }
            self.send_mail(
                subject_template_name,
                email_template_name,
                context,
                from_email,
                user_email,
                html_email_template_name=html_email_template_name,
            )

    def __init__(self, *args, **kwargs):
        super(CustomPasswordResetForm, self).__init__(*args, **kwargs)

        self.fields['email'].widget.attrs.update({'class': 'form-control form-control-xl',
                                                  'type': 'email',
                                                  'placeholder': 'E-mail'})


class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(CustomSetPasswordForm, self).__init__(*args, **kwargs)

        self.fields['new_password1'].widget.attrs.update({'class': 'form-control form-control-xl',
                                                          'type': 'password',
                                                          'placeholder': 'Password'})

        self.fields['new_password2'].widget.attrs.update({'class': 'form-control form-control-xl',
                                                          'type': 'password',
                                                          'placeholder': 'Confirm password'})

    def clean_new_password1(self):
        new_password1 = self.cleaned_data.get('new_password1')
        if new_password1:
            if self.user.check_password(new_password1):
                raise ValidationError("New password can't be the same as the current password.")
        return new_password1


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(CustomPasswordChangeForm, self).__init__(*args, **kwargs)

        self.fields['old_password'].widget.attrs.update({'class': 'form-control',
                                                         'type': 'password',
                                                         })

        self.fields['new_password1'].widget.attrs.update({'class': 'form-control',
                                                          'type': 'password',
                                                          })

        self.fields['new_password2'].widget.attrs.update({'class': 'form-control',
                                                          'type': 'password',
                                                          })

    def clean_new_password1(self):
        new_password1 = self.cleaned_data.get('new_password1')
        if new_password1:
            if self.user.check_password(new_password1):
                raise ValidationError("New password can't be the same as the current password.")
        return new_password1


class CreateAccountForm(CustomSetPasswordForm):
    email = forms.EmailField(
        label=_('Email'),
        required=True,
        disabled=True,
        widget=forms.EmailInput(attrs={'class': 'form-control form-control-xl',
                                       'placeholder': _('E-mail')})
    )
    first_name = forms.CharField(
        label=_('First Name'),
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-xl',
                                      'placeholder': _('First name')})
    )
    last_name = forms.CharField(
        label=_('Last Name'),
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-xl',
                                      'placeholder': _('Last name')})
    )
    organization = forms.CharField(
        label=_('Organization'),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-xl',
                                      'placeholder': _('Organization')})
    )
    phone_number = forms.CharField(
        label=_('Phone number'),
        max_length=15,
        required=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$',
                                   message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")],
        widget=forms.TextInput(attrs={'class': 'form-control form-control-xl',
                                      'placeholder': _('Phone number')})
    )

    def __init__(self, *args, **kwargs):
        super(CreateAccountForm, self).__init__(*args, **kwargs)
        self.fields['email'].initial = self.user.email
        self.fields['first_name'].initial = self.user.first_name
        self.fields['last_name'].initial = self.user.last_name

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        self.user.email = self.cleaned_data['email']
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.organization = self.cleaned_data['organization']
        self.user.phone_number = self.cleaned_data['phone_number']
        self.user.is_active = True

        if commit:
            self.user.save()
        return self.user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'organization', 'phone_number')

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class UserProfileFormDisabled(UserProfileForm):
    def __init__(self, *args, **kwargs):
        super(UserProfileFormDisabled, self).__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
            field.disabled = True