from django.db import models
from django.contrib.auth.models import AbstractUser

from django import utils
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from users.tokens import account_activation_token_generator


class User(AbstractUser):
    email = models.EmailField(blank=True, max_length=254, unique=True, verbose_name=_('Email address'))
    # who created this account
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_('Parent'))

    organization = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('Organization'))
    phone_number = models.CharField(null=True, blank=True, max_length=30, verbose_name=_('Phone number'))
    language = models.CharField(default='en', max_length=3, verbose_name=_('Language'))

    date_activated = models.DateTimeField(null=True, blank=True, verbose_name=_('Date activated'))

    _active_token = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Active token'))

    @property
    def active_token(self):
        return self._active_token

    @active_token.setter
    def active_token(self, value):
        self._active_token = value
        self.save()

    def generate_url_args(self, token_generator):
        base64_encoded_id = utils.http.urlsafe_base64_encode(utils.encoding.force_bytes(self.id))
        token = token_generator.make_token(self)
        self.active_token = token
        url_args = {'uidb64': base64_encoded_id, 'token': token}
        return url_args

    def get_password_reset_path(self):
        reset_url_args = self.generate_url_args(PasswordResetTokenGenerator())
        reset_path = reverse('password_reset_confirm', kwargs=reset_url_args)
        return reset_path

    def get_account_verification_path(self):
        activation_url_args = self.generate_url_args(account_activation_token_generator)
        activation_path = reverse('activation_confirm', kwargs=activation_url_args)
        return activation_path