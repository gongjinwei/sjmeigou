# -*- coding:UTF-8 -*-
from rest_framework import serializers
from . import models


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
        return "%s/%s" % (obj.business_hour_from,obj.business_hour_to)

    def get_store_images(self,obj):
        return obj.info.store_images.values('store_image')

    class Meta:
        model = models.Stores
        fields=('id','business_hours','active_state','create_time','store_name','address_name','longitude','latitude','store_phone','store_images')