# -*- coding:UTF-8 -*-
from rest_framework import serializers

from django.db.models import F

from . import models


class ShoppingCarItemSerializer(serializers.ModelSerializer):
    sku_id=serializers.ReadOnlyField(source='sku.id')
    title=serializers.ReadOnlyField(source='sku.color.good_detail.title')
    price=serializers.ReadOnlyField(source='sku.price')
    color=serializers.ReadOnlyField(source='sku.color.color_name')
    size=serializers.ReadOnlyField(source='sku.size.size_name')
    good_id=serializers.ReadOnlyField(source='sku.color.good_detail.id')
    store_id=serializers.ReadOnlyField(source='sku.color.good_detail.store.id')

    class Meta:
        model=models.ShoppingCarItem
        fields='__all__'

    def create(self, validated_data):

        ModelClass = self.Meta.model
        num=validated_data.get('num')

        instance,created = ModelClass.objects.get_or_create(defaults=validated_data,sku=validated_data['sku'],user=validated_data['user'])
        if not created:
            ModelClass.objects.filter(pk=instance.id).update(num=F('num')+num)
        return instance
