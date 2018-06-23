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
    generate=serializers.BooleanField(default=False)

    class Meta:
        model = models.CodeWarehouse
        fields = '__all__'

    def create(self, validated_data):
        validated_data.pop('generate')
        super().create(validated_data)