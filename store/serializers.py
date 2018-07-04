# -*- coding:UTF-8 -*-
from rest_framework import serializers
from . import models

from goods.models import GoodDetail

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


class StoreQRCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.StoreQRCode
        fields='__all__'


class StoreInfoSerializer(serializers.ModelSerializer):
    business_hours=serializers.SerializerMethodField()
    store_name=serializers.ReadOnlyField(source='info.store_name')
    address_name=serializers.ReadOnlyField(source='info.store_address')
    longitude=serializers.ReadOnlyField(source='info.longitude')
    latitude=serializers.ReadOnlyField(source='info.latitude')
    store_phone=serializers.ReadOnlyField(source='info.store_phone')
    store_images=serializers.SerializerMethodField()

    def get_business_hours(self,obj):
        return "{0.hour:0>2}:{0.minute:0>2}/{1.hour:0>2}:{1.minute:0>2}".format(obj.business_hour_from,obj.business_hour_to)

    def get_store_images(self,obj):
        return obj.info.store_images.values('store_image')

    class Meta:
        model = models.Stores
        fields=('id','business_hours','active_state','create_time','store_name','address_name','longitude','latitude','store_phone','store_images')


class EnterpriseQualificationSerializer(serializers.ModelSerializer):
    license_unit_name=serializers.ReadOnlyField(source='info.license_unit_name')
    license_legal_representative=serializers.ReadOnlyField(source='info.license_legal_representative')
    store_licence_pic=serializers.ReadOnlyField(source='info.store_licence_pic')

    class Meta:
        model = models.Stores
        fields=('license_unit_name','license_legal_representative','store_licence_pic')


class GoodDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = GoodDetail
        fields=('id','title','good_type','create_time','min_price','state')


class GoodsTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.GoodsType
        exclude=('store_goods_type',)


class StoreGoodsTypeSerializer(serializers.ModelSerializer):
    good_types=GoodsTypeSerializer(many=True)

    class Meta:
        model = models.StoreGoodsType
        fields='__all__'

    def create(self, validated_data):
        type_data=validated_data.pop('good_types')
        store_good_type,created=models.StoreGoodsType.objects.update_or_create(defaults=validated_data,**validated_data)

        for data in type_data:
            data.update(store_goods_type=store_good_type)

            models.GoodsType.objects.update_or_create(defaults=data,order_num=data.get('order_num'),store_goods_type=store_good_type)
        return store_good_type


class AddGoodsSerializer(serializers.Serializer):
    good_list=serializers.ListField()
    put_on_sale_list=serializers.ListField()



