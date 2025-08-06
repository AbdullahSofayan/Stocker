from django.shortcuts import render, redirect
from django.http import HttpRequest

# Create your views here.

def Home_view(request: HttpRequest):

    return render(request, "main/dashboard.html")

