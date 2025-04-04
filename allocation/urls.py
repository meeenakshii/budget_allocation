from django.urls import path
from .views import home, expense_list, add_expense, delete_expense, delete_department, reset_budget, reset_expenses, homepage

urlpatterns = [
    path('', homepage, name='homepage'), 
    path('home/', home, name='home'),  # Home page (Budget Optimization)
    path('expenses/', expense_list, name='expense_list'),  # Expense List
    path('expenses/add/', add_expense, name='add_expense'),  # Add Expense
    path('expenses/delete/<int:expense_id>/', delete_expense, name='delete_expense'),  # Delete Expense
    path('delete-department/<str:department_name>/', delete_department, name='delete_department'),  # Delete Department
    path('reset-budget/', reset_budget, name='reset_budget'),
    path('expenses/reset/', reset_expenses, name='reset_expenses'),  # Added reset URL

]
