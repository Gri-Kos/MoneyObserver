from decimal import Decimal
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Transaction, Savings, Plans, Table
from django.db.models import Sum, Avg, Max, Min
import matplotlib.pyplot as plt
import matplotlib
import io
import base64

@login_required(login_url='login')
def main_page(request):
    # Получаем все таблицы пользователя и сортируем их в убывающем порядке по дате создания
    tables = Table.objects.filter(user=request.user).order_by('-id')

    # Обработка создания новой таблицы и вывод сообщения
    if request.method == 'POST':
        new_table_name = request.POST.get('new_table_name')
        if new_table_name:
            Table.objects.create(user=request.user, name=new_table_name)
            messages.success(request, "Новая таблица успешно создана!")
            return redirect('main_page')

    # Сохраняем table в сессии – нужно дальше
    if 'table' in request.GET:
        request.session['table'] = request.GET['table']
        print(request.session.get('table'))

    return render(request, 'main_page.html', {'tables': tables})


#редактирование таблицы
@login_required(login_url='login')
def edit_table(request, table_id):
    table = get_object_or_404(Table, id=table_id, user=request.user)

    if request.method == 'POST':
        new_name = request.POST.get('new_table_name')
        table.name = new_name
        table.save()
        messages.success(request, "Название таблицы обновлено!")
        return redirect('main_page')

    return redirect('main_page')

#удаление таблицы
@login_required(login_url='login')
def delete_table(request, table_id):
    table = get_object_or_404(Table, id=table_id, user=request.user)

    # Удаляются и все транзакции, сбережения, планы, связанные с таблицей
    table.delete()
    messages.success(request, "Таблица и все связанные записи удалены!")
    return redirect('main_page')


#вывод сбережений
@login_required(login_url='login')
def savings_list(request):
    table = request.session.get('table')
    savings = Savings.objects.filter(user=request.user, table=table)

    savings_data = []
    #высчитываем текущий баланс на сбережении на основе транзакций
    for saving in savings:
        income_total = Transaction.objects.filter(
            user=request.user,
            table=table,
            saving=saving.name,
            transaction_type='Income'
        ).aggregate(Sum('price'))['price__sum'] or 0

        expense_total = Transaction.objects.filter(
            user=request.user,
            table=table,
            saving=saving.name,
            transaction_type='Expense'
        ).aggregate(Sum('price'))['price__sum'] or 0

        current_balance = income_total - expense_total + saving.sumStart
        dynamics = current_balance - saving.sumStart

        savings_data.append({
            'saving': saving,
            'current_balance': current_balance,
            'dynamics': dynamics,
        })

    return render(request, 'savings_list.html', {'savings_data': savings_data,
        'table': Table.objects.get(pk=table).name})


#создание нового сбережения
@login_required(login_url='login')
def add_saving(request):
    table = request.session.get('table')
    if request.method == 'POST':
        name = request.POST.get('name')
        sum_start = request.POST.get('sumStart', 0)

        if Savings.objects.filter(user=request.user, name=name, table=table).exists():
            messages.error(request, "Сбережение с таким именем уже существует.")
            return redirect('savings_list')
        table = Table.objects.get(pk=table)
        saving = Savings.objects.create(user=request.user, name=name, table=table, sumStart=sum_start, sumEnd=sum_start)
        messages.success(request, "Сбережение добавлено успешно!")
        return redirect('savings_list')

    return HttpResponse("Ошибка при добавлении сбережения.", status=400)


#редактирование сбережения, у сбережений должны быть уникальные имена
@login_required(login_url='login')
def edit_saving(request, id):
    table = request.session.get('table')
    saving = get_object_or_404(Savings, id=id, user=request.user, table=table)

    if request.method == 'POST':
        name = request.POST.get('name')
        sum_start = request.POST.get('sumStart', 0)

        if Savings.objects.filter(user=request.user, name=name, table=table).exclude(id=id).exists():
            messages.error(request, "Сбережение с таким именем уже существует.")
            return redirect('savings_list')

        saving.name = name
        saving.sumStart = sum_start
        saving.save()
        messages.success(request, "Сбережение успешно обновлено!")
        return redirect('savings_list')

    return render(request, 'savings_list.html', {'saving': saving})


# удаление сбережения
@login_required(login_url='login')
def delete_saving(request, id):
    table = request.session.get('table')
    saving = get_object_or_404(Savings, id=id, user=request.user, table=table)

    # удаляем все транзакции, связанные с данным сбережением
    Transaction.objects.filter(user=request.user, saving=saving.name, table=table).delete()

    saving.delete()
    return redirect('savings_list')


