from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path("", views.login_view, name="login_view"),
    path("signup/", views.sign_up_view, name="sign_up_view"),
    path("logout/", views.logout_view, name="logout_view"),
]