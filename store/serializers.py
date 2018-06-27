# -*- coding:UTF-8 -*-
from rest_framework import serializers
from . import models

from index.models import Application

class CheckApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CheckApplication
        fields = '__all__'


class GenerateCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CodeWarehouse
        fields = '__all__'


class StoresSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Stores
        fields='__all__'


class StoreStatusSerializer(serializers.ModelSerializer):
    status_name=serializers.ReadOnlyField(source='get_application_status_display')

    class Meta:
        model=Application
        fields=('application_id',"store_name",'update_time','application_status','status_name')


class StatusChangeSerializer(serializers.Serializer):
    application_status=serializers.IntegerField(choices=[1,2,3,4,5,6])
    application_id=serializers.CharField(max_length=20)