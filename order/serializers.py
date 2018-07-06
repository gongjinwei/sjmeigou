# -*- coding:UTF-8 -*-
from rest_framework import serializers

from . import models


class ShoppingCarItemSerializer(serializers.ModelSerializer):
    sku_id=serializers.ReadOnlyField(source='sku.id')
    title=serializers.ReadOnlyField(source='sku.color.good_detail.title')
    price=serializers.ReadOnlyField(source='sku.price')
    color=serializers.ReadOnlyField(source='sku.color.color_name')
    good_id=serializers.ReadOnlyField(source='sku.color.good_detail.id')
    store_id=serializers.ReadOnlyField(source='sku.color.good_detail.store.id')

    class Meta:
        model=models.ShoppingCarItem
        fields='__all__'
