from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from payment.serializer import TransactionSerializer, HeaderSerializer
from payment.models import Transaction, Merchant, CustomerDetails, TransactionItem, PaymentMethod
from django.views.generic import View
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.template.loader import render_to_string
from payment.helpers import *
import math
from django_htmx.http import HttpResponseClientRefresh, HttpResponseClientRedirect
import json

class TransactionCreateView(APIView):
    def save_transaction(self, data):
        merchant = Merchant.objects.filter(code=data['merchantCode']).first()
        
        transaction = Transaction.objects.filter(invoice_code=data['invoiceCode']).first()
        if transaction is not None:
            return {'transaction': transaction, 'status': 'exists'}

        data = {
            'amount': data['paymentAmount'],
            'invoice_code': data['invoiceCode'],
            'merchant': merchant,
            'callback_url': data['callback_url'],
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
    
    def validate_header(self, request):
        if 'signature' not in request.headers or not request.headers["signature"]:
            return False
        if 'timestamp' not in request.headers or not request.headers["timestamp"]:
            return False
        if 'merchantcode' not in request.headers or not request.headers["merchantcode"]:
            return False
        return True
    
    def post(self, request, format=None):
        if not self.validate_header(request):
            return Response({'message': 'Invalid header'}, status=status.HTTP_400_BAD_REQUEST)
        
        merchant = Merchant.objects.filter(code=request.headers["merchantcode"]).first()
        if merchant is None:
            return Response({'message': 'Merchant not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not verify_signature(merchant.code, merchant.api_key, request.headers["signature"], request.headers["timestamp"]):
            return Response({'message': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            request.data["merchantCode"] = request.headers["merchantcode"]
            transaction = self.save_transaction(request.data)
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
                'urlPayment': get_transaction_url(request, transaction)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PaymentView(View):
    def get(self, request, *args, **kwargs):
        if not request.GET.get('code'):
            return HttpResponseNotFound()
        transaction = Transaction.objects.filter(code=request.GET.get('code')).first()
        if not transaction:
            return HttpResponseNotFound()
        if transaction.status == 1:
            return HttpResponseRedirect(get_callback_url(transaction))
        
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

        if transaction.status == 1:
            return HttpResponseRedirect(get_callback_url(transaction))
        
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

        if transaction.status == 1:
            return HttpResponse(get_callback_url(transaction))
        
        if transaction.check_count != 0:
            if get_datetime_now() < get_expired_at(transaction.check_count * 2,transaction.check_time):
                time_to_get = get_expired_at(transaction.check_count * 2,transaction.check_time) - get_datetime_now()
                time_to_get = math.ceil(time_to_get.seconds/60)
                return HttpResponse(time_to_get)
        
        status = self.get_bank_mutation()
        if status:
            transaction.status = 1
            transaction.save()
            return HttpResponse(get_callback_url(transaction))
        else :
            transaction.check_count += 1
            transaction.check_time = get_datetime_now()
            transaction.save()
            return HttpResponse('002')

class ConfirmPayment(APIView):
    def validate_header(self, request):
        if 'signature' not in request.headers or not request.headers["signature"]:
            return False
        if 'timestamp' not in request.headers or not request.headers["timestamp"]:
            return False
        if 'merchantcode' not in request.headers or not request.headers["merchantcode"]:
            return False
        return True
    
    def get(self, request, *args, **kwargs):
        if not request.GET.get('code'):
            return HttpResponseNotFound()
        if not self.validate_header(request):
            return Response({'message': 'Invalid header'}, status=status.HTTP_400_BAD_REQUEST)
        merchant = Merchant.objects.filter(code=request.headers["merchantcode"]).first()
        if merchant is None:
            return Response({'message': 'Merchant not found'}, status=status.HTTP_400_BAD_REQUEST)
        if not verify_signature(merchant.code, merchant.api_key, request.headers["signature"], request.headers["timestamp"]):
            return Response({'message': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)
        
        transaction = Transaction.objects.filter(code=request.GET.get('code')).first()
        if transaction is None:
            return Response({'message': 'Transaction not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'transactionCode': transaction.code,
            'invoiceCode': transaction.invoice_code,
            'amount': transaction.amount,
            'status': transaction.status
        }, status=status.HTTP_200_OK)
        
