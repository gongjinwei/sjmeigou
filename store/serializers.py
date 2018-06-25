# -*- coding:UTF-8 -*-
from rest_framework import serializers
from . import models


class CheckApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CheckApplication
        fields = '__all__'


class CheckCode(serializers.Serializer):
    active_code=serializers.CharField(max_length=16)


class GenerateCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CodeWarehouse
        fields = '__all__'


class CreateStoreSerializer(serializers.ModelSerializer):
    code=serializers.CharField(max_length=12)

    class Meta:
        model = models.CreateStore
        fields='__all__'

    def create(self, validated_data):
        code=validated_data.pop('code')
        return super().create(validated_data)