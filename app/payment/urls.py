from django.urls import path, include
from payment.views import TransactionCreateView, PaymentView, CheckPaymentView, ConfirmPayment

app_name = 'payment'

urlpatterns = [
    path('create-transaction/', TransactionCreateView.as_view(), name='create_transaction'),
    path('pay/', PaymentView.as_view(), name='pay'),
    path('check/', CheckPaymentView.as_view(), name='check'),
    path('confirm-payment/', ConfirmPayment.as_view(), name='confirm'),
]