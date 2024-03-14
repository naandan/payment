from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from payment.serializer import TransactionSerializer
from payment.models import Transaction, Merchant, CustomerDetails, TransactionItem, PaymentMethod, Pay
from django.views.generic import View
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.template.loader import render_to_string
from payment.helpers import *
import math

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
            'return_url': data['return_url'],
        }
        
        data['code'] = generate_transaction_code()
        transaction = Transaction.objects.create(**data)
        return {'transaction': transaction, 'status': 'created'}

    def create_payment(self, data):
        data['payment_code'] = generate_payment_code()
        return Pay.objects.create(**data)

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
        if not validate_header(request):
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
                transaction = transaction['transaction']
                if transaction.status == 0:
                    payment = Pay.objects.filter(transaction=transaction, status=0).first()
                    if payment is None:
                        self.create_payment({
                            'transaction': transaction,
                            'amount': request.data['paymentAmount']
                        })
                transaction = {
                    'transactionCode': transaction.code,
                    'urlPayment': get_transaction_url(request, transaction)
                }
                return Response(transaction, status=status.HTTP_201_CREATED)
            
            transaction = transaction['transaction']
            self.create_payment({'transaction': transaction,'amount': request.data['paymentAmount']})
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
            return HttpResponseRedirect(get_return_url(transaction))
        
        payment_methods = PaymentMethod.objects.all()
        transaction.total = transaction.amount - transaction.paid
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
            return HttpResponseRedirect(get_return_url(transaction))
        
        payment_method = PaymentMethod.objects.filter(id=payment_method).first()
        if not payment_method:
            return HttpResponseNotFound()
        
        payment = Pay.objects.filter(transaction=transaction, status=0).first()
        if payment is None:
            return HttpResponseRedirect(get_return_url(transaction))

        payment.payment_method = payment_method
        payment.save()

        transaction = Transaction.objects.filter(code=request.GET.get('code')).first()
        transaction.total = transaction.amount - transaction.paid
        pay_result = render_to_string('pay.html', {'transaction': transaction, 'payment': payment, 'url_check': get_check_payment_url(request, transaction)})
        return HttpResponse(pay_result)

class CheckPaymentView(View):
    def get_bank_mutation(self, transaction, payment):
        data = [
            {
                "bank": "BCA",
                "account": "12345678900",
                "amount": 10000,
                "note": "#PAY37584",
                "date": "2024-03-14 15:00:00",
            },
            {
                "bank": "BCA",
                "account": "12345678900",
                "amount": 100000,
                "note": "#PAY74562",
                "date": "2024-03-14 17:00:00",
            }
        ]

        payment_paid = 0

        for item in data:
            if item['note'] == f"#{payment.payment_code}" and item['date'].split(' ')[0] == get_datetime_now().strftime("%Y-%m-%d"):
                payment_paid += int(item['amount'])
        
        if payment_paid != 0:
            payment.status = 1
            payment.paid = payment_paid
            payment.save()

            transaction.paid += payment_paid
            transaction.save()

            return True
        return False
    
    def get(self, request, *args, **kwargs):
        if not request.GET.get('code'):
            return HttpResponseNotFound()
        transaction = Transaction.objects.filter(code=request.GET.get('code')).first()
        if not transaction:
            return HttpResponseNotFound()

        if transaction.status == 1:
            return HttpResponse(get_return_url(transaction))
        
        payment = Pay.objects.filter(transaction=transaction, status=0).first()
        
        if payment.check_count != 0:
            if get_datetime_now() < get_expired_at(payment.check_count * 2,payment.check_time):
                time_to_get = get_expired_at(payment.check_count * 2,payment.check_time) - get_datetime_now()
                time_to_get = math.ceil(time_to_get.seconds/60)
                return HttpResponse(time_to_get)
        
        status = self.get_bank_mutation(transaction, payment)
        if status:
            return HttpResponse(get_callback_url(transaction))
        else :
            payment.check_count += 1
            payment.check_time = get_datetime_now()
            payment.save()
            return HttpResponse('002')

class ConfirmPayment(APIView):
    def get(self, request, *args, **kwargs):
        if not request.GET.get('code'):
            return HttpResponseNotFound()
        if not validate_header(request):
            return Response({'message': 'Invalid header'}, status=status.HTTP_400_BAD_REQUEST)
        merchant = Merchant.objects.filter(code=request.headers["merchantcode"]).first()
        if merchant is None:
            return Response({'message': 'Merchant not found'}, status=status.HTTP_400_BAD_REQUEST)
        if not verify_signature(merchant.code, merchant.api_key, request.headers["signature"], request.headers["timestamp"]):
            return Response({'message': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)
        
        transaction = Transaction.objects.filter(code=request.GET.get('code')).first()
        if transaction is None:
            return Response({'message': 'Transaction not found'}, status=status.HTTP_400_BAD_REQUEST)
        if transaction.status == 1:
            return HttpResponseRedirect(get_return_url(transaction))

        if transaction.paid >= transaction.amount:
            transaction.status = 1
            transaction.save()
        
        return Response({
            'transactionCode': transaction.code,
            'invoiceCode': transaction.invoice_code,
            'amount': transaction.pays.first().paid,
            'status': transaction.status
        }, status=status.HTTP_200_OK)
        
