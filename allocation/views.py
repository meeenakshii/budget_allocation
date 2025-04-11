from django.shortcuts import render, redirect, get_object_or_404
import numpy as np
from scipy.optimize import linprog
from .models import Expense
from .forms import ExpenseForm

def homepage(request):
    return render(request, 'allocation/homepage.html')

def optimize_budget(budget, departments, min_funding, max_funding):
    """Optimizes budget allocation while ensuring feasibility."""
    n = len(departments)
    
    if n == 0:
        return "Error: No departments provided."

    if sum(min_funding) > budget:
        return "Error: Budget is too low to meet minimum funding requirements."

    if sum(max_funding) < budget:
        return "Error: Budget is too high compared to max funding limits."

    c = np.zeros(n)  # Objective function (we just need a feasible solution)

    A_ub = np.vstack([np.eye(n), -np.eye(n)])
    b_ub = np.hstack([max_funding, -np.array(min_funding)])

    A_eq = np.ones((1, n))
    b_eq = [budget]

    result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, method="highs")

    if result.success:
        allocation = result.x.round(2).tolist()
        return [(departments[i], allocation[i]) for i in range(len(departments))]
    else:
        return "No feasible solution found."



from django.shortcuts import render, redirect
from scipy.optimize import linprog
import numpy as np

def home(request):
    optimized_allocation = request.session.get("optimized_allocation", None)
    budget = request.session.get("budget", None)
    departments = request.session.get("departments", [])
    min_funding = request.session.get("min_funding", [])
    max_funding = request.session.get("max_funding", [])

    if request.method == "POST":
        if "clear_budget" in request.POST:
            request.session.flush()
            return redirect("home")

        try:
            # Get new total budget input
            new_budget = float(request.POST.get("total_budget", 0))
            budget = new_budget  # Overwrite each time for simplicity

            # Retrieve form data
            new_departments = request.POST.getlist("departments[]")
            new_min_funding = request.POST.getlist("min_funding[]")
            new_max_funding = request.POST.getlist("max_funding[]")

            departments = []
            min_funding = []
            max_funding = []

            for dept, min_fund, max_fund in zip(new_departments, new_min_funding, new_max_funding):
                min_fund = float(min_fund)
                max_fund = float(max_fund)

                if min_fund > max_fund:
                    optimized_allocation = f"❌ Error: Min funding cannot be greater than max funding for {dept}."
                    return render(request, "allocation/home.html", {"optimized_allocation": optimized_allocation})

                departments.append(dept)
                min_funding.append(min_fund)
                max_funding.append(max_fund)

            request.session["departments"] = departments
            request.session["min_funding"] = min_funding
            request.session["max_funding"] = max_funding
            request.session["budget"] = budget

            n = len(departments)
            if n < 2:
                return render(request, "allocation/home.html", {
                    "optimized_allocation": "Please enter at least two departments/crops.",
                })

            total_min = sum(min_funding)
            total_max = sum(max_funding)

            if budget < total_min:
                return render(request, "allocation/home.html", {
                    "optimized_allocation": "🚫 Budget too low to satisfy minimum needs of all.",
                })

            # Objective: Distribute as evenly as possible (or zero vector since cost doesn't matter)
            c = np.zeros(n)

            # Inequality constraints for max and min bounds
            A_ub = np.vstack([np.eye(n), -np.eye(n)])
            b_ub = np.hstack([max_funding, -np.array(min_funding)])

            # Equality constraint only if total budget <= sum of max (force full usage of water/budget)
            A_eq = None
            b_eq = None
            if budget <= total_max:
                A_eq = np.ones((1, n))
                b_eq = [budget]
            else:
                # No equality constraint; allocate only as much as needed
                pass

            result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, method="highs")

            if result.success:
                allocation = result.x
                optimized_allocation = {
                    dept: round(val, 2) for dept, val in zip(departments, allocation)
                }
                request.session["optimized_allocation"] = optimized_allocation
            else:
                optimized_allocation = "❌ No feasible allocation. Adjust funding ranges or budget."

        except Exception as e:
            optimized_allocation = f"⚠️ Error: {str(e)}"

    return render(request, "allocation/home.html", {
        "optimized_allocation": optimized_allocation,
        "budget": budget,
        "departments": departments
    })



def delete_department(request, department_name):
    """Deletes a department from the session and re-optimizes the budget."""
    departments = request.session.get("departments", [])
    min_funding = request.session.get("min_funding", [])
    max_funding = request.session.get("max_funding", [])

    if department_name in departments:
        index = departments.index(department_name)
        departments.pop(index)
        min_funding.pop(index)
        max_funding.pop(index)

        request.session["departments"] = departments
        request.session["min_funding"] = min_funding
        request.session["max_funding"] = max_funding
        request.session["optimized_allocation"] = optimize_budget(
            request.session.get("budget", 0),
            departments,
            min_funding,
            max_funding
            )


    return redirect("home")

