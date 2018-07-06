# -*- coding:UTF-8 -*-
from rest_framework import serializers

from django.db.models import F

from . import models


class ShoppingCarItemSerializer(serializers.ModelSerializer):
    sku_id = serializers.ReadOnlyField(source='sku.id')
    title = serializers.ReadOnlyField(source='sku.color.good_detail.title')
    price = serializers.ReadOnlyField(source='sku.price')
    color = serializers.ReadOnlyField(source='sku.color.color_name')
    size = serializers.ReadOnlyField(source='sku.size.size_name')
    good_id = serializers.ReadOnlyField(source='sku.color.good_detail.id')
    store_id = serializers.ReadOnlyField(source='sku.color.good_detail.store.id')

    class Meta:
        model = models.ShoppingCarItem
        fields = '__all__'

    def create(self, validated_data):
        ModelClass = self.Meta.model
        num = validated_data.get('num')

        instance, created = ModelClass.objects.get_or_create(defaults=validated_data, sku=validated_data['sku'],
                                                             user=validated_data['user'])
        if not created:
            ModelClass.objects.filter(pk=instance.id).update(num=F('num') + num)
        return instance


def check_discount(value):
    if value % 5 != 0:
        raise serializers.ValidationError('折扣面额必须是5的倍数')


class CouponSerializer(serializers.ModelSerializer):
    discount = serializers.IntegerField(validators=[check_discount])

    class Meta:
        model = models.Coupon
        fields = '__all__'


class GetCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GetCoupon
        fields = '__all__'

    def create(self, validated_data):
        instance, created = models.GetCoupon.objects.get_or_create(defaults=validated_data, user=validated_data['user'],
                                                             coupon=validated_data['coupon'])
        models.GetCoupon.objects.filter(pk=instance.id).update(has_num=F('has_num')+1)
        # 记录领取的行为
        record=models.CouponRecords()
        record.get_coupon=instance
        record.action=0
        record.save()
        return instance