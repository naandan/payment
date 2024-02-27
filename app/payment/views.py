from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from payment.serializer import TransactionSerializer
from payment.models import Transaction, Merchant, CustomerDetails, TransactionItem, PaymentMethod
from django.views.generic import View
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound
from django.template.loader import render_to_string
from payment.helpers import *
import math
from django_htmx.http import HttpResponseClientRefresh, HttpResponseClientRedirect

class TransactionCreateView(APIView):
    def save_transaction(self, data):
        merchant = Merchant.objects.filter(code=data['merchantCode']).first()
        if merchant is None:
            return Response({'message': 'Merchant not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        transaction = Transaction.objects.filter(invoice_code=data['invoiceCode']).first()
        if transaction is not None:
            if check_expired(transaction.expired_at):
                if transaction.status != 1:
                    transaction.status = 2
                    transaction.save()
                return {'message': 'Transaction expired', 'status': 'expired'}
            return {'transaction': transaction, 'status': 'exists'}

        data = {
            'amount': data['paymentAmount'],
            'invoice_code': data['invoiceCode'],
            'merchant': merchant,
            'callback_url': data['callback_url'],
            'expire_priod': data['expire_priod'],
            'expired_at': get_expired_at(data['expire_priod']),
        }
        
        data['code'] = generate_transaction_code()
        transaction = Transaction.objects.create(**data)
        return {'transaction': transaction, 'status': 'created'}

    def save_customer_details(self, data, transaction):
        customer_data = data.get('customerDetails')
        customer_data['transaction'] = transaction
        return CustomerDetails.objects.create(**customer_data)
    
    def save_items(self, data, transaction):
        items_data = data.get('itemsDetails')
        for item in items_data:
            item['transaction'] = transaction
            TransactionItem.objects.create(**item)
        return True

    def post(self, request, format=None):
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            transaction = self.save_transaction(request.data)
            if transaction['status'] == 'expired':
                return Response(transaction, status=status.HTTP_400_BAD_REQUEST)
            if transaction['status'] == 'exists':
                transaction = {
                    'transactionCode': transaction['transaction'].code,
                    'urlPayment': get_transaction_url(request, transaction['transaction'])
                }
                return Response(transaction, status=status.HTTP_201_CREATED)
            transaction = transaction['transaction']
            self.save_customer_details(request.data, transaction)
            self.save_items(request.data, transaction)

            return Response({
                'transactionCode': transaction.code,
                'urlPayment': get_transaction_url(request, transaction),
                'expiredAt': get_time_id(transaction.expired_at)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentView(View):
    def get(self, request, *args, **kwargs):
        if not request.GET.get('code'):
            return HttpResponseNotFound()
        transaction = Transaction.objects.filter(code=request.GET.get('code')).first()
        if not transaction:
            return HttpResponseNotFound()
        
        if check_expired(transaction.expired_at):
            if transaction.status != 1:
                transaction.status = 2
                transaction.save()
            return HttpResponseNotFound()
        
        payment_methods = PaymentMethod.objects.all()
        return render(request, 'payment.html', {
            'payment_methods': payment_methods, 
            'transaction': transaction,
            'url_back': get_transaction_url(request, transaction)
        })
    
    def post(self, request, *args, **kwargs):
        payment_method = request.POST.get('payment_method')
        if not payment_method:
            return HttpResponseNotFound()
        transaction = Transaction.objects.filter(code=request.GET.get('code')).first()
        if not transaction:
            return HttpResponseNotFound()
        payment_method = PaymentMethod.objects.filter(id=payment_method).first()
        if not payment_method:
            return HttpResponseNotFound()
        transaction.payment_method = payment_method
        transaction.save()

        transaction = Transaction.objects.filter(code=request.GET.get('code')).first()
        pay_result = render_to_string('pay.html', {'transaction': transaction, 'url_check': get_check_payment_url(request, transaction)})
        return HttpResponse(pay_result)

class CheckPaymentView(View):
    def get_bank_mutation(self):
        return True
    
    def get(self, request, *args, **kwargs):
        if not request.GET.get('code'):
            return HttpResponseNotFound()
        transaction = Transaction.objects.filter(code=request.GET.get('code')).first()
        if not transaction:
            return HttpResponseNotFound()

        if check_expired(transaction.expired_at):
            if transaction.status != 1:
                transaction.status = 2
                transaction.save()
            return HttpResponseClientRefresh()
        
        if transaction.check_count != 0:
            if get_datetime_now() < get_expired_at(transaction.check_count * 5,transaction.check_time):
                time_to_get = get_expired_at(transaction.check_count * 2,transaction.check_time) - get_datetime_now()
                time_to_get = math.ceil(time_to_get.seconds/60)
                return HttpResponse(f'Harap tunggu {time_to_get} menit')
        
        status = self.get_bank_mutation()
        if status:
            transaction.status = 1
            transaction.save()
            return HttpResponseClientRedirect(transaction.callback_url)
        else :
            transaction.check_count += 1
            transaction.check_time = get_datetime_now()
            transaction.save()
            return HttpResponse('Pending')
