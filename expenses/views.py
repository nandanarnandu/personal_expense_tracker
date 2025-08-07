# expenses/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import forms
from .models import Expense, Income, Goal
from django.db.models import Q, Sum
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import pandas as pd # NEW
from sklearn.linear_model import LinearRegression # NEW

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ('title', 'amount', 'category')

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ('title', 'amount', 'category')

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ('name', 'target_amount', 'current_amount', 'due_date', 'completed')
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

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

# NEW: AI/ML function to predict spending
def predict_monthly_spending(user):
    all_expenses = Expense.objects.filter(owner=user).order_by('date')
    if not all_expenses:
        return None, "Not enough data to predict."

    # Convert to DataFrame
    df = pd.DataFrame(list(all_expenses.values('date', 'amount')))
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')

    # Group by month and sum amounts
    monthly_spending = df.groupby('month')['amount'].sum()

    # We need at least two months of data to create a trend
    if len(monthly_spending) < 2:
        return None, "Not enough historical data to predict spending."

    # Prepare data for the linear regression model
    X = pd.to_datetime(monthly_spending.index.to_timestamp()).astype('int64').values.reshape(-1, 1)
    y = monthly_spending.values

    # Train the model
    model = LinearRegression()
    model.fit(X, y)

    # Predict for the next month
    last_month_timestamp = pd.to_datetime(monthly_spending.index[-1].to_timestamp()).value
    next_month_timestamp = pd.to_datetime(monthly_spending.index[-1].to_timestamp() + pd.DateOffset(months=1)).value

    predicted_spending = model.predict([[next_month_timestamp]])[0]

    # Round the prediction to 2 decimal places
    predicted_spending = round(predicted_spending, 2)

    return predicted_spending, None

@login_required
def dashboard(request):
    if request.method == 'POST':
        if 'add_expense' in request.POST:
            expense_form = ExpenseForm(request.POST)
            if expense_form.is_valid():
                expense = expense_form.save(commit=False)
                expense.owner = request.user
                expense.save()
                messages.success(request, 'Expense added successfully!')
                return redirect('dashboard')
        elif 'add_income' in request.POST:
            income_form = IncomeForm(request.POST)
            if income_form.is_valid():
                income = income_form.save(commit=False)
                income.owner = request.user
                income.save()
                messages.success(request, 'Income added successfully!')
                return redirect('dashboard')
        elif 'add_goal' in request.POST:
            goal_form = GoalForm(request.POST)
            if goal_form.is_valid():
                goal = goal_form.save(commit=False)
                goal.owner = request.user
                goal.save()
                messages.success(request, 'Goal added successfully!')
                return redirect('dashboard')
    else:
        expense_form = ExpenseForm()
        income_form = IncomeForm()
        goal_form = GoalForm()

    expenses = Expense.objects.filter(owner=request.user)
    incomes = Income.objects.filter(owner=request.user)

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str:
        try:
            start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            expenses = expenses.filter(date__gte=start_date_obj)
            incomes = incomes.filter(date__gte=start_date_obj)
        except ValueError:
            messages.error(request, "Invalid start date format. Please use YYYY-MM-DD.")

    if end_date_str:
        try:
            end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            expenses = expenses.filter(date__lte=end_date_obj)
            incomes = incomes.filter(date__lte=end_date_obj)
        except ValueError:
            messages.error(request, "Invalid end date format. Please use YYYY-MM-DD.")

    today = date.today()
    today_expenses = Expense.objects.filter(owner=request.user, date=today)
    today_incomes = Income.objects.filter(owner=request.user, date=today)

    expenses = expenses.order_by('-date')
    incomes = incomes.order_by('-date')

    # NEW: Predict next month's spending
    predicted_spending_amount, prediction_error = predict_monthly_spending(request.user)

    total_spent = expenses.aggregate(Sum('amount'))['amount__sum']
    total_income = incomes.aggregate(Sum('amount'))['amount__sum']

    total_spent = total_spent if total_spent is not None else Decimal(0)
    total_income = total_income if total_income is not None else Decimal(0)
    balance = total_income - total_spent

    category_summary = expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
    category_labels = [item['category'] for item in category_summary]
    category_data = [float(item['total']) for item in category_summary]
    monthly_summary = expenses.extra(select={'month': "strftime('%%Y-%%m', date)"}).values('month').annotate(total=Sum('amount')).order_by('month')
    monthly_labels = [item['month'] for item in monthly_summary]
    monthly_data = [float(item['total']) for item in monthly_summary]

    goals = Goal.objects.filter(owner=request.user).order_by('due_date')

    context = {
        'expense_form': expense_form,
        'income_form': income_form,
        'goal_form': goal_form,
        'expenses': expenses,
        'incomes': incomes,
        'goals': goals,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'total_spent': total_spent,
        'total_income': total_income,
        'balance': balance,
        'today_expenses': today_expenses,
        'today_incomes': today_incomes,
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_data': json.dumps(monthly_data),
        'current_month_year': today.strftime('%B %Y'),
        'predicted_spending': predicted_spending_amount, # NEW
        'prediction_error': prediction_error, # NEW
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

@login_required
def edit_goal(request, goal_id):
    goal = get_object_or_404(Goal, pk=goal_id)
    if goal.owner != request.user:
        messages.error(request, "You are not authorized to edit this goal.")
        return redirect('dashboard')
    if request.method == 'POST':
        form = GoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Goal updated successfully!')
            return redirect('dashboard')
    else:
        form = GoalForm(instance=goal)
    context = {
        'form': form,
        'goal': goal,
    }
    return render(request, 'expense/edit_goal.html', context)

@login_required
def delete_goal(request, goal_id):
    goal = get_object_or_404(Goal, pk=goal_id)
    if goal.owner != request.user:
        messages.error(request, "You are not authorized to delete this goal.")
        return redirect('dashboard')
    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Goal deleted successfully!')
        return redirect('dashboard')
    messages.info(request, "Confirm deletion?")
    return render(request, 'expense/confirm_delete_goal.html', {'goal': goal})