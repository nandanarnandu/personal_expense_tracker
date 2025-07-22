from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import forms
from .models import Expense
from django.db.models import Q, Sum # Add Sum
from datetime import datetime, date
import json # Add this import
from django.db import connections # Add this for potential database date functions if needed, though not strictly for this current implementation

# --- Start of the ExpenseForm code (remains the same) ---
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ('title', 'amount', 'category')
# --- End of the ExpenseForm code ---

# --- Your existing view functions (home, register, delete_expense) remain the same ---

def home(request):
    return render(request, 'expense/home.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'expense/register.html', {'form': form})

@login_required
def dashboard(request):
    # Handle adding new expense
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

    start_date_obj = None
    end_date_obj = None

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

    # --- Start of NEW ANALYTICS / DATA SCIENCE logic ---
    total_spent = expenses.aggregate(Sum('amount'))['amount__sum'] or 0.0

    # Data for Category Distribution Pie Chart
    category_summary = expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
    category_labels = [item['category'] for item in category_summary]
    category_data = [float(item['total']) for item in category_summary] # Convert Decimal to float for JSON

    # Data for Monthly Spending Bar Chart
    # Use database functions to group by month and year.
    # This part can be tricky across different databases (SQLite vs PostgreSQL etc.)
    # For SQLite (default Django), we can extract year and month
    monthly_summary = expenses.extra(select={'month': "strftime('%%Y-%%m', date)"}).values('month').annotate(total=Sum('amount')).order_by('month')

    monthly_labels = [item['month'] for item in monthly_summary]
    monthly_data = [float(item['total']) for item in monthly_summary]

    # Convert data to JSON strings for JavaScript
    category_labels_json = json.dumps(category_labels)
    category_data_json = json.dumps(category_data)
    monthly_labels_json = json.dumps(monthly_labels)
    monthly_data_json = json.dumps(monthly_data)
    # --- End of NEW ANALYTICS / DATA SCIENCE logic ---


    context = {
        'form': form,
        'expenses': expenses,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'total_spent': total_spent, # New
        'category_labels': category_labels_json, # New
        'category_data': category_data_json, # New
        'monthly_labels': monthly_labels_json, # New
        'monthly_data': monthly_data_json, # New
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