# -*- coding:UTF-8 -*-
from rest_framework import serializers

from . import models


class SecondClassSerializer(serializers.ModelSerializer):

    class Meta:
        model=models.SecondClass
        fields=('second_class_name','id')


class FirstClassSerializer(serializers.ModelSerializer):
    second_classes=SecondClassSerializer(many=True,read_only=True)

    class Meta:
        model=models.FirstClass
        fields=('second_classes','first_class_name')


class ThirdClassSerializer(serializers.ModelSerializer):

    class Meta:
        model=models.ThirdClass
        fields=('id','third_class_name')


class FirstPropertySerializer(serializers.ModelSerializer):

    class Meta:
        model=models.FirstProperty
        fields='__all__'


class SecondPropertySerializer(serializers.ModelSerializer):

    class Meta:
        model=models.SecondProperty
        fields='__all__'


