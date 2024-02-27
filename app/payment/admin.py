from django.contrib import admin
from payment.models import Merchant, PaymentMethod, Transaction, TransactionItem, CustomerDetails
from payment.helpers import generate_api_key, generate_merchant_code, cek_web_status

class MerchantAdmin(admin.ModelAdmin):
    exclude = ('code', 'api_key', 'status')

    def save_model(self, request, obj, form, change):
        obj.code = generate_merchant_code()
        obj.api_key = generate_api_key()
        obj.status = cek_web_status(obj.web)
        print(obj)
        obj.save()

    

admin.site.register(Merchant, MerchantAdmin)
admin.site.register(PaymentMethod)
admin.site.register(Transaction)
admin.site.register(TransactionItem)
admin.site.register(CustomerDetails)
