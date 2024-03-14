from django.db import models
from django.conf import settings
import uuid
from payment.helpers import generate_payment_code

class Merchant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    web = models.URLField()
    callback = models.URLField()
    status = models.BooleanField(default=False)
    api_key = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='merchants')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Merchant'
        verbose_name_plural = 'Merchants'

class PaymentMethod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    status = models.BooleanField(default=False)
    account_number = models.CharField(max_length=100)
    account_name = models.CharField(max_length=100)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'

class Transaction(models.Model):
    STATUS = (
        (0, 'Pending'),
        (1, 'Success'),
        (2, 'Failed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True)
    invoice_code = models.CharField(max_length=10, unique=True)
    status = models.PositiveIntegerField(choices=STATUS, default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='transactions')
    callback_url = models.URLField()
    return_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.code + ' - ' + self.merchant.name)

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'

class Pay(models.Model):
    STATUS = (
        (0, 'Pending'),
        (1, 'Success'),
        (2, 'Failed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='pays')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, null=True, related_name='pays')
    payment_code = models.CharField(max_length=10, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.PositiveIntegerField(choices=STATUS, default=0)
    expire_priod = models.IntegerField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    check_count = models.IntegerField(default=0)
    check_time = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.payment_code + ' - ' + self.transaction.code)

    class Meta:
        verbose_name = 'Pay'
        verbose_name_plural = 'Pays'
        ordering = ['-created_at']

class TransactionItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='items')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)
    
    class Meta:
        verbose_name = 'Transaction Item'
        verbose_name_plural = 'Transaction Items'

class CustomerDetails(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='customer')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.firstname)

    class Meta:
        verbose_name = 'Customer Details'
        verbose_name_plural = 'Customer Details'