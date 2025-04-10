from django.urls import path
from .views import home, expense_list, add_expense, delete_expense, delete_department, reset_budget, reset_expenses, homepage, debt_optimizer, monthly_expenses,delete_expense,update_expense
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', homepage, name='homepage'), 
    path('home/', home, name='home'),  # Home page (Budget Optimization)
    path('expenses/', expense_list, name='expense_list'),  # Expense List
    path('expenses/add/', add_expense, name='add_expense'),  # Add Expense
    path('expenses/delete/<int:expense_id>/', delete_expense, name='delete_expense'),  # Delete Expense
    path('delete-department/<str:department_name>/', delete_department, name='delete_department'),  # Delete Department
    path('reset-budget/', reset_budget, name='reset_budget'),
    path('expenses/reset/', reset_expenses, name='reset_expenses'),  # Added reset URL
    path('debt-optimizer/', debt_optimizer, name='debt_optimizer'),
    path("monthly-expenses/", monthly_expenses, name="monthly_expenses"),
    path("delete-expense/<int:id>/", delete_expense, name="delete_expense"),
    path('monthly-expenses/', monthly_expenses, name='monthly_expenses'),
    path('expenses/delete/<int:id>/', delete_expense, name='delete_expense'),
    path('expenses/update/<int:id>/', update_expense, name='update_expense'),



]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
