# -*- coding:UTF-8 -*-
import datetime
from rest_framework import serializers

from django.db.models import F, Q,Sum

from . import models
from store.models import Stores


class ShoppingCarItemSerializer(serializers.ModelSerializer):
    title = serializers.ReadOnlyField(source='sku.color.good_detail.title')
    price = serializers.ReadOnlyField(source='sku.price')
    color = serializers.ReadOnlyField(source='sku.color.color_name')
    color_pic = serializers.ReadOnlyField(source='sku.color.color_pic')
    stock = serializers.ReadOnlyField(source='sku.stock')
    size = serializers.ReadOnlyField(source='sku.size.size_name')
    good_id = serializers.ReadOnlyField(source='sku.color.good_detail.id')
    # activities = serializers.SerializerMethodField()

    store = serializers.IntegerField(write_only=True)

    class Meta:
        model = models.ShoppingCarItem
        exclude = ('shopping_car',)

    # def get_activities(self, obj):
    #     store = obj.shopping_car.store
    #     good = obj.sku.color.good_detail
    #     now = datetime.datetime.now()
    #
    #     # 获取所有在进行中的活动
    #     if good.store == store:
    #         activities_filter = models.StoreActivity.objects.filter(store=store, state=0, datetime_to__gte=now,
    #                                                                 datetime_from__lte=now)
    #
    #         # 在正常的活动中过滤或者选中了所有商品的或者有参与的活动
    #         relate_activities = activities_filter.filter(
    #             Q(select_all=True) | Q(select_all=False, selected_goods__good=good))
    #         if relate_activities.exists() and good.store == store:
    #             return relate_activities.values_list('id',flat=True)

    def create(self, validated_data):
        ModelClass = self.Meta.model
        num = validated_data.get('num')
        total_money=validated_data.get('total_money')
        price_of_added=validated_data.get('price_of_added')
        store_id = validated_data.pop('store')
        store = Stores.objects.get(pk=store_id)
        user = validated_data.pop('user')
        shopping_car, creating = models.ShoppingCar.objects.get_or_create(defaults={'user': user, 'store': store},
                                                                          user=user, store=store)

        validated_data.update({"shopping_car": shopping_car})
        instance, created = ModelClass.objects.get_or_create(defaults=validated_data, sku=validated_data['sku'],
                                                             shopping_car=validated_data['shopping_car'])
        if not created:
            ModelClass.objects.filter(pk=instance.id).update(num=F('num') + num,total_money=F('total_money')+total_money,price_of_added=price_of_added)
        return instance


class ShoppingCarSerializer(serializers.ModelSerializer):
    items = ShoppingCarItemSerializer(many=True, read_only=True)
    store_name = serializers.ReadOnlyField(source='store.info.store_name')
    store_logo = serializers.ReadOnlyField(source='store.logo')
    coupons = serializers.SerializerMethodField()
    store_activities = serializers.SerializerMethodField()

    def get_store_activities(self, obj):
        now = datetime.datetime.now()
        # 取出所有活动
        activities=models.StoreActivity.objects.filter(store=obj.store, state=0, datetime_to__gte=now,
                                                   datetime_from__lte=now)
        # 取出购车车中数量总金额与数量
        car_items=models.ShoppingCarItem.objects.filter(shopping_car=obj)
        items_num=car_items.annotate(total_num=Sum('num')).values('total_num')
        items_money=car_items.annotate(all_money=Sum('total_money')).values('all_money')
        ret = []
        if items_num and items_money:
            items_num = items_num[0].get('total_num')
            items_money=items_money[0].get('all_money')
            for activity in activities:
                x,y=activity.algorithm(items_num,items_money)
                ret.append({'id':activity.id,'activity':x,'reduction_money':y})
        return ret

    def get_coupons(self,obj):
        today = datetime.date.today()
        return models.Coupon.objects.filter(store=obj.store, date_to__gte=today,date_from__lte=today,available_num__gt=0).values()

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


class JoinActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.JoinActivity
        fields = '__all__'
