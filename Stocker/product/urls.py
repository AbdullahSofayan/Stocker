from django.urls import path
from . import views

app_name = 'product'

urlpatterns = [
    path("", views.inventory_view , name="inventory_view"),
    path("add/product/", views.add_product_view , name="add_product_view"),
    path("edit/<int:product_id>/", views.edit_product_view, name="edit_product_view"),
    path('inventory/delete/<int:product_id>/', views.delete_product_view, name='delete_product_view'),
    path('<int:product_id>/details/', views.details_product_view, name='details_product_view'),
    path('categories/', views.categories_view, name='categories_view'),
    path('categories/<int:category_id>/edit/', views.edit_category_view, name='edit_category_view'),
    path('categories/<int:category_id>/delete/', views.delete_category_view, name='delete_category_view'),
    path('categories/add', views.add_category_view, name='add_category_view'),
    path('suppliers/', views.suppliers_view, name='suppliers_view'),
    path('suppliers/add', views.add_supplier_view, name='add_supplier_view'),
    path('suppliers/<int:supplier_id>/delete/', views.delete_supplier_view, name='delete_supplier_view'),
    path('suppliers/<int:supplier_id>/edit/', views.edit_supplier_view, name='edit_supplier_view'),
    path('suppliers/<int:supplier_id>/details/', views.supplier_details_view, name='supplier_details_view'),
    path("export/csv/", views.export_products_csv, name="export_products_csv"),
    path("import/csv/", views.import_products_csv, name="import_products_csv"),
    path("reports/inventory.csv", views.inventory_report_csv, name="inventory_report_csv"),
    path("reports/suppliers.csv", views.supplier_report_csv, name="supplier_report_csv"),






]