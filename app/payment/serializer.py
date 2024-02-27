from rest_framework import serializers
from payment.models import Transaction, TransactionItem, CustomerDetails

class TransactionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionItem
        fields = ["name", "quantity", "price"]

class CustomerDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerDetails
        fields = ["firstname", "lastname", "email", "phone", "address", "city", "province", "country", "postal_code"]

class TransactionSerializer(serializers.ModelSerializer):
    itemsDetails = TransactionItemSerializer(many=True)
    customerDetails = CustomerDetailsSerializer()

    invoiceCode = serializers.CharField(source='code')
    paymentAmount = serializers.CharField(source='amount')

    class Meta:
        model = Transaction
        fields = ["invoiceCode", "paymentAmount", "customerDetails", "itemsDetails","callback_url"]

class CheckTransactionSerializer(serializers.ModelSerializer):
    merchantCode = serializers.CharField()
    invoiceCode = serializers.CharField()

    class Meta:
        model = Transaction
        fields = ["merchantCode", "invoiceCode"]


class HeaderSerializer(serializers.Serializer):
    signature = serializers.CharField()
    timestamp = serializers.IntegerField()
    merchantcode = serializers.CharField()

    class Meta:
        fields = ["signature", "timestamp", "merchantcode"]