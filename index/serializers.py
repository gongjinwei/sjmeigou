# -*- coding:UTF-8 -*-
from rest_framework import serializers
from . import models


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Banner
        fields = '__all__'


class RecruitSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RecruitMerchant
        fields = '__all__'


class StoreImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StoreImage
        fields = '__all__'


class ApplicationSerializer(serializers.ModelSerializer):
    store_images=StoreImageSerializer(many=True)

    class Meta:
        model = models.Application
        fields = '__all__'

    def create(self, validated_data):
        store_images_list = validated_data.pop('store_images')
        application = models.Application.objects.create(**validated_data)

        for store_image in store_images_list:
            models.StoreImage.objects.create(store_image=store_image,application=application)

        return application