# вывод финансовых ожиданий
@login_required(login_url='login')
def plans(request):
    if 'table' in request.GET:
        request.session['table'] = request.GET['table']
    table = request.session.get('table')
    print(request.session.get('table'))
    income_plans = Plans.objects.filter(user=request.user, type='Income', table=table)
    expense_plans = Plans.objects.filter(user=request.user, type='Expense', table=table)

    # высчитываем получившиеся суммы в категориях
    for plan in income_plans:
        plan.reality_sum = Transaction.objects.filter(user=request.user, table=table, transaction_type='Income', type=plan.name).aggregate(Sum('price'))['price__sum'] or 0

    for plan in expense_plans:
        plan.reality_sum = Transaction.objects.filter(user=request.user, table=table, transaction_type='Expense', type=plan.name).aggregate(Sum('price'))['price__sum'] or 0

    return render(request, 'plans_list.html', {'income_plans': income_plans, 'expense_plans': expense_plans,
        'table': Table.objects.get(pk=table).name})

# добавление финансовых ожиданий
@login_required(login_url='login')
def add_plan(request):
    table = request.session.get('table')
    if request.method == 'POST':
        plan_type = request.POST.get('type')
        name = request.POST.get('name')
        expected_sum = request.POST.get('expected_sum')
        analytics = request.POST.get('analytics')
        table = Table.objects.get(pk = table)

        if Plans.objects.filter(user=request.user, table=table, name=name, type=plan_type).exists(): # план должен быть уникальным в рамках своего типа (расходы / доходы)
            messages.error(request, "План с таким названием уже существует.")
            return redirect('plans')

        Plans.objects.create(user=request.user, table=table, type=plan_type, name=name, expected_sum=expected_sum, analytics=analytics)
        messages.success(request, "План добавлен успешно!")
        return redirect('plans')

    return HttpResponse("Ошибка при добавлении плана.", status=400)


#редактирование планов
@login_required(login_url='login')
def edit_plan(request, id):
    table = request.session.get('table')
    plan = get_object_or_404(Plans, id=id, user=request.user, table=table)

    if request.method == 'POST':
        name = request.POST.get('name')
        expected_sum = request.POST.get('expected_sum')
        plan_type = request.POST.get('type')
        analytics = request.POST.get('analytics')

        # исключаем текущий редактируемый план из фильтрации
        if Plans.objects.filter(user=request.user, table=table, name=name, type=plan_type).exclude(id=plan.id).exists():
            messages.error(request, "План с таким названием уже существует.")
            return redirect('plans')
        else:
            plan.name = name
            plan.expected_sum = expected_sum
            plan.analytics = analytics
            plan.save()
            messages.success(request, "План обновлен!")
            return redirect('plans')

    return render(request, 'plans_list.html', {'plan': plan})


# удаление плана
@login_required(login_url='login')
def delete_plan(request, id):
    table = request.session.get('table')
    plan = get_object_or_404(Plans, id=id, user=request.user, table=table)

    # удаляем все транзакции с соответствующим типом
    Transaction.objects.filter(user=request.user, table=table, type=plan.name).delete()

    plan.delete()
    messages.success(request, "План удален!")
    return redirect('plans')


# вывод трат
@login_required
def expenses_list(request):
    table = request.session.get('table')

    transactions = Transaction.objects.filter(user=request.user, table=table, transaction_type="Expense")

    # получаем доступные варианты для полей "type" и "saving"
    plans = Plans.objects.filter(user=request.user, table=table, type="Expense")
    savings = Savings.objects.filter(user=request.user, table=table)

    return render(request, 'expenses.html', {
        'transactions': transactions,
        'plans': plans,
        'savings': savings,
        'table': Table.objects.get(pk=table).name
    })

# вывод доходов, аналогичен expenses_list
@login_required
def incomes_list(request):
    table = request.session.get('table')

    transactions = Transaction.objects.filter(user=request.user, table=table, transaction_type="Income")

    plans = Plans.objects.filter(user=request.user, table=table, type="Income")
    savings = Savings.objects.filter(user=request.user, table=table)

    return render(request, 'incomes.html', {
        'transactions': transactions,
        'plans': plans,
        'savings': savings,
        'table': Table.objects.get(pk=table).name
    })


#добавление транзакции
@login_required
def add_transaction(request, transaction_type):
    table = request.session.get('table')
    if request.method == "POST":
        table = Table.objects.get(pk=table)
        try:
            transaction = Transaction.objects.create(
                user=request.user,
                table=table,
                transaction_type=transaction_type,
                type=request.POST.get("type"),
                price=request.POST.get("price"),
                date=request.POST.get("date"),
                saving=request.POST.get("saving"),
                name=request.POST.get("name"),
                analytics=request.POST.get("analytics"),
            )
            messages.success(request, "Транзакция успешно добавлена.")
        except Exception as e:
            messages.error(request, f"Ошибка при добавлении транзакции: {e}")

    if request.method == "POST" and transaction_type == "Expense":
        return redirect('expenses_list')
    elif request.method == "POST" and transaction_type == "Income":
        return redirect('incomes_list')

    return HttpResponseForbidden("Неверный метод запроса.")


#редактирование транзакции
@login_required
def edit_transaction(request, transaction_id):
    table = request.session.get('table')
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user, table=table)

    if request.method == 'POST':
        transaction.name = request.POST['name']
        transaction.price = request.POST['price']
        transaction.date = request.POST['date']
        transaction.type = request.POST['type']
        transaction.saving = request.POST['saving']
        transaction.analytics = request.POST['analytics']
        try:
            transaction.full_clean()
            transaction.save()
            messages.success(request, "Транзакция успешно обновлена.")
        except ValidationError as e:
            messages.error(request, f"Ошибка при обновлении транзакции: {e}")
    if transaction.transaction_type == "Expense":
        return redirect('expenses_list')

    elif transaction.transaction_type == "Income":
        return redirect('incomes_list')


