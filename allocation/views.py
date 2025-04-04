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
import numpy as np
from scipy.optimize import linprog

def home(request):
    optimized_allocation = request.session.get("optimized_allocation", None)
    budget = request.session.get("budget", None)
    departments = request.session.get("departments", [])
    min_funding = request.session.get("min_funding", [])
    max_funding = request.session.get("max_funding", [])

    if request.method == "POST":
        if "clear_budget" in request.POST:  # Reset everything
            request.session.flush()
            return redirect("home")

        try:
            # Get Total Budget
            new_budget = float(request.POST.get("total_budget", 0))
            if budget is not None:
                budget += new_budget
            else:
                budget = new_budget

            # Retrieve department details
            new_departments = request.POST.getlist("departments[]")
            new_min_funding = request.POST.getlist("min_funding[]")
            new_max_funding = request.POST.getlist("max_funding[]")

            # Convert values to float and store them
            for dept, min_fund, max_fund in zip(new_departments, new_min_funding, new_max_funding):
                min_fund = float(min_fund)
                max_fund = float(max_fund)

                if min_fund > max_fund:
                    optimized_allocation = f"Error: Min funding cannot be greater than max funding for {dept}."
                    return render(request, "allocation/home.html", {"optimized_allocation": optimized_allocation})

                departments.append(dept)
                min_funding.append(min_fund)
                max_funding.append(max_fund)

            request.session["departments"] = departments
            request.session["min_funding"] = min_funding
            request.session["max_funding"] = max_funding

            # Ensure at least one department exists
            n = len(departments)
            if n == 0:
                optimized_allocation = "Error: No departments provided."
            else:
                total_min_funding = sum(min_funding)
                
                if budget < total_min_funding:
                    optimized_allocation = "Error: Budget is too low to satisfy the minimum funding requirements."
                    return render(request, "allocation/home.html", {"optimized_allocation": optimized_allocation})

                # **Optimization using Linear Programming**
                c = np.zeros(n)  # Minimize cost (equal distribution)
                A_ub = np.vstack([np.eye(n), -np.eye(n)])  # Constraints for min/max funding
                b_ub = np.hstack([max_funding, -np.array(min_funding)])  # Bounds
                A_eq = np.ones((1, n))  # Total budget constraint
                b_eq = [budget]

                # Solve using Linear Programming
                result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, method="highs")

                if result.success:
                    allocation = result.x
                    optimized_allocation = optimize_budget(budget, departments, min_funding, max_funding)

                    request.session["optimized_allocation"] = optimized_allocation
                    request.session["budget"] = budget
                else:
                    optimized_allocation = "No feasible solution found. Try adjusting your budget or funding constraints."

        except Exception as e:
            optimized_allocation = f"Error: {str(e)}"
        print("DEBUG optimized_allocation:", optimized_allocation)


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
            return redirect('expense_list')
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

