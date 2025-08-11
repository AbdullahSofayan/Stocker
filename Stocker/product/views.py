import json
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from .models import Product, Supplier, Category
from datetime import date
from django.contrib import messages
from django.db.models import Count, Sum, F, Case, When, IntegerField, DecimalField, Q
import csv, io
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth.models import User
# Create your views here.

@login_required
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
        n = len(selected_suppliers) # Number of suppliers the user picked.

        products = (
            products.annotate(
                total_suppliers=Count('supplier', distinct=True),matched_suppliers=Count('supplier',filter=Q(supplier__id__in=selected_suppliers),distinct=True),
            ).filter(matched_suppliers=n).filter(total_suppliers=n)
        )

    if status:
        products = products.filter(stock_status=status)

   
    paginator = Paginator(products, 12) 
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # keep all current query params except 'page'
    params = request.GET.copy()
    params.pop('page', None)
    base_qs = params.urlencode()



    return render(request, 'products/inventory.html', {'base_qs': base_qs, 'today_date': today, 'products': page_obj, 'page_obj': page_obj, 'categories': categories,
     'suppliers': suppliers, "stock_status_choices": Product.STOCK_STATUS_CHOICES, 'selected_suppliers': selected_suppliers})


@login_required
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
from django.urls import reverse


@login_required
def edit_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    page = request.GET.get("page", 1) 

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



        if product.quantity == '0':
            product.stock_status = "out_of_stock"
        elif int(product.quantity) < int(product.reorder_level):
            product.stock_status = "almost_done"
        else:
            product.stock_status = "in_stock"


        

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

        # Send alert if low stock
        if product.stock_status in ["almost_done", "out_of_stock"]:
            send_low_stock_alert(product)

        return redirect(f"{reverse('product:inventory_view')}?page={page}") # Redirect to the same page.

@login_required
def delete_product_view(request: HttpRequest, product_id):

    if not ( request.user.is_staff and request.user.has_perm('product.delete_product')) :
        messages.error(request, "You do not have permission to delete products.", "alert-danger")
        return redirect('product:inventory_view')
    
    product = get_object_or_404(Product, id=product_id)
    page = request.GET.get("page", 1) 

    product.delete()
    messages.success(request, "Product deleted successfully.", "alert-success")


    return redirect(f"{reverse('product:inventory_view')}?page={page}") # Redirect to the same page.

@login_required
def details_product_view(request: HttpRequest, product_id):
    product = get_object_or_404(Product, id=product_id)

    return render(request, 'products/product_details.html', {'product': product} )

@login_required
def categories_view(request: HttpRequest):
    categories = Category.objects.all()

    paginator = Paginator(categories, 12) 
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # keep all current query params except 'page'
    params = request.GET.copy()
    params.pop('page', None)
    base_qs = params.urlencode()


    return render(request, 'categories/categories_page.html', {'base_qs': base_qs,'categories': page_obj, 'page_obj': page_obj})


@login_required
def edit_category_view(request: HttpRequest, category_id):

    if not ( request.user.is_staff and request.user.has_perm('product.edit_category')) :
        messages.error(request, "You do not have permission to edit category.", "alert-danger")
        return redirect('product:categories_view')
    
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


@login_required
def delete_category_view(request: HttpRequest, category_id):

    if not ( request.user.is_staff and request.user.has_perm('product.delete_category')) :
        messages.error(request, "You do not have permission to delete category.", "alert-danger")
        return redirect('product:categories_view')
    
    category = get_object_or_404(Category, id = category_id)

    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted.", "alert-success")
        
    return redirect('product:categories_view')


@login_required
def add_category_view(request: HttpRequest):

    if not ( request.user.is_staff and request.user.has_perm('product.add_category')) :
        messages.error(request, "You do not have permission to add category.", "alert-danger")
        return redirect('product:categories_view')
    

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


