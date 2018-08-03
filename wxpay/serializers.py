# -*- coding:UTF-8 -*-
from rest_framework import serializers
from . import models
from delivery.models import InitDwdOrder


class NotifyOrderSerializer(serializers.ModelSerializer):

    class Meta:
        fields="__all__"
        model=models.NotifyOrderModel


class InitDwdOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = InitDwdOrder
        exclude =('good_refund','store_order')
