from django.urls import path
from . import views

app_name = 'product'

urlpatterns = [
    path("", views.inventory_view , name="inventory_view"),
    path("add/product/", views.add_product_view , name="add_product_view"),
    path("edit/<int:product_id>/", views.edit_product_view, name="edit_product_view"),
    path('inventory/delete/<int:product_id>/', views.delete_product_view, name='delete_product_view'),
    path('<int:product_id>/details/', views.details_product_view, name='details_product_view'),


]