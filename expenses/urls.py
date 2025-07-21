from django.urls import path
from . import views # The '.' means 'from the current folder'

urlpatterns = [
    path('', views.home, name='home'),
]