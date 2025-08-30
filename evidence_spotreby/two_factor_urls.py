from django.urls import path
from two_factor.views import (
    BackupTokensView, DisableView, ProfileView, QRGeneratorView,
    SetupCompleteView, SetupView,
)

from users.views import CustomDisableView

app_name = 'two_factor'  # This sets the application namespace

urlpatterns = [
    path('setup/', SetupView.as_view(), name='setup'),
    path('qrcode/', QRGeneratorView.as_view(), name='qr'),
    path('setup/complete/', SetupCompleteView.as_view(), name='setup_complete'),
    path('backup/tokens/', BackupTokensView.as_view(), name='backup_tokens'),
    path('', ProfileView.as_view(), name='profile'),
    path('disable/', CustomDisableView.as_view(), name='disable'),
]