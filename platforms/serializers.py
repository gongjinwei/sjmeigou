# -*- coding:UTF-8 -*-

from rest_framework import serializers
from . import models
from index.models import Application


class CheckApplicationSerializer(serializers.ModelSerializer):
    application = serializers.PrimaryKeyRelatedField(queryset=Application.objects.filter(application_status=1))

    class Meta:
        model = models.CheckApplication
        fields = '__all__'


class StoreActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StoreActivityType
        fields = '__all__'


class DeliverSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Delivers
        fields = '__all__'


class DeliverServiceSerializer(serializers.ModelSerializer):
    delivers = DeliverSerializer(many=True, read_only=True)

    class Meta:
        model = models.DeliverServices
        fields = '__all__'


class GenerateCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CodeWarehouse
        fields = '__all__'


class AccountRechargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AccountRecharge
        fields = '__all__'


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Account
        fields = ('id', 'account_type', 'bank_balance')


class KeepAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.KeepAccounts
        fields = '__all__'


class DeliverReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DeliveryReason
        fields = '__all__'


class ProtocolSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Protocol
        fields = '__all__'


class RefundReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RefundReason
        fields = '__all__'


class BargainPosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BargainPoster
        fields = '__all__'
