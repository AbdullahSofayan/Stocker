from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render, redirect
from .models import Product, Supplier, Category
from datetime import date
from django.contrib import messages
from django.db.models import Q
# Create your views here.

def inventory_view(request: HttpRequest):
    products = Product.objects.all()
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    today = date.today().isoformat()

    q = (request.GET.get('q') or '').strip()
    cat_id    = request.GET.get("category", "")
    selected_suppliers = request.GET.getlist("supplier")
    status    = request.GET.get("status", "")

    if q:
        products = products.filter(Q(name__icontains=q) |Q(sku__icontains=q))

    if cat_id:
        products = products.filter(category_id = cat_id)



    if selected_suppliers:
        products = products.filter(supplier__id__in=selected_suppliers).distinct()

    if status:
        products = products.filter(stock_status=status)




    return render(request, 'products/inventory.html', {'today_date': today, 'products': products, 'categories': categories, 'suppliers': suppliers, "stock_status_choices": Product.STOCK_STATUS_CHOICES, 'selected_suppliers': selected_suppliers})

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
        stock_status = request.POST['stock_status']
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
                stock_status=stock_status,
                description=description,
                image=image
            )
            messages.success(request, "Product added successfully.", "alert-success")

            suppliers_ids = request.POST.getlist('supplier')
            product.supplier.set(suppliers_ids)
        except Exception as e:
            print(e)
            messages.error(request, "SKU must be uniqe!", "alert-danger")
            return redirect('product:add_product_view')

        return redirect('product:inventory_view')

        


    return render(request, 'products/add_product.html', {'today_date': today, 'suppliers': suppliers, 'categories': categories})


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

    return render(request, 'products/product_details.html', {'product': product} )


def categories_view(request: HttpRequest):
    categories = Category.objects.all()
    return render(request, 'categories/categories_page.html', {'categories': categories})



def edit_category_view(request: HttpRequest, category_id):

    category = get_object_or_404(Category, id = category_id)

    if request.method == "POST":
        try:
            category.name = request.POST.get('name', category.name)
            category.description = request.POST.get('description', '')
            image_file = request.FILES.get('image')
            if image_file:
                category.image = image_file
            category.save()
            messages.success(request, "Category updated.", "alert-success")
        except Exception as e:
            messages.error(request, "Category Couldn't updated.", "alert-danger")

    return redirect('product:categories_view')


def delete_category_view(request: HttpRequest, category_id):
    category = get_object_or_404(Category, id = category_id)

    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted.", "alert-success")
        
    return redirect('product:categories_view')


def add_category_view(request: HttpRequest):

    if request.method == 'POST':
        name = request.POST.get("name")
        description = request.POST.get("description")
        image = request.FILES.get("image")
        try:
            Category.objects.create (
                name = name,
                description = description,
                image = image
            )
            messages.success(request, "Category added successfully.", "alert-success")

        except Exception as e :
            messages.error(request, "Category couldn't created", "alert-danger")

    return redirect("product:categories_view")


def suppliers_view(request:HttpRequest):
    suppliers = Supplier.objects.all()
    return render(request, "suppliers/suppliers_page.html", {'suppliers':suppliers})



def add_supplier_view(request: HttpRequest):

    if request.method == 'POST':
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        image = request.FILES.get("image")

        try:
            Supplier.objects.create (
                name = name,
                phone = phone,
                image=image
            )
            messages.success(request, "Supplier added successfully.", "alert-success")

        except Exception as e :
            messages.error(request, "Supplier couldn't created", "alert-danger")

    return redirect("product:suppliers_view")


def delete_supplier_view(request: HttpRequest, supplier_id):
    supplier = get_object_or_404(Supplier, id = supplier_id)

    if request.method == "POST":
        supplier.delete()
        messages.success(request, "Supplier deleted.", "alert-success")
        
    return redirect('product:suppliers_view')



def edit_supplier_view(request: HttpRequest, supplier_id):

    supplier = get_object_or_404(Supplier, id = supplier_id)

    if request.method == "POST":
        try:
            supplier.name = request.POST.get('name', supplier.name)
            supplier.phone = request.POST.get('phone', '')
            image_file = request.FILES.get('image')
            if image_file:
                supplier.image = image_file
            supplier.save()
            messages.success(request, "Supplier updated.", "alert-success")
        except Exception as e:
            messages.error(request, "Supplier Couldn't updated.", "alert-danger")

    return redirect('product:suppliers_view')