def expense_list(request):
    """Displays all recorded expenses and compares them with the budget."""
    expenses = Expense.objects.all()
    total_expenses = sum(expense.amount for expense in expenses)
    budget = request.session.get("budget", 0)

    return render(request, 'allocation/expense_list.html', {
        'expenses': expenses,
        'total_expenses': total_expenses,
        'budget': budget
    })


def add_expense(request):
    """Handles adding new expenses to the tracker."""
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('expense_list')  # ✅ fixed redirect
    else:
        form = ExpenseForm()
    return render(request, 'allocation/add_expense.html', {'form': form})


def delete_expense(request, expense_id):
    """Deletes an expense entry."""
    expense = get_object_or_404(Expense, id=expense_id)
    expense.delete()
    return redirect('expense_list')

def reset_budget(request):
    """ Clears all budget-related session data """
    request.session.flush()  # <-- Make sure no extra arguments are passed
    return redirect("home")



def reset_expenses(request):
    """Only clears expense data but keeps budget & allocations."""
    Expense.objects.all().delete()
    return redirect("expense_list")



from django.shortcuts import render
from scipy.optimize import linprog
import numpy as np
import math

def debt_optimizer(request):
    result = None
    error = None

    if request.method == 'POST':
        try:
            budget = float(request.POST.get('budget'))
            raw_debts = request.POST['debts'].split('\n')

            principals = []
            interest_rates = []
            min_payments = []

            for line in raw_debts:
                if not line.strip():
                    continue
                parts = line.strip().split(',')
                if len(parts) != 2:
                    continue
                principal, rate = map(float, parts)
                principals.append(principal)
                interest_rates.append(rate)
                # Calculate min payment dynamically
                min_payments.append(max(0.02 * principal, 100))  # 2% or ₹100

            if not principals:
                raise ValueError("No valid debt data provided.")

            # Objective: Minimize total interest this month
            c = interest_rates

            # Constraint: sum(payments) <= budget
            A = [np.ones(len(principals))]
            b = [budget]

            # Bounds: payment_i >= min_payment_i and <= principal
            bounds = [(min_payments[i], principals[i]) for i in range(len(principals))]

            res = linprog(c=c, A_ub=A, b_ub=b, bounds=bounds, method='highs')

            if res.success:
                payments = res.x.tolist()
                months = [
                    math.ceil(principals[i] / payments[i]) if payments[i] > 0 else float('inf')
                    for i in range(len(principals))
                ]
                result = list(zip(principals, interest_rates, min_payments, payments, months))
            else:
                error = "Optimization failed. Please try different inputs."

        except Exception as e:
            error = str(e)

    return render(request, 'allocation/debt_optimizer.html', {
        'result': result,
        'error': error,
        'expenses': request.session.get('expenses', [])
    })



from django.shortcuts import render, redirect, get_object_or_404
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from .models import Expense

# View to show/add expenses
def monthly_expenses(request):
    expenses = Expense.objects.all().order_by('-date')

    if request.method == "POST":
        try:
            date_str = request.POST.get("date")
            category = request.POST.get("category")
            amount = Decimal(request.POST.get("amount"))
            note = request.POST.get("note", "")

            # Validate and convert date
            date = datetime.strptime(date_str, "%Y-%m-%d").date()

            Expense.objects.create(
                date=date,
                category=category,
                amount=amount,
                description=note
            )
            return redirect("monthly_expenses")

        except Exception as e:
            # If error, pass existing data with error message
            total_spent = sum(exp.amount for exp in expenses)
            category_breakdown = defaultdict(Decimal)
            for exp in expenses:
                category_breakdown[exp.category] += exp.amount

            return render(request, "allocation/monthly_expenses.html", {
                "expenses": expenses,
                "total_spent": total_spent,
                "category_breakdown": dict(category_breakdown),
                "error": f"Error: {str(e)}"
            })

    # Monthly summary
    total_spent = sum(exp.amount for exp in expenses)
    category_breakdown = defaultdict(Decimal)
    for exp in expenses:
        category_breakdown[exp.category] += exp.amount

    return render(request, "allocation/monthly_expenses.html", {
        "expenses": expenses,
        "total_spent": total_spent,
        "category_breakdown": dict(category_breakdown),
    })

def delete_monthly_expense(request, expense_id):
    expense = Expense.objects.get(id=expense_id)
    expense.delete()
    return redirect('monthly_expenses')


# View to update an expense
def update_expense(request, id):
    expense = get_object_or_404(Expense, id=id)

    if request.method == "POST":
        try:
            expense.category = request.POST.get("category")
            expense.amount = Decimal(request.POST.get("amount"))
            expense.description = request.POST.get("note", "")
            expense.date = datetime.strptime(request.POST.get("date"), "%Y-%m-%d").date()
            expense.save()
            return redirect("monthly_expenses")
        except Exception as e:
            return render(request, "allocation/update_expense.html", {"expense": expense, "error": f"Error: {str(e)}"})

    return render(request, "allocation/update_expense.html", {"expense": expense})

