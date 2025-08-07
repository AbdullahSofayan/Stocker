from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render, redirect
from .models import Product, Supplier, Category
from datetime import date
from django.contrib import messages
# Create your views here.

def inventory_view(request: HttpRequest):
    products = Product.objects.all()
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    today = date.today().isoformat()
    return render(request, 'inventory.html', {'today_date': today, 'products': products, 'categories': categories, 'suppliers': suppliers})

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


def edit_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == "POST":

        sku = request.POST.get('sku')
        if Product.objects.filter(sku=sku).exclude(id=product.id).exists():
            messages.error(request, "SKU must be uniqe!", "alert-danger")
            return redirect('product:inventory_view')

        product.name = request.POST.get("name")
        product.quantity = request.POST.get("quantity")
        product.reorder_level = request.POST.get("reorder_level")          

       

        product.cost_price= request.POST.get("cost_price")
        product.quantity= request.POST.get("quantity")
        expiry_date = request.POST.get("expiry_date")
        if expiry_date:
            product.expiry_date = expiry_date
        else:
            product.expiry_date = None

        product.stock_status= request.POST.get("stock_status")
        product.description= request.POST.get("description")

        image_file = request.FILES.get("image")
        if image_file:
            product.image = image_file

        category_id = request.POST.get("category")
        if category_id:
            product.category = get_object_or_404(Category, id=category_id)

        image_file = request.FILES.get("image")
        if image_file:
            product.image = image_file 

        product.save()

        supplier_ids = request.POST.getlist("supplier")
        product.supplier.set(supplier_ids)

        
        return redirect("product:inventory_view")  

    
def delete_product_view(request: HttpRequest, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('product:inventory_view')


def details_product_view(request: HttpRequest, product_id):
    product = get_object_or_404(Product, id=product_id)

    return render(request, 'product_details.html', {'product': product} )