#даление транзакции
@login_required
def delete_transaction(request, transaction_id):
    table = request.session.get('table')
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user, table=table)

    transaction_type = transaction.transaction_type

    transaction.delete()

    messages.success(request, "Транзакция успешно удалена.")

    if transaction_type == "Expense":
        return redirect('expenses_list')

    elif transaction_type == "Income":
        return redirect('incomes_list')


#формируем круговые диаграммы
def generate_pie_chart(data, title):
    matplotlib.use('Agg')
    if not data:
        return None

    labels = [item.get("type", "Unknown") for item in data]
    sizes = [item.get("total", 0) for item in data]

    if not any(sizes):
        return None

    fig, ax = plt.subplots(figsize=(8, 8))

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=1.2
    )

    ax.legend(wedges, labels, title="Категории", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

    plt.setp(autotexts, size=10, weight="bold")
    ax.set_title(title, fontsize=14, weight="bold")

    buf = io.BytesIO()
    try:
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        encoded_image = base64.b64encode(buf.read()).decode('utf-8')
    finally:
        buf.close()
        plt.close(fig)

    return f"data:image/png;base64,{encoded_image}"


#вывод аналитики
@login_required
def analytics_view(request):
    table = request.session.get('table')
    income_data = Transaction.objects.filter(transaction_type="Income", analytics=True, table=table)
    expense_data = Transaction.objects.filter(transaction_type="Expense", analytics=True, table=table)
    plan_data = Plans.objects.filter(analytics=True, table=table)

    # анализ доходов
    income_analysis = {
        "max": income_data.aggregate(Max("price")),
        "min": income_data.aggregate(Min("price")),
        "avg": income_data.aggregate(Avg("price")),
    }

    # анализ расходов
    expense_analysis = {
        "max": expense_data.aggregate(Max("price")),
        "min": expense_data.aggregate(Min("price")),
        "avg": expense_data.aggregate(Avg("price")),
    }

    # анализ ожиданий
    expected_income = plan_data.filter(type="Income").aggregate(Sum("expected_sum"))
    expected_expense = plan_data.filter(type="Expense").aggregate(Sum("expected_sum"))
    reality_income = income_data.aggregate(Sum("price"))
    reality_expense = expense_data.aggregate(Sum("price"))

    # обработка None значений
    expected_income_sum = expected_income["expected_sum__sum"] or Decimal('0')
    expected_expense_sum = expected_expense["expected_sum__sum"] or Decimal('0')
    reality_income_sum = reality_income["price__sum"] or Decimal('0')
    reality_expense_sum = reality_expense["price__sum"] or Decimal('0')

    expectation_analysis = {
        "expected_income": expected_income,
        "expected_expense": expected_expense,
        "expected_diff": expected_income_sum - expected_expense_sum,
        "reality_diff": reality_income_sum - reality_expense_sum,
    }

    # диаграммы
    income_pie = generate_pie_chart(
        list(income_data.values("type").annotate(total=Sum("price")).order_by()),
        "Соотношение доходов",
    )
    expense_pie = generate_pie_chart(
        list(expense_data.values("type").annotate(total=Sum("price")).order_by()),
        "Соотношение расходов",
    )

    context = {
        "income_analysis": income_analysis,
        "expense_analysis": expense_analysis,
        "expectation_analysis": expectation_analysis,
        "reality_income": reality_income_sum,
        "reality_expense": reality_expense_sum,
        "income_pie": income_pie,
        "expense_pie": expense_pie,
        'table': Table.objects.get(pk=table).name,
    }
    return render(request, "analytics.html", context)


#вход в аккаунт
def login_page(request):
    if request.method == "POST":
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
            user_obj = User.objects.filter(username=username).first()
            if not user_obj:
                messages.error(request, "Пользователь не найден")
                return redirect('/login/')
            user_auth = authenticate(username=username, password=password)
            if user_auth:
                login(request, user_auth)
                return redirect('main_page')
            messages.error(request, "Неверный пароль")
            return redirect('/login/')
        except Exception as e:
            messages.error(request, "Что-то пошло не так")
            return redirect('/register/')
    return render(request, "login.html")


#регистрация
def register_page(request):
    if request.method == "POST":
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
            user_obj = User.objects.filter(username=username)
            if user_obj.exists():
                messages.error(request, "Ник занят")
                return redirect('/register/')
            user_obj = User.objects.create(username=username)
            user_obj.set_password(password)
            user_obj.save()
            messages.success(request, "Аккаунт создан")
            return redirect('login')
        except Exception as e:
            messages.error(request, "Что-то пошло не так")
            return redirect('/register')
    return render(request, "register.html")


#выход
def custom_logout(request):
    logout(request)
    return redirect('login')