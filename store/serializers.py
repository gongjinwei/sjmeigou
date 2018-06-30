# -*- coding:UTF-8 -*-
from rest_framework import serializers
from . import models


class GenerateCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CodeWarehouse
        fields = '__all__'


class StoresSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Stores
        fields='__all__'


class StatusChangeSerializer(serializers.Serializer):
    application_status=serializers.ChoiceField(choices=[1,2,3,4,5,6])
    application_id=serializers.CharField(max_length=20)


class DepositSerializer(serializers.ModelSerializer):
    application=serializers.CharField(max_length=20,required=True)

    class Meta:
        model = models.Deposit
        fields='__all__'