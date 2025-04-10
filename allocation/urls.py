from django.urls import path
from .views import (
    home, homepage, expense_list, add_expense, delete_expense,
    delete_department, reset_budget, reset_expenses, debt_optimizer,
    monthly_expenses, update_expense, delete_monthly_expense
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', homepage, name='homepage'),
    path('home/', home, name='home'),

    # Expense tracker
    path('expenses/', expense_list, name='expense_list'),
    path('expenses/add/', add_expense, name='add_expense'),
    path('expenses/delete/<int:expense_id>/', delete_expense, name='delete_expense'),
    path('expenses/update/<int:id>/', update_expense, name='update_expense'),

    # Monthly expenses
    path('monthly-expenses/', monthly_expenses, name='monthly_expenses'),
    path('monthly-expenses/delete/<int:expense_id>/', delete_monthly_expense, name='delete_monthly_expense'),

    # Other
    path('delete-department/<str:department_name>/', delete_department, name='delete_department'),
    path('reset-budget/', reset_budget, name='reset_budget'),
    path('expenses/reset/', reset_expenses, name='reset_expenses'),
    path('debt-optimizer/', debt_optimizer, name='debt_optimizer'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
