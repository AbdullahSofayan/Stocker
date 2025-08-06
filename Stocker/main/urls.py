from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path("", views.Home_view, name="Home_view")
]