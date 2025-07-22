from django.urls import path
from django.contrib.auth import views as auth_views # Import Django's built-in views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='expense/login.html'), name='login'), # CHANGE THIS LINE
    path('logout/', auth_views.LogoutView.as_view(template_name='expenses/home.html'), name='logout'), # The logout page
    path('dashboard/', views.dashboard, name='dashboard'), # Our new dashboard page
    path('dashboard/edit/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('dashboard/delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='expense/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='expense/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='expense/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='expense/password_reset_complete.html'), name='password_reset_complete'),
]