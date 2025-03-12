from django.db import models
from decimal import Decimal

class Customer(models.Model):
    name = models.CharField(max_length=100)
    uid = models.CharField(max_length=100, unique=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"{self.name} ({self.uid})"

class Payment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    fare = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    new_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    date = models.CharField(max_length=10)  # بصيغة dd/mm/yyyy
    time = models.CharField(max_length=8)   # بصيغة HH:mm:ss

    def __str__(self):
        return f"Payment for {self.customer.uid} on {self.date} {self.time}"
