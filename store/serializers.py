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


class StoresSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Stores
        fields='__all__'
