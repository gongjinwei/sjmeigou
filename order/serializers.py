# -*- coding:UTF-8 -*-
from rest_framework import serializers
from rest_framework.utils import model_meta

from django.db.models import F

from . import models
from store.models import Stores


class ShoppingCarItemSerializer(serializers.ModelSerializer):
    title = serializers.ReadOnlyField(source='sku.color.good_detail.title')
    price = serializers.ReadOnlyField(source='sku.price')
    color = serializers.ReadOnlyField(source='sku.color.color_name')
    color_pic=serializers.ReadOnlyField(source='sku.color.color_pic')
    stock = serializers.ReadOnlyField(source='sku.stock')
    size = serializers.ReadOnlyField(source='sku.size.size_name')
    good_id = serializers.ReadOnlyField(source='sku.color.good_detail.id')
    store = serializers.IntegerField(write_only=True)

    class Meta:
        model = models.ShoppingCarItem
        exclude=('shopping_car',)

    def create(self, validated_data):
        ModelClass = self.Meta.model
        num = validated_data.get('num')
        store_id = validated_data.pop('store')
        store = Stores.objects.get(pk=store_id)
        user = validated_data.pop('user')
        shopping_car, creating = models.ShoppingCar.objects.get_or_create(defaults={'user': user, 'store': store},
                                                                          user=user, store=store)

        validated_data.update({"shopping_car": shopping_car})
        instance, created = ModelClass.objects.get_or_create(defaults=validated_data, sku=validated_data['sku'],
                                                             shopping_car=validated_data['shopping_car'])
        if not created:
            ModelClass.objects.filter(pk=instance.id).update(num=F('num') + num)
        return instance

    def update(self, instance, validated_data):
        instance= models.ShoppingCarItem.objects.get(shopping_car=instance.shopping_car,sku=instance.sku)
        info = model_meta.get_field_info(instance)

        # Simply set each attribute on the instance, and then save it.
        # Note that unlike `.create()` we don't need to treat many-to-many
        # relationships as being a special case. During updates we already
        # have an instance pk for the relationships to be associated with.
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                field = getattr(instance, attr)
                field.set(value)
            else:
                setattr(instance, attr, value)
        instance.save()

        return instance


class ShoppingCarSerializer(serializers.ModelSerializer):
    items = ShoppingCarItemSerializer(many=True,read_only=True)
    store_name = serializers.ReadOnlyField(source='store.info.store_name')
    store_logo=serializers.ReadOnlyField(source='store.logo')

    class Meta:
        model = models.ShoppingCar
        fields = '__all__'


def check_discount(value):
    if value % 5 != 0:
        raise serializers.ValidationError('折扣面额必须是5的倍数')


class CouponSerializer(serializers.ModelSerializer):
    discount = serializers.IntegerField(validators=[check_discount])

    class Meta:
        model = models.Coupon
        fields = '__all__'


class GetCouponSerializer(serializers.ModelSerializer):
    date_from = serializers.ReadOnlyField(source='coupon.date_from')
    date_to = serializers.ReadOnlyField(source='coupon.date_to')
    store_name = serializers.ReadOnlyField(source='coupon.store.info.store_name')

    class Meta:
        model = models.GetCoupon
        fields = '__all__'

    def create(self, validated_data):
        instance, created = models.GetCoupon.objects.get_or_create(defaults=validated_data, user=validated_data['user'],
                                                                   coupon=validated_data['coupon'])
        models.GetCoupon.objects.filter(pk=instance.id).update(has_num=F('has_num') + 1)
        # 记录领取的行为
        record = models.CouponRecords()
        record.get_coupon = instance
        record.action = 0
        record.save()
        return instance


class StoreActivitySelectedSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StoreActivitySelected
        fields = '__all__'


class StoreActivitySerializer(serializers.ModelSerializer):
    selected_goods = StoreActivitySelectedSerializer(many=True, required=False)

    class Meta:
        model = models.StoreActivity
        fields = '__all__'

    def create(self, validated_data):
        selected_data = validated_data.pop('selected_goods', [])
        activity = self.Meta.model.objects.create(**validated_data)
        for data in selected_data:
            models.StoreActivitySelected.objects.create(activity=activity, **data)
        return activity
