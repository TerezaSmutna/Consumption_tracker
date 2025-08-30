import logging
from smtplib import SMTPSenderRefused, SMTPException

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.contrib import admin, messages
from django.contrib.admin.sites import AlreadyRegistered

from django_otp.plugins.otp_static.models import StaticToken, StaticDevice
from django_otp.conf import settings

from users.forms import CustomAdminUserCreationForm, CustomAdminUserChangeForm
from users.utils import send_verification_email, send_email_and_handle_messages

logger = logging.getLogger(__name__)


class CustomUserAdmin(UserAdmin):
    add_form = CustomAdminUserCreationForm
    form = CustomAdminUserChangeForm
    actions = ['resend_verification_email']
    search_fields = ('id', 'username', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('parent', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'organization', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions', 'groups')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        # ('Contact info', {'fields': ('contact_no',)}),
        ('Security', {'fields': ('_active_token',)})
    )

    add_fieldsets = (
        (None, {
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Check if the object is being created (and not just updated)
        if not change:
            send_email_and_handle_messages(request, obj)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial['is_active'] = False
        return initial

    @admin.action(description='Resend verification email to selected users')
    def resend_verification_email(self, request, queryset):
        for user in queryset:
            send_email_and_handle_messages(request, user)


admin.site.register(get_user_model(), CustomUserAdmin)


# OVERRIDE OF StaticDeviceAdmin FROM django-otp to include Throttling fields

class StaticTokenInline(admin.TabularInline):
    model = StaticToken
    extra = 0


class StaticDeviceAdmin(admin.ModelAdmin):
    """
    :class:`~django.contrib.admin.ModelAdmin` for
    :class:`~django_otp.plugins.otp_static.models.StaticDevice`.
    """

    fieldsets = [
        (
            'Identity',
            {
                'fields': ['user', 'name', 'confirmed'],
            },
        ),
    ]
    raw_id_fields = ['user']

    inlines = [
        StaticTokenInline,
    ]

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (
                'Identity',
                {
                    'fields': ['user', 'name', 'confirmed'],
                },
            ),
            (
                'Throttling',
                {
                    'fields': [
                        'throttling_failure_timestamp',
                        'throttling_failure_count',
                    ],
                },
            ),
        ]
        return fieldsets

    def get_inline_instances(self, request, obj=None):
        if settings.OTP_ADMIN_HIDE_SENSITIVE_DATA and obj:
            return []
        return super().get_inline_instances(request, obj)


# Somehow this is getting imported twice, triggering a useless exception.
# (This is just copied from django-otp, it might be unnecessary.)
try:
    admin.site.register(StaticDevice, StaticDeviceAdmin)
except AlreadyRegistered:
    pass
