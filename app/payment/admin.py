from django.contrib import admin
from payment.models import Merchant, PaymentMethod, Transaction, TransactionItem, CustomerDetails, Pay
from payment.helpers import generate_api_key, generate_merchant_code, cek_web_status

class MerchantAdmin(admin.ModelAdmin):
    exclude = ('code', 'api_key', 'status')
    list_display = ('code', 'name', 'web', 'callback', 'status', 'api_key', 'user', 'created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        obj.code = generate_merchant_code()
        while Merchant.objects.filter(code=obj.code).exists():
            obj.code = generate_merchant_code()
        obj.api_key = generate_api_key()
        obj.status = cek_web_status(obj.web)
        print(obj)
        obj.save()

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('code', 'invoice_code', 'status', 'amount', 'paid', 'merchant', 'created_at', 'updated_at')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'payment_method', 'payment_code', 'amount', 'paid', 'status', 'created_at', 'updated_at')

class CustomerDetailsAdmin(admin.ModelAdmin):
    list_display = ('firstname', 'lastname', 'email', 'phone', 'postal_code', 'transaction', 'created_at', 'updated_at')

class TransactionItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'quantity', 'transaction', 'created_at', 'updated_at')

class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'status', 'account_number', 'account_name', 'merchant', 'created_at', 'updated_at')

admin.site.register(Merchant, MerchantAdmin)
admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(TransactionItem, TransactionItemAdmin)
admin.site.register(CustomerDetails, CustomerDetailsAdmin)
admin.site.register(Pay, PaymentAdmin)
