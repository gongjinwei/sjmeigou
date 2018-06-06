# -*- coding:UTF-8 -*-
from rest_framework import serializers
from . import models

class BannerSerializer(serializers.ModelSerializer):

    class Meta:
        model=models.Banner
        fields='__all__'


class SortTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model=models.SortType
        fields = '__all__'