@login_required
def suppliers_view(request:HttpRequest):

    suppliers = Supplier.objects.all()
    q = (request.GET.get('q') or '').strip()

    if q:
        suppliers = suppliers.filter(Q(name__icontains=q))

    paginator = Paginator(suppliers, 12) 
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # keep all current query params except 'page'
    params = request.GET.copy()
    params.pop('page', None)
    base_qs = params.urlencode()
        
    return render(request, "suppliers/suppliers_page.html", {'base_qs': base_qs, 'suppliers':page_obj, 'page_obj':page_obj})



@login_required
def add_supplier_view(request: HttpRequest):

    if not ( request.user.is_staff and request.user.has_perm('product.add_supplier')) :
        messages.error(request, "You do not have permission to add supplier.", "alert-danger")
        return redirect('product:suppliers_view')
    
    if request.method == 'POST':
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        website = request.POST.get("website")
        image = request.FILES.get("image")

        try:
            Supplier.objects.create (
                name = name,
                phone = phone,
                email = email,
                website = website,
                image=image
            )
            messages.success(request, "Supplier added successfully.", "alert-success")

        except Exception as e :
            messages.error(request, "Supplier couldn't created", "alert-danger")

    return redirect("product:suppliers_view")


@login_required
def delete_supplier_view(request: HttpRequest, supplier_id):

    if not ( request.user.is_staff and request.user.has_perm('product.delete_supplier')) :
        messages.error(request, "You do not have permission to delete supplier.", "alert-danger")
        return redirect('product:suppliers_view')
    
    supplier = get_object_or_404(Supplier, id = supplier_id)

    if request.method == "POST":
        supplier.delete()
        messages.success(request, "Supplier deleted.", "alert-success")
        
    return redirect('product:suppliers_view')



@login_required
def edit_supplier_view(request: HttpRequest, supplier_id):

    if not ( request.user.is_staff and request.user.has_perm('product.edit_supplier')) :
        messages.error(request, "You do not have permission to edit supplier.", "alert-danger")
        return redirect('product:suppliers_view')

    supplier = get_object_or_404(Supplier, id = supplier_id)

    if request.method == "POST":
        try:
            supplier.name = request.POST.get('name', supplier.name)
            supplier.phone = request.POST.get('phone', '')
            supplier.email = request.POST.get('email', '')
            supplier.website = request.POST.get('website', '')
            image_file = request.FILES.get('image')
            if image_file:
                supplier.image = image_file
            supplier.save()
            messages.success(request, "Supplier updated.", "alert-success")
        except Exception as e:
            messages.error(request, "Supplier Couldn't updated.", "alert-danger")

    return redirect('product:suppliers_view')


@login_required
def supplier_details_view(request, supplier_id):
    
    supplier = get_object_or_404(Supplier, id = supplier_id)
    products_by_supplier = Product.objects.filter(supplier = supplier)

    return render(request, "suppliers/supplier_details.html", {'supplier': supplier, 'products_by_supplier': products_by_supplier})


def _sanitize_csv(text: str) -> str:
    """
    Prevent CSV injection when opening in Excel by prefixing risky values.
    """
    if text and text[0] in ("=", "+", "-", "@"):
        return "'" + text
    return text



@login_required
def export_products_csv(request):
    qs = Product.objects.all()

    timestamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    filename = f"products-{timestamp}.csv"

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    # Write BOM so Excel opens UTF-8 correctly (helps with Arabic)
    response.write("\ufeff")

    writer = csv.writer(response)
    writer.writerow([
        "ID",
        "Name",
        "SKU",
        "Category",
        "Suppliers",
        "Cost Price",
        "Quantity",
        "Reorder Level",
        "Stock Status",
        "Expiry Date",
        "Description",
        "Image URL",
        "Created",
        "Updated",
    ])

    for p in qs.select_related("category").prefetch_related("supplier"):
        suppliers = ", ".join(s.name for s in p.supplier.all())
        expiry = p.expiry_date.strftime("%Y-%m-%d") if p.expiry_date else ""
        img_url = p.image.url if (p.image and p.image.name) else ""

        writer.writerow([
            p.id,
            _sanitize_csv(p.name or ""),
            _sanitize_csv(p.sku or ""),
            p.category.name if p.category_id else "",
            suppliers,
            str(p.cost_price or ""),
            p.quantity,
            p.reorder_level,
            p.stock_status,
            expiry,
            (p.description or "").replace("\r\n", " ").replace("\n", " "),
            img_url,
            p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
            p.updated_at.strftime("%Y-%m-%d %H:%M") if p.updated_at else "",
        ])

    return response


