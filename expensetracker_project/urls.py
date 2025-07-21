from django.contrib import admin
from django.urls import path, include # Add 'include' here

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('expenses.urls')), # This tells the main project to look inside our 'expenses' app for more URLs!
]