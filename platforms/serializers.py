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
    delivers=DeliverSerializer(many=True,read_only=True)

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
        fields = '__all__'