@login_required
def import_products_csv(request):
    if request.method == "POST" and request.FILES.get("csv_file"):
        csv_file = request.FILES["csv_file"]

        if not csv_file.name.endswith(".csv"):
            messages.error(request, "Please upload a CSV file.")
            return redirect("product:inventory_view")

        # Decode and read CSV
        try:
            data_set = csv_file.read().decode("utf-8-sig")  # handles BOM
        except UnicodeDecodeError:
            messages.error(request, "Invalid file encoding. Please use UTF-8.")
            return redirect("product:inventory_view")

        io_string = io.StringIO(data_set)
        reader = csv.DictReader(io_string)

        imported_count = 0
        for row in reader:
            sku = row.get("SKU", "").strip()
            if not sku:
                continue

            category_name = row.get("Category", "").strip()
            category_obj = None
            if category_name:
                category_obj, _ = Category.objects.get_or_create(name=category_name)

            product, created = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": row.get("Name", "").strip(),
                    "category": category_obj,
                    "description": row.get("Description", "").strip(),
                    "quantity": int(row.get("Quantity", 0) or 0),
                    "reorder_level": int(row.get("Reorder Level", 0) or 0),
                    "cost_price": row.get("Cost Price", 0) or 0,
                    "stock_status": row.get("Stock Status", "in_stock"),
                },
            )

            supplier_names = row.get("Suppliers", "")
            if supplier_names:
                supplier_list = []
                for s_name in supplier_names.split(","):
                    s_name = s_name.strip()
                    if s_name:
                        supplier_obj, _ = Supplier.objects.get_or_create(name=s_name)
                        supplier_list.append(supplier_obj)
                product.supplier.set(supplier_list)

            imported_count += 1

        messages.success(request, f"Imported {imported_count} products successfully!", "alert-success")
        return redirect("product:inventory_view")

    messages.error(request, "No file uploaded.")
    return redirect("product:inventory_view")



def _sanitize_csv(text: str) -> str:
    if text and str(text)[0] in ("=", "+", "-", "@"):
        return "'" + str(text)
    return str(text)

def _ts_filename(prefix: str, ext="csv"):
    return f'{prefix}-{timezone.now().strftime("%Y%m%d-%H%M%S")}.{ext}'

