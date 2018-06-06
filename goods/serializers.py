# -*- coding:UTF-8 -*-
from rest_framework import serializers

from . import models


class FirstClassSerializer(serializers.ModelSerializer):

    class Meta:
        model=models.FirstClass
        fields='__all__'


class SecondClassSerializer(serializers.ModelSerializer):

    class Meta:
        model=models.SecondClass
        fields='__all__'


class FirstPropetySerializer(serializers.ModelSerializer):

    class Meta:
        model=models.FirstProperty
        fields='__all__'

class SecondPropetySerializer(serializers.ModelSerializer):

    class Meta:
        model=models.SecondProperty
        fields='__all__'