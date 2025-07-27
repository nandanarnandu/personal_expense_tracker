# expenses/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='expense/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='expense/home.html'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/edit/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('dashboard/delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),

    # Password reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='expense/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='expense/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='expense/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='expense/password_reset_complete.html'), name='password_reset_complete'),
    path('edit-goal/<int:goal_id>/', views.edit_goal, name='edit_goal'),
    path('delete-goal/<int:goal_id>/', views.delete_goal, name='delete_goal'),
]