@login_required
def inventory_report_csv(request):
    # Optional: respect same filters as inventory page
    qs = Product.objects.select_related("category").prefetch_related("supplier").all()

    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q))

    category_id = request.GET.get("category")
    if category_id:
        qs = qs.filter(category_id=category_id)

    selected_suppliers = request.GET.getlist("supplier")
    if selected_suppliers:
        n = len(selected_suppliers)
        qs = (
            qs.annotate(
                total_suppliers=Count('supplier', distinct=True),
                matched_suppliers=Count('supplier', filter=Q(supplier__id__in=selected_suppliers), distinct=True),
            )
            .filter(matched_suppliers=n)
            .filter(total_suppliers=n)
        )

    status = request.GET.get("status")
    if status:
        qs = qs.filter(stock_status=status)

    # KPI aggregates
    totals = qs.aggregate(
        total_products=Count("id"),
        total_qty=Sum("quantity"),
        total_value=Sum(F("quantity") * F("cost_price"), output_field=DecimalField()),
        in_stock=Count(Case(When(stock_status="in_stock", then=1), output_field=IntegerField())),
        almost_done=Count(Case(When(stock_status="almost_done", then=1), output_field=IntegerField())),
        out_of_stock=Count(Case(When(stock_status="out_of_stock", then=1), output_field=IntegerField())),
    )

    # Per-category breakdown
    by_category = (
        qs.values("category__name")
          .annotate(
              products=Count("id"),
              qty=Sum("quantity"),
              value=Sum(F("quantity") * F("cost_price"), output_field=DecimalField()),
          )
          .order_by("category__name")
    )

    # CSV response
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{_ts_filename("inventory-report")}"'
    resp.write("\ufeff")
    w = csv.writer(resp)

    # Header: KPIs section
    w.writerow(["Inventory Report"])
    w.writerow(["Generated At", timezone.now().strftime("%Y-%m-%d %H:%M")])
    w.writerow([])
    w.writerow(["KPI", "Value"])
    w.writerow(["Total Products", totals["total_products"] or 0])
    w.writerow(["Total Quantity", totals["total_qty"] or 0])
    w.writerow(["Total Inventory Value", totals["total_value"] or 0])
    w.writerow(["In Stock", totals["in_stock"] or 0])
    w.writerow(["Almost Done", totals["almost_done"] or 0])
    w.writerow(["Out of Stock", totals["out_of_stock"] or 0])

    # Category breakdown
    w.writerow([])
    w.writerow(["By Category"])
    w.writerow(["Category", "Products", "Total Qty", "Total Value"])
    for row in by_category:
        w.writerow([
            row["category__name"] or "—",
            row["products"] or 0,
            row["qty"] or 0,
            row["value"] or 0,
        ])

    # Detailed lines (optional but handy)
    w.writerow([])
    w.writerow(["Detailed Products"])
    w.writerow(["ID","Name","SKU","Category","Suppliers","Cost Price","Qty","Reorder","Status","Expiry Date","Description"])
    for p in qs:
        suppliers = ", ".join(s.name for s in p.supplier.all())
        expiry = p.expiry_date.strftime("%Y-%m-%d") if p.expiry_date else ""
        w.writerow([
            p.id,
            _sanitize_csv(p.name or ""),
            _sanitize_csv(p.sku or ""),
            p.category.name if p.category_id else "",
            suppliers,
            str(p.cost_price or 0),
            p.quantity,
            p.reorder_level,
            p.stock_status,
            expiry,
            (p.description or "").replace("\r\n", " ").replace("\n", " "),
        ])

    return resp

@login_required
def supplier_report_view(request):
    # Filter the same way you already do
    qs = Product.objects.all()

    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q))

    category_id = request.GET.get("category")
    if category_id:
        qs = qs.filter(category_id=category_id)

    status = request.GET.get("status")
    if status:
        qs = qs.filter(stock_status=status)

    suppliers_qs = (
        Supplier.objects.annotate(
            product_count=Count("products", filter=Q(products__in=qs), distinct=True),
            total_qty=Sum("products__quantity", filter=Q(products__in=qs)),
            total_value=Sum(
                F("products__quantity") * F("products__cost_price"),
                filter=Q(products__in=qs),
                output_field=DecimalField()
            ),
            low_stock=Count(
                Case(When(products__stock_status="almost_done", then=1), output_field=IntegerField()),
                filter=Q(products__in=qs),
            ),
            out_stock=Count(
                Case(When(products__stock_status="out_of_stock", then=1), output_field=IntegerField()),
                filter=Q(products__in=qs),
            ),
        )
        .filter(product_count__gt=0)
        .order_by("-total_value", "name")
    )

    labels = [s.name for s in suppliers_qs]
    values_value = [float(s.total_value or 0) for s in suppliers_qs]
    values_qty = [int(s.total_qty or 0) for s in suppliers_qs]

    total_value_sum = float(sum(values_value)) or 1.0
    total_qty_sum = int(sum(values_qty)) or 1

    percents_value = [round((v / total_value_sum) * 100, 2) for v in values_value]
    percents_qty = [round((q / total_qty_sum) * 100, 2) for q in values_qty]

    # Build a detailed table (list of dicts) for the template
    suppliers_table = []
    for idx, s in enumerate(suppliers_qs):
        tv = float(s.total_value or 0)
        tq = int(s.total_qty or 0)
        avg_unit_cost = round(tv / tq, 2) if tq else 0.0
        suppliers_table.append({
            "name": s.name,
            "product_count": s.product_count or 0,
            "total_qty": tq,
            "total_value": round(tv, 2),
            "percent_value": percents_value[idx],
            "percent_qty": percents_qty[idx],
            "low_stock": s.low_stock or 0,
            "out_stock": s.out_stock or 0,
            "avg_unit_cost": avg_unit_cost,
        })

    context = {
        "labels_json": json.dumps(labels),
        "values_value_json": json.dumps(values_value),
        "values_qty_json": json.dumps(values_qty),
        "percents_value_json": json.dumps(percents_value),
        "percents_qty_json": json.dumps(percents_qty),
        "total_value_sum": total_value_sum,
        "total_qty_sum": total_qty_sum,
        "suppliers_table": suppliers_table,                 # <-- new
        "querystring": request.GET.urlencode(),
    }
    return render(request, "suppliers/suppliers_charts.html", context)

