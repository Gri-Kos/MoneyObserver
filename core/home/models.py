from django.db import models
from django.contrib.auth.models import User
from datetime import datetime


class Table(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    possible_types = [
        ("Income", "Income"),
        ("Expense", "Expense"),
    ]
    transaction_type = models.CharField(max_length=10, choices=possible_types) #трата или доход
    type = models.CharField(max_length=255, default='')  #может быть только одним из существующих имен в Plans
    price = models.DecimalField(max_digits=14, decimal_places=4)
    date = models.DateField(default=datetime.now)
    saving = models.CharField(max_length=255) #может быть только одним из существующих имен в Savings
    name = models.CharField(max_length=255, default='')
    analytics = models.BooleanField(default=True) #использовать ли при анализе

    class Meta:
        ordering = ["-date"]


class Savings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    sumStart = models.DecimalField(max_digits=14, decimal_places=4)
    sumEnd = models.DecimalField(max_digits=14, decimal_places=4)


class Plans(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    possible_types = [
        ("Income", "Доход"),
        ("Expense", "Трата"),
    ]
    type = models.CharField(max_length=10, choices=possible_types, default="Income") #трата или доход
    name = models.CharField(max_length=255)
    expected_sum = models.DecimalField(max_digits=14, decimal_places=4)
    analytics = models.BooleanField(default=True) #использовать ли при анализе