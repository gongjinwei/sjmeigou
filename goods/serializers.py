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


class SizeDescSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SizeDesc
        exclude=("size_group",)


class SizeGroupSerializer(serializers.ModelSerializer):
    sizes = SizeDescSerializer(many=True, read_only=True)

    class Meta:
        model = models.SizeGroup
        exclude=('second_class',)


class SizeGroupClassSerializer(serializers.ModelSerializer):
    size_group=SizeGroupSerializer(read_only=True)

    class Meta:
        model = models.SizeGroupClass
        fields = '__all__'


class ThirdClassSerializer(serializers.ModelSerializer):
    size_group_classes = SizeGroupClassSerializer(many=True, read_only=True)

    class Meta:
        model = models.ThirdClass
        fields = ('id', 'third_class_name','size_group_classes')


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


class ItemsGroupDescSerializer(serializers.ModelSerializer):
    items=serializers.JSONField()

    class Meta:
        model=models.ItemsGroupDesc
        fields='__all__'


class SKUSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.SKU
        exclude = ('good_detail',)


class AfterSaleServicesSerializer(serializers.ModelSerializer):
    server_name = serializers.ReadOnlyField(source='get_server_display')

    class Meta:
        model=models.AfterSaleServices
        fields = ('server', 'server_name')


class DeliverServicesSerializer(serializers.ModelSerializer):
    server_name=serializers.ReadOnlyField(source='get_server_display')

    class Meta:
        model=models.DeliverServices
        fields=('server','server_name')


class GoodDetailSerializer(serializers.ModelSerializer):
    class_name=serializers.SerializerMethodField()
    relate_desc=serializers.ReadOnlyField(source='item_desc.items')
    params=serializers.JSONField()
    master_graphs=serializers.JSONField()
    sku=SKUSerializer(many=True)
    after_sale_services=AfterSaleServicesSerializer(many=True)
    delivers=DeliverServicesSerializer(many=True)
    size_name=serializers.ReadOnlyField(source='size.size_name')

    def get_class_name(self,obj):
        return "%s>%s" % (obj.third_class.second_class.second_class_name,obj.third_class.third_class_name)

    class Meta:
        model = models.GoodDetail
        fields = '__all__'

    def create(self, validated_data):
        skus=validated_data.pop('sku')
        after_sale_services=validated_data.pop('after_sale_services')
        delivers=validated_data.pop('delivers')

        instance=models.GoodDetail.objects.create(**validated_data)

        for service in after_sale_services:
            models.AfterSaleServices.objects.create(good_detail=instance,**service)
        for deliver in delivers:
            models.DeliverServices.objects.create(good_detail=instance,**deliver)
        for sku in skus:
            models.SKU.objects.create(good_detail=instance,**sku)

        return instance
