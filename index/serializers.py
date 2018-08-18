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
        fields = ('store_image',)


class ApplicationSerializer(serializers.ModelSerializer):
    store_images=StoreImageSerializer(many=True)
    status_name = serializers.ReadOnlyField(source='get_application_status_display')
    active_code = serializers.ReadOnlyField(source='codewarehouse.code')

    class Meta:
        model = models.Application
        fields = '__all__'

    def create(self, validated_data):
        store_images_list = validated_data.pop('store_images')
        application = models.Application.objects.create(**validated_data)

        for store_image in store_images_list:
            models.StoreImage.objects.create(**store_image,application=application)

        return application


class GoodTrackSerializer(serializers.ModelSerializer):
    master_graph = serializers.SerializerMethodField()
    store_id = serializers.ReadOnlyField(source='good.store.id')
    min_price = serializers.ReadOnlyField(source='good.min_price')

    class Meta:
        model = models.GoodTrack
        exclude = ('user',)

    def create(self, validated_data):
        instance,created = self.Meta.model.objects.update_or_create(defaults=validated_data,
                                                                    user=validated_data['user'],
                                                                    good=validated_data['good'],
                                                                    date=validated_data['date'])
        return instance

    def get_master_graph(self,obj):
        if obj.good.master_map:
            return obj.good.master_map
        else:
            return obj.good.master_graphs[0]





