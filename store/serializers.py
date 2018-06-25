# -*- coding:UTF-8 -*-
from rest_framework import serializers
from . import models


class CheckApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CheckApplication
        fields = '__all__'


class GenerateCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CodeWarehouse
        fields = '__all__'


class CreateStoreSerializer(serializers.ModelSerializer):
    code=serializers.SlugField(source='info.CodeWarehouse.code')

    class Meta:
        model = models.CreateStore
        fields='__all__'
