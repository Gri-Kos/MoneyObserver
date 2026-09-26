from django.contrib import admin
from django.urls import path
from home import views

urlpatterns = [
    #вход, выход, регистрация, администрирование
    path('', views.login_page, name='login'),
    path('login', views.login_page, name='login'),
    path('logout/', views.custom_logout, name="logout"),
    path('register/', views.register_page, name='register'),
    path('admin/', admin.site.urls),

    #отображение таблиц, их редактирование(добавление), удаление
    path('main_page/', views.main_page, name='main_page'),
    path('edit_table/<int:table_id>/', views.edit_table, name='edit_table'),
    path('delete_table/<int:table_id>/', views.delete_table, name='delete_table'),

    #отображение сбережений, их добавление, редактирование, удаление
    path('savings/', views.savings_list, name='savings_list'),
    path('savings/add/', views.add_saving, name='add_saving'),
    path('savings/edit/<int:id>/', views.edit_saving, name='edit_saving'),
    path('savings/delete/<int:id>/', views.delete_saving, name='delete_saving'),

    #отображение планов, их добавление, редактирование, удаление
    path('plans/', views.plans, name='plans'),
    path('plans/add/', views.add_plan, name='add_plan'),
    path('plans/edit/<int:id>/', views.edit_plan, name='edit_plan'),
    path('plans/delete/<int:id>/', views.delete_plan, name='delete_plan'),

    #отображение трат, доходов, их добавление, редактирование, удаление
    path('expenses/', views.expenses_list, name='expenses_list'),
    path('incomes/', views.incomes_list, name='incomes_list'),
    path('transactions/add/<str:transaction_type>/', views.add_transaction, name='add_transaction'),
    path('transactions/edit/<int:transaction_id>/', views.edit_transaction, name='edit_transaction'),
    path('transactions/delete/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),

    #аналитика
    path('analytics/', views.analytics_view, name='analytics'),
]