@login_required
def supplier_report_csv(request):
    qs = Product.objects.all()

    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q))
    category_id = request.GET.get("category")
    if category_id:
        qs = qs.filter(category_id=category_id)
    status = request.GET.get("status")
    if status:
        qs = qs.filter(stock_status=status)

    suppliers_qs = (
        Supplier.objects.annotate(
            product_count=Count("products", filter=Q(products__in=qs), distinct=True),
            total_qty=Sum("products__quantity", filter=Q(products__in=qs)),
            total_value=Sum(
                F("products__quantity") * F("products__cost_price"),
                filter=Q(products__in=qs),
                output_field=DecimalField()
            ),
            low_stock=Count(
                Case(When(products__stock_status="almost_done", then=1), output_field=IntegerField()),
                filter=Q(products__in=qs),
            ),
            out_stock=Count(
                Case(When(products__stock_status="out_of_stock", then=1), output_field=IntegerField()),
                filter=Q(products__in=qs),
            ),
        )
        .filter(product_count__gt=0)
        .order_by("-total_value", "name")
    )

    # Totals for percentage calculation
    totals = suppliers_qs.aggregate(
        sum_value=Sum("total_value"),
        sum_qty=Sum("total_qty"),
    )
    sum_value = float(totals["sum_value"] or 0.0)
    sum_qty = int(totals["sum_qty"] or 0)

    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{_ts_filename("supplier-report")}"'
    resp.write("\ufeff")
    w = csv.writer(resp)

    w.writerow(["Supplier Report"])
    w.writerow(["Generated At", timezone.now().strftime("%Y-%m-%d %H:%M")])
    w.writerow([])
    w.writerow(["Supplier","Products","Total Qty","Total Value","% of Value","% of Qty","Low Stock","Out of Stock","Avg Unit Cost"])

    for s in suppliers_qs:
        tv = float(s.total_value or 0.0)
        tq = int(s.total_qty or 0)
        pct_val = round((tv / (sum_value or 1.0)) * 100, 2) if sum_value else 0.0
        pct_qty = round((tq / (sum_qty or 1)) * 100, 2) if sum_qty else 0.0
        avg_unit_cost = round(tv / tq, 2) if tq else 0.0

        w.writerow([
            s.name,
            s.product_count or 0,
            tq,
            round(tv, 2),
            pct_val,
            pct_qty,
            s.low_stock or 0,
            s.out_stock or 0,
            avg_unit_cost,
        ])

    return resp




def send_low_stock_alert(product):
    admin_emails = list(User.objects.filter(is_superuser=True).values_list('email', flat=True))

    subject = f"Low Stock Alert - {product.name}"
    html_message = render_to_string("low_stock_alert.html", {"products": [product]})

    # Send to admin email (set in .env)
    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=settings.EMAIL_HOST_USER,
        to=admin_emails
    )
    email.content_subtype = "html"
    email.send(fail_silently=False)



