from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
<<<<<<< HEAD
    path("dashboard/", views.dashboard_view, name="dashboard_view"),
   
=======
    path("", views.Home_view, name="Home_view")
>>>>>>> 93c65be4906da29330fd850b320161ef5417f727
]