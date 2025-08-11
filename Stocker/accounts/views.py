from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.shortcuts import render, redirect
from django.utils import timezone
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.db.models import F
from product.models import Product


User = get_user_model()


def sign_up_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        password = request.POST.get("password", "")

        # Basic validation
        if not username or not email or not password:
            messages.error(request, "All fields are required.", "alert-danger")
            return redirect("accounts:sign_up_view")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.", "alert-danger")
            return redirect("accounts:sign_up_view")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already in use.", "alert-danger")
            return redirect("accounts:sign_up_view")

        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
        )
        messages.success(request, "Registered successfully. Please log in.", "alert-success")
        return redirect("accounts:login_view")

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully", "alert-success")

            # Trigger on superuser login
            if user.is_superuser:
                try:
                    send_expiry_date_alert()
                    send_low_stock_alert()
                except Exception as e:
                    print("send_expiry_date_alert failed:", e)

            # Respect ?next=...
            next_url = request.GET.get("next")
            return redirect(next_url or "main:dashboard_view")

        messages.error(request, "Username or password is wrong", "alert-danger")

    return render(request, "login.html")


def send_expiry_date_alert():
    admin_emails = list(
        User.objects.filter(is_superuser=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )

    # Fallback so send doesn't explode if no admin has email set
    if not admin_emails:
        fallback = getattr(settings, "EMAIL_HOST_USER", None)
        if fallback:
            admin_emails = [fallback]
        else:
            return 

    today = timezone.localdate()
    soon = today + timedelta(days=30)

    expiring_qs = (
        Product.objects.filter(expiry_date__range=(today, soon))
        .select_related("category")
        .order_by("expiry_date")
    )

    if not expiring_qs.exists():
        return

    subject = f"Expiry Date Alert — {expiring_qs.count()} product(s) expiring soon"
    html_message = render_to_string(
        "expiry_alert.html",
        {"products": expiring_qs, "today": today, "soon": soon}
    )

    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=settings.EMAIL_HOST_USER,
        to=admin_emails,
    )
    email.content_subtype = "html"
    email.send(fail_silently=False)

def send_low_stock_alert():
    admin_emails = list(
        User.objects.filter(is_superuser=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )

    low_stock = (
        Product.objects
        .filter(quantity__lte=F('reorder_level'))
        .order_by('quantity')[:10]
    )
    print(low_stock)

    if not low_stock.exists():
        return
    
    subject = f"Low Stock Alert — {low_stock.count()} product(s)"
    html_message = render_to_string(
        "low_stock_alert.html", 
        {"products": low_stock}
    )

    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=settings.EMAIL_HOST_USER,
        to=admin_emails,
    )
    email.content_subtype = "html"
    email.send(fail_silently=False)


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully", "alert-warning")
    return redirect("accounts:login_view")
