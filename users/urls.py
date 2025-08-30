from django.urls import path
from django.views.generic import RedirectView

from . import views


app_name = 'users'
urlpatterns = [
    # PROFILES
    path('accounts/profile/', views.user_profile, name='profile'),
    path('accounts/profile/edit/', views.edit_user_profile, name='edit_profile'),

]
