from django.urls import path
from django.contrib.auth import views as auth_views # Import Django's built-in views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='expenses/login.html'), name='login'), # The login page
    path('logout/', auth_views.LogoutView.as_view(template_name='expenses/home.html'), name='logout'), # The logout page
    path('dashboard/', views.dashboard, name='dashboard'), # Our new dashboard page
]