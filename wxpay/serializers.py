# -*- coding:UTF-8 -*-
from rest_framework import serializers
from . import models


class UnifiedOrderSerializer(serializers.Serializer):
    out_trade_no=serializers.CharField(max_length=32,required=True,help_text='商户订单号')
    userId=serializers.CharField(max_length=128,help_text="用户在小程序中的ID")
    spbill_create_ip=serializers.CharField(max_length=16,help_text="用户终端ip",required=False)


class NotifyOrderSerializer(serializers.ModelSerializer):

    class Meta:
        fields="__all__"
        model=models.NotifyOrderModel
