from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

# Create your views here.


def sign_up_view(request):

    if request.method == 'POST':
        try:
            new_user = User.objects.create_user(username=request.POST["username"],password=request.POST["password"], email=request.POST["email"], first_name = request.POST["first_name"])
            new_user.save()
            messages.success(request, "Registered User Successfuly", "alert-success")
            return redirect("accounts:login_view")
        except Exception as e:
            print(e)

    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, "Logged in successfully", "alert-success")
            return redirect('main:dashboard_view')
        messages.error(request, "Please try again. Your credentials are wrong", "alert-danger")
    return render(request, "login.html")


def logout_view(request):

    logout(request)
    messages.success(request, "logged out successfully", "alert-warning")
    
    return redirect("accounts:login_view")