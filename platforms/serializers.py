# -*- coding:UTF-8 -*-

from rest_framework import serializers
from . import models
from order.models import StoreActivityType


class CheckApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CheckApplication
        fields = '__all__'


class StoreActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model=StoreActivityType
        fields='__all__'