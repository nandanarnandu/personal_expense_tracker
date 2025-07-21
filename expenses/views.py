from django.shortcuts import render

# This view will handle the home page.
def home(request):
    return render(request, 'expenses/home.html')