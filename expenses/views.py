from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import forms
from .models import Expense
from django.db.models import Q, Sum
from datetime import datetime, date
import json
from django.db import connections

# The ExpenseForm class
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ('title', 'amount', 'category')

# The CustomUserCreationForm class
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email',)

def home(request):
    return render(request, 'expense/home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'expense/register.html', {'form': form})

@login_required
def dashboard(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.owner = request.user
            expense.save()
            messages.success(request, 'Expense added successfully!')
            return redirect('dashboard')
    else:
        form = ExpenseForm()

    expenses = Expense.objects.filter(owner=request.user)

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str:
        try:
            start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            expenses = expenses.filter(date__gte=start_date_obj)
        except ValueError:
            messages.error(request, "Invalid start date format. Please use YYYY-MM-DD.")

    if end_date_str:
        try:
            end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            expenses = expenses.filter(date__lte=end_date_obj)
        except ValueError:
            messages.error(request, "Invalid end date format. Please use YYYY-MM-DD.")

    expenses = expenses.order_by('-date')

    total_spent = expenses.aggregate(Sum('amount'))['amount__sum'] or 0.0
    category_summary = expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
    category_labels = [item['category'] for item in category_summary]
    category_data = [float(item['total']) for item in category_summary]
    monthly_summary = expenses.extra(select={'month': "strftime('%%Y-%%m', date)"}).values('month').annotate(total=Sum('amount')).order_by('month')
    monthly_labels = [item['month'] for item in monthly_summary]
    monthly_data = [float(item['total']) for item in monthly_summary]

    context = {
        'form': form,
        'expenses': expenses,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'total_spent': total_spent,
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_data': json.dumps(monthly_data),
    }
    return render(request, 'expense/dashboard.html', context)

@login_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, pk=expense_id)
    if expense.owner != request.user:
        messages.error(request, "You are not authorized to edit this expense.")
        return redirect('dashboard')
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('dashboard')
    else:
        form = ExpenseForm(instance=expense)
    context = {
        'form': form,
        'expense': expense,
    }
    return render(request, 'expense/edit_expense.html', context)

@login_required
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, pk=expense_id)
    if expense.owner != request.user:
        messages.error(request, "You are not authorized to delete this expense.")
        return redirect('dashboard')
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('dashboard')
    messages.info(request, "Confirm deletion?")
    return render(request, 'expense/confirm_delete.html', {'expense': expense})