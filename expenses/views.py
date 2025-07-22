from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm # This is needed for CustomUserCreationForm to inherit from it
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import forms # This is needed for forms.ModelForm and forms.EmailField
from .models import Expense
from django.db.models import Q, Sum
from datetime import datetime, date
import json
from django.db import connections

# --- Start of the ExpenseForm code (remains the same) ---
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ('title', 'amount', 'category')
# --- End of the ExpenseForm code ---

# --- Start of CustomUserCreationForm code (NEWLY ADDED / MODIFIED) ---
class CustomUserCreationForm(UserCreationForm):
    # Add the email field here
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')

    class Meta(UserCreationForm.Meta):
        # Include 'email' along with the default fields
        fields = UserCreationForm.Meta.fields + ('email',)
# --- End of CustomUserCreationForm code ---

def home(request):
    return render(request, 'expense/home.html')

def register(request):
    if request.method == 'POST':
        # Use our custom form here
        form = CustomUserCreationForm(request.POST) # CHANGED: Using CustomUserCreationForm
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('home')
    else:
        # Use our custom form here as well
        form = CustomUserCreationForm() # CHANGED: Using CustomUserCreationForm
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
    category_data = [float(item['total']) for item in category_summary]

    # Data for Monthly Spending Bar Chart
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
        'total_spent': total_spent,
        'category_labels': category_labels_json,
        'category_data': category_data_json,
        'monthly_labels': monthly_labels_json,
        'monthly_data': monthly_data_json,
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