# -*- coding:UTF-8 -*-

from rest_framework import serializers
from . import models

class CheckApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CheckApplication
        fields = '__all__'


class StoreActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StoreActivityType
        fields = '__all__'


class DeliverSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Delivers
        fields = '__all__'


class DeliverServiceSerializer(serializers.ModelSerializer):
    delivers=DeliverSerializer(many=True,read_only=True)

    class Meta:
        model = models.DeliverServices
        fields = '__all__'

# class
