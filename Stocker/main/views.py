# main/views.py
from datetime import timedelta
from django.db.models import Count, F, Q
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from product.models import Product, Category, Supplier

@login_required
def dashboard_view(request):
    today = timezone.localdate()
    soon  = today + timedelta(days=30)

    total_products       = Product.objects.count()
    total_categories     = Category.objects.count()
    low_stock_count      = Product.objects.filter(quantity__lte=F('reorder_level')).count()
    out_of_stock_count   = Product.objects.filter(Q(stock_status='out_of_stock') | Q(quantity__lte=0)).count()

   
    low_stock = (
        Product.objects
        .filter(quantity__lte=F('reorder_level'))
        .order_by('quantity')[:10]
    )

    expiring_soon = (
        Product.objects
        .filter(expiry_date__isnull=False, expiry_date__gte=today, expiry_date__lte=soon)
        .order_by('expiry_date')[:10]
    )

    recent_activity = (
        Product.objects
        .order_by('-updated_at')[:10]
        .values('name', 'updated_at', 'sku')
    )

    supplier_perf = (
        Supplier.objects
        .annotate(total_products=Count('products'))
        .order_by('-total_products')[:10]
        .values('name', 'total_products')
    )

    # Charts data
    status_breakdown = (
        Product.objects
        .values('stock_status')
        .annotate(total=Count('id'))
        .order_by('stock_status')
    )

    top_products = (
        Product.objects
        .order_by('-quantity')
        .values('name', 'quantity')[:6]
    )

    # very simple “activity by day” over last 7 days (updates)
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    by_day = []
    for d in days:
        next_d = d + timedelta(days=1)
        by_day.append({
            "label": d.strftime("%b %d"),
            "count": Product.objects.filter(updated_at__date__gte=d, updated_at__date__lt=next_d).count()
        })

    context = {
        # headline stats
        "stats": {
            "total_products": total_products,
            "low_stock": low_stock_count,
            "out_of_stock": out_of_stock_count,
            "total_categories": total_categories,
        },

        # tables
        "low_stock_rows": low_stock,
        "expiring_rows": expiring_soon,
        "recent_activity": list(recent_activity),
        "supplier_perf": list(supplier_perf),

        # charts (serialize-friendly)
        "chart_status": list(status_breakdown),
        "chart_top_products": list(top_products),
        "chart_daily": by_day,
    }
    return render(request, "main/dashboard.html", context)
