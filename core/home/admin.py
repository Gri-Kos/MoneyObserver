from django.contrib import admin
from .models import Table, Transaction, Savings, Plans


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):

    list_display = ("id", "user", "name") # Отображаемые поля

    list_display_links = ("id", "name") # Поля-ссылки на редактирование

    list_filter = ("user",) # По чему можем фильтровать

    search_fields = ("name", "user__username") # Поля для поиска

    list_per_page = 20 # Количество отображаемых записей на листе

    fields = ("user", "name") # Поля, которые можем редактировать


#остальной код устроен аналогичным образом
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):

    list_display = ("id", "user", "table", "transaction_type", "type", "price", "saving", "date", "name", "analytics")

    list_display_links = ("id", "name")

    list_filter = ("transaction_type", "date", "user", "saving", "table", "analytics")

    search_fields = ("name", "user__username", "transaction_type", "type", "saving", "table__name")

    readonly_fields = ("date",) # Поля только для чтения

    list_per_page = 20

    fields = ("user", "table", "transaction_type", "type", "price", "saving", "name", "date", "analytics")


@admin.register(Savings)
class SavingsAdmin(admin.ModelAdmin):

    list_display = ("id", "user", "table", "name", "sumStart", "sumEnd")

    list_display_links = ("id", "name")

    list_filter = ("user", "table")

    search_fields = ("name", "user__username", "table__name")

    list_per_page = 20

    fields = ("user", "table", "name", "sumStart", "sumEnd")


@admin.register(Plans)
class PlansAdmin(admin.ModelAdmin):

    list_display = ("id", "user", "table", "type", "name", "expected_sum", "analytics")

    list_display_links = ("id", "name")

    list_filter = ("type", "user", "table", "analytics")

    search_fields = ("name", "user__username", "type", "table__name")

    list_per_page = 20

    fields = ("user", "table", "type", "name", "expected_sum", "analytics")
