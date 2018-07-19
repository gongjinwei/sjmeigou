# -*- coding:UTF-8 -*-
from rest_framework import serializers
from geopy.distance import VincentyDistance

from . import models

from goods.models import GoodDetail

class GenerateCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CodeWarehouse
        fields = '__all__'


class StoresSerializer(serializers.ModelSerializer):
    active_code=serializers.CharField(write_only=True)

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
    store_images=serializers.SerializerMethodField()

    def get_store_images(self,obj):
        return obj.info.store_images.values('store_image')

    class Meta:
        model = models.Stores
        fields=('id','business_hour_from','business_hour_to','logo','active_state','create_time','name','receive_address','longitude','latitude','store_phone','store_images')


class EnterpriseQualificationSerializer(serializers.ModelSerializer):
    license_unit_name=serializers.ReadOnlyField(source='info.license_unit_name')
    license_legal_representative=serializers.ReadOnlyField(source='info.license_legal_representative')
    store_licence_pic=serializers.ReadOnlyField(source='info.store_licence_pic')

    class Meta:
        model = models.Stores
        fields=('license_unit_name','license_legal_representative','store_licence_pic')


class GoodDetailSerializer(serializers.ModelSerializer):
    good_type_name=serializers.ReadOnlyField(source='good_type.name')
    master_graph=serializers.SerializerMethodField()

    class Meta:
        model = GoodDetail
        fields=('id','title','good_type','create_time','min_price','state','good_type_name','master_graph')

    def get_master_graph(self,obj):
        if obj.master_graphs:
            return obj.master_graphs[0]


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
    good_list=serializers.ListField(required=False)
    put_on_sale_list=serializers.ListField(required=False)


class StoreSearchSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Stores
        fields=('name','logo','receive_address','latitude','longitude')

    def to_representation(self, instance):
        ret=super().to_representation(instance)
        request = self.context.get('request')
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        if lat and lng:
            lat=float(lat)
            lng=float(lng)
            distance=round(VincentyDistance((lat, lng),(ret['latitude'], ret['longitude'])).kilometers, 1)

            ret.update({
                "distance": distance
            })
        return ret


