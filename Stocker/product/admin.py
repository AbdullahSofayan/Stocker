from django.contrib import admin
from .models import Category, Supplier, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    ordering = ('name',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'created_at', 'updated_at')
    search_fields = ('name', 'phone')
    ordering = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'sku', 'category', 'quantity',
        'reorder_level', 'cost_price', 'stock_status', 'expiry_date', 'created_at'
    )
    list_filter = ('category', 'stock_status', 'supplier', 'expiry_date')
    search_fields = ('name', 'sku', 'description')
    ordering = ('name',)
    filter_horizontal = ('supplier',)  # For ManyToMany supplier selection
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'sku', 'category', 'description', 'image')
        }),
        ('Inventory Details', {
            'fields': ('quantity', 'reorder_level', 'cost_price', 'stock_status')
        }),
        ('Suppliers', {
            'fields': ('supplier',)
        }),
        ('Expiry Info', {
            'fields': ('expiry_date',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

