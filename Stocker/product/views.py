<<<<<<< HEAD
from django.http import HttpRequest
from django.shortcuts import render, redirect
from .models import Product, Supplier, Category
from datetime import date
from django.contrib import messages
# Create your views here.

def inventory_view(request: HttpRequest):
    products = Product.objects.all()
    return render(request, 'inventory.html', {'products': products})

def add_product_view(request: HttpRequest):
    suppliers = Supplier.objects.all()
    categories = Category.objects.all()

    today = date.today().isoformat()

    if request.method == "POST":
        name = request.POST['name']
        sku = request.POST['sku']
        category_id = request.POST['category']
        quantity = request.POST['quantity']
        reorder_level = request.POST['reorder_level']
        cost_price = request.POST['cost_price']
        expiry_date = request.POST.get('expiry_date', None)
        status = request.POST['status']
        description = request.POST['description']
        image = request.FILES.get('image')

        
        try:
            category = Category.objects.get(id=category_id)
            product = Product.objects.create(
                name=name,
                sku=sku,
                category=category,
                quantity=quantity,
                reorder_level=reorder_level,
                cost_price=cost_price,
                expiry_date=expiry_date or None,
                status=status,
                description=description,
                image=image
            )
            
            suppliers_ids = request.POST.getlist('supplier')
            product.supplier.set(suppliers_ids)
        except Exception as e:
            messages.error(request, "SKU must be uniqe!", "alert-danger")
            return redirect('product:add_product_view')

        return redirect('product:inventory_view')

        


    return render(request, 'add_product.html', {'today_date': today, 'suppliers': suppliers, 'categories': categories})
=======
from django.shortcuts import render

# Create your views here.
>>>>>>> 93c65be4906da29330fd850b320161ef5417f727
