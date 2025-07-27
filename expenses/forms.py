from django import forms
from .models import Expense, Goal

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ('title', 'amount', 'category')


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['name', 'target_amount', 'current_amount', 'due_date', 'completed']
