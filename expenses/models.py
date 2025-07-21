from django.db import models
from django.contrib.auth.models import User # We need to use Django's built-in User model

# This is our blueprint for an Expense entry.
# It will create a table in our database.
class Expense(models.Model):
    # The 'owner' field links each expense to a specific user.
    # This is super important so each person only sees their own expenses!
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE)

    # A title or description for the expense.
    title = models.CharField(max_length=255)

    # The amount of money spent. We use DecimalField for accurate money values.
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # The category of the expense (like 'Food', 'Bills', etc.).
    category = models.CharField(max_length=255)

    # The date the expense occurred.
    date = models.DateField(auto_now_add=True) # auto_now_add makes it use the current date automatically

    # This special method makes the expense easier to read in the admin panel.
    def __str__(self):
        return self.title