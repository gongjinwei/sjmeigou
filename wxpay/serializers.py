# -*- coding:UTF-8 -*-
from rest_framework import serializers


class UnifiedOrderSerializer(serializers.Serializer):
    out_trade_no=serializers.CharField(max_length=32,required=True,help_text='商户订单号')
    body=serializers.CharField(max_length=128,required=True,help_text="商品描述")
    total_fee=serializers.IntegerField(help_text="订单总金额，单位为分")
    trade_type=serializers.CharField(max_length=16,default='JSAPI',read_only=True,required=False)
    openid=serializers.CharField(max_length=128,help_text="小程序ID")
    spbill_create_ip=serializers.CharField(max_length=16,help_text="用户终端ip",required=False)

class NotifyOrderSerializer(serializers.Serializer):
    data=serializers.JSONField(required=False)