from django.urls import path
from . import views

app_name = 'product'

urlpatterns = [
    path("", views.inventory_view , name="inventory_view"),
    path("add/product/", views.add_product_view , name="add_product_view"),
]