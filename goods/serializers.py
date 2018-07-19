# -*- coding:UTF-8 -*-
import datetime
from rest_framework import serializers
from order.models import Coupon,StoreActivity
from django.db.models import Q


from . import models
from platforms.serializers import DeliverServiceSerializer
from platforms.models import DeliverServices

class SecondClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SecondClass
        fields = ('second_class_name', 'id')


class FirstClassSerializer(serializers.ModelSerializer):
    second_classes = SecondClassSerializer(many=True, read_only=True)

    class Meta:
        model = models.FirstClass
        fields = ('second_classes', 'first_class_name','cover_path')


class SizeDescSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SizeDesc
        exclude=("size_group",)


class SizeGroupSerializer(serializers.ModelSerializer):
    sizes = SizeDescSerializer(many=True, read_only=True)

    class Meta:
        model = models.SizeGroup
        exclude=('second_class',)


class SizeGroupClassSerializer(serializers.ModelSerializer):
    size_group=SizeGroupSerializer(read_only=True)

    class Meta:
        model = models.SizeGroupClass
        fields = '__all__'


class ThirdClassSerializer(serializers.ModelSerializer):
    size_group_classes = SizeGroupClassSerializer(many=True, read_only=True)

    class Meta:
        model = models.ThirdClass
        fields = ('id', 'third_class_name','size_group_classes')


class SecondPropertySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.SecondProperty
        fields = ('id', 'second_property_name', 'first_property')


class FirstPropertySerializer(serializers.ModelSerializer):
    # third_class_name=serializers.ReadOnlyField(source='third_class.third_class_name')
    # second_class_name=serializers.ReadOnlyField(source='third_class.second_class.second_class_name')
    secondProperties = SecondPropertySerializer(read_only=True, many=True)
    delivers = serializers.SerializerMethodField()

    class Meta:
        model = models.FirstProperty
        fields = ('id', 'first_property_name', 'third_class', 'secondProperties')
        # fields=('id','first_property_name','third_class','third_class_name','second_class_name','secondProperties')

    def get_delivers(self,obj):
        serializer=DeliverServiceSerializer(DeliverServices.objects.all(),many=True)
        return serializer.data


class ItemsGroupDescSerializer(serializers.ModelSerializer):
    items=serializers.JSONField()

    class Meta:
        model=models.ItemsGroupDesc
        fields='__all__'


class SKUSerializer(serializers.ModelSerializer):
    size_name = serializers.ReadOnlyField(source='size.size_name')

    class Meta:
        model=models.SKU
        exclude = ('color',)


class AfterSaleServicesSerializer(serializers.ModelSerializer):
    server_name = serializers.ReadOnlyField(source='get_server_display')

    class Meta:
        model=models.AfterSaleServices
        fields = ('server', 'server_name')


class GoodDeliverSerializer(serializers.ModelSerializer):
    deliver_name = serializers.ReadOnlyField(source='server.name')
    server_name = serializers.ReadOnlyField(source='server.deliver_server.name')

    class Meta:
        model = models.GoodDetail
        fields = ('server','server_name','deliver_name')


class SKUColorSerializer(serializers.ModelSerializer):
    skus=SKUSerializer(many=True)

    class Meta:
        model = models.SKUColor
        exclude=('good_detail',)

    def create(self, validated_data):
        skus = validated_data.pop('skus')
        instance=models.SKUColor.objects.create(**validated_data)
        for sku in skus:
            models.SKU.objects.create(color=instance, **sku)


class GoodDetailSerializer(serializers.ModelSerializer):
    class_name=serializers.SerializerMethodField()
    relate_desc=serializers.ReadOnlyField(source='item_desc.items')
    params=serializers.JSONField()
    master_graphs=serializers.JSONField()
    colors=SKUColorSerializer(many=True)
    after_sale_services=AfterSaleServicesSerializer(many=True)
    delivers=GoodDeliverSerializer(many=True)

    def get_class_name(self,obj):
        return "%s>%s" % (obj.third_class.second_class.second_class_name,obj.third_class.third_class_name)

    class Meta:
        model = models.GoodDetail
        fields = '__all__'

    def create(self, validated_data):
        colors=validated_data.pop('colors')
        after_sale_services=validated_data.pop('after_sale_services')
        delivers=validated_data.pop('delivers')

        instance=models.GoodDetail.objects.create(**validated_data)

        for service in after_sale_services:
            models.AfterSaleServices.objects.create(good_detail=instance,**service)
        for deliver in delivers:
            models.GoodDeliver.objects.create(good_detail=instance,**deliver)
        for color_data in colors:
            skus=color_data.pop('skus')
            color=models.SKUColor.objects.create(good_detail=instance,**color_data)
            for sku in skus:
                models.SKU.objects.create(color=color,**sku)

        return instance


class GoodSearchSerializer(serializers.ModelSerializer):
    master_graph=serializers.SerializerMethodField()
    coupons = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()

    class Meta:
        model = models.GoodDetail
        fields = ('title','master_graph','min_price','coupons','activities','store')

    def get_master_graph(self,obj):
        if obj.master_graphs:
            return obj.master_graphs[0]

    def get_coupons(self,obj):
        store = obj.store
        today = datetime.date.today()
        coupon = Coupon.objects.filter(store=store,date_from__gte=today,date_to__lte=today,available_num__gt=0)
        return [cou.act_name for cou in coupon]

    def get_activities(self,obj):
        store =obj.store
        now = datetime.datetime.now()
        valid_activities=StoreActivity.objects.filter(store=store,datetime_from__lte=now,datetime_to__gte=now,state=0)
        good_activities=valid_activities.filter(Q(select_all=True)|Q(selected_goods__good=obj))

        return [activity.act_name for activity in good_activities]
