# -*- coding:UTF-8 -*-
from rest_framework import serializers

from . import models


class SecondClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SecondClass
        fields = ('second_class_name', 'id')


class FirstClassSerializer(serializers.ModelSerializer):
    second_classes = SecondClassSerializer(many=True, read_only=True)

    class Meta:
        model = models.FirstClass
        fields = ('second_classes', 'first_class_name')


class ThirdClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ThirdClass
        fields = ('id', 'third_class_name')


class SecondPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SecondProperty
        fields = ('id', 'second_property_name', 'first_property')


class FirstPropertySerializer(serializers.ModelSerializer):
    # third_class_name=serializers.ReadOnlyField(source='third_class.third_class_name')
    # second_class_name=serializers.ReadOnlyField(source='third_class.second_class.second_class_name')
    secondProperties = SecondPropertySerializer(read_only=True, many=True)

    class Meta:
        model = models.FirstProperty
        fields = ('id', 'first_property_name', 'third_class', 'secondProperties')
        # fields=('id','first_property_name','third_class','third_class_name','second_class_name','secondProperties')


class SizeDescSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SizeDesc
        fields = '__all__'


class SizeGroupSerializer(serializers.ModelSerializer):
    sizes=SizeDescSerializer(many=True,read_only=True)

    class Meta:
        model = models.SizeGroup
        fields = '__all__'
