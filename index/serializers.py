# -*- coding:UTF-8 -*-
from rest_framework import serializers
from . import models

class BannerSerializer(serializers.ModelSerializer):

    class Meta:
        model=models.Banner
        fields='__all__'


class RecruitSerializer(serializers.ModelSerializer):

    class Meta:
        model=models.RecruitMerchant
        fields = '__all__'