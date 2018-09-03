# -*- coding:UTF-8 -*-
import datetime
from rest_framework import serializers
from order.models import Coupon,StoreActivity
from django.db.models import Q


from . import models
from platforms.serializers import DeliverServiceSerializer
from platforms.models import DeliverServices
from geopy.distance import VincentyDistance
from order.models import CommentContent
from store.models import GoodFavorites,SharingReduceActivity,BargainActivity
from order.serializers import CommentContentSerializer


class SecondClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SecondClass
        fields = ('second_class_name', 'id')


class FirstClassSerializer(serializers.ModelSerializer):
    second_classes = SecondClassSerializer(many=True, read_only=True)

    class Meta:
        model = models.FirstClass
        fields = ('second_classes', 'first_class_name','cover_path','id')


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
    delivers = serializers.SerializerMethodField()

    class Meta:
        model = models.FirstProperty
        fields = ('id', 'first_property_name', 'third_class', 'secondProperties','delivers')
        # fields=('id','first_property_name','third_class','third_class_name','second_class_name','secondProperties')

    def get_delivers(self,obj):
        serializer=DeliverServiceSerializer(DeliverServices.objects.all(),many=True)
        return serializer.data


class ItemsGroupDescSerializer(serializers.ModelSerializer):
    items=serializers.JSONField()

    class Meta:
        model=models.ItemsGroupDesc
        fields='__all__'


class SKUSerializer(serializers.ModelSerializer):
    size_name = serializers.ReadOnlyField(source='size.size_name')
    size_group_name = serializers.ReadOnlyField(source='size.size_group.group_name')
    id = serializers.IntegerField(required=False)

    class Meta:
        model=models.SKU
        exclude = ('color',)

    def create(self, validated_data):
        validated_data.pop('id',None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('id',None)
        return super().update(instance,validated_data)


class AfterSaleServicesSerializer(serializers.ModelSerializer):
    server_name = serializers.ReadOnlyField(source='get_server_display')
    id = serializers.IntegerField(required=False)

    class Meta:
        model=models.AfterSaleServices
        fields = ('server', 'server_name','id')

    def create(self, validated_data):
        validated_data.pop('id',None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('id',None)
        return super().update(instance,validated_data)


class GoodDeliverSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    deliver_name = serializers.ReadOnlyField(source='server.name')
    server_name = serializers.ReadOnlyField(source='server.deliver_server.name')

    class Meta:
        model = models.GoodDeliver
        fields = ('server','server_name','deliver_name','id')

    def create(self, validated_data):
        validated_data.pop('id',None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('id',None)
        return super().update(instance,validated_data)


class SKUColorSerializer(serializers.ModelSerializer):
    skus=SKUSerializer(many=True)
    id = serializers.IntegerField(required=False)

    class Meta:
        model = models.SKUColor
        exclude=('good_detail',)

    def create(self, validated_data):
        validated_data.pop('id', None)
        skus = validated_data.pop('skus')
        instance=models.SKUColor.objects.create(**validated_data)
        for sku in skus:
            models.SKU.objects.create(color=instance, **sku)

    def update(self, instance, validated_data):
        validated_data.pop('id',None)
        return super().update(instance,validated_data)


class CommentFirstSerializer(serializers.ModelSerializer):
    avatarUrl = serializers.ReadOnlyField(source='sku_order.store_order.user.userinfo.avatarUrl')
    comment_name = serializers.SerializerMethodField()

    class Meta:
        model = CommentContent
        fields = ('comment','avatarUrl','comment_name')

    def get_comment_name(self, obj):
        if obj.is_anonymous:
            return '匿名用户'
        else:
            return obj.sku_order.store_order.user.userinfo.nickName


class GoodDetailSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    class_name=serializers.SerializerMethodField()
    relate_desc=serializers.ReadOnlyField(source='item_desc.items')
    params=serializers.JSONField()
    master_graphs=serializers.JSONField()
    colors=SKUColorSerializer(many=True)
    after_sale_services=AfterSaleServicesSerializer(many=True)
    delivers=GoodDeliverSerializer(many=True)
    latest_comment = serializers.SerializerMethodField()
    had_been_favored=serializers.SerializerMethodField()
    sku_num = serializers.SerializerMethodField()
    good_share_activity=serializers.SerializerMethodField()
    good_bargain_activity = serializers.SerializerMethodField()

    def get_class_name(self,obj):
        return "%s>%s" % (obj.third_class.second_class.second_class_name,obj.third_class.third_class_name)

    class Meta:
        model = models.GoodDetail
        fields = '__all__'

    def create(self, validated_data):
        colors=validated_data.pop('colors')
        after_sale_services=validated_data.pop('after_sale_services')
        delivers=validated_data.pop('delivers')

        instance=models.GoodDetail.objects.create(**validated_data)

        for service in after_sale_services:
            models.AfterSaleServices.objects.create(good_detail=instance,**service)
        for deliver in delivers:
            models.GoodDeliver.objects.create(good_detail=instance,**deliver)
        for color_data in colors:
            skus=color_data.pop('skus')
            color=models.SKUColor.objects.create(good_detail=instance,**color_data)
            for sku in skus:
                models.SKU.objects.create(color=color,**sku)

        return instance

    def update(self, instance, validated_data):
        colors = validated_data.pop('colors')
        after_sale_services = validated_data.pop('after_sale_services')
        delivers = validated_data.pop('delivers')

        for service in after_sale_services:
            pk = service.get('id',None)
            if pk:
                models.AfterSaleServices.objects.filter(pk=pk).update(**service)
            else:
                models.AfterSaleServices.objects.create(good_detail=instance,**service)
        for deliver in delivers:
            pk = deliver.get('id', None)
            if pk:
                models.GoodDeliver.objects.filter(pk=pk).update(**deliver)
            else:
                models.GoodDeliver.objects.create(good_detail=instance,**deliver)

        for color_data in colors:
            skus = color_data.pop('skus')
            color_pk = color_data.get('id',None)
            if color_pk:
                models.SKUColor.objects.filter(pk=color_pk).update(**color_data)
            else:
                models.SKUColor.objects.create(**color_data)

            for sku in skus:
                sku_pk = sku.get('id',None)
                if sku_pk:
                    models.SKU.objects.filter(pk=sku_pk).update(**sku)
                else:
                    models.SKU.objects.create(**sku)
        return super().update(instance,validated_data)

    def get_latest_comment(self,obj):
        content = CommentContent.objects.filter(sku_order__sku__color__good_detail=obj)
        if content.exists():
            return CommentFirstSerializer(content.latest('comment_time')).data

    def get_had_been_favored(self,obj):
        request= self.context.get('request',None)
        if request and hasattr(request,'user') and request.user.is_authenticated and GoodFavorites.objects.filter(user=request.user,good=obj).exists():
            return True
        else:
            return False

    def get_sku_num(self,obj):
        return len(models.SKU.objects.filter(color__good_detail=obj))

    def get_good_share_activity(self,obj):
        activity = SharingReduceActivity.objects.filter(store=obj.store, is_ended=False)
        if activity.exists():
            return {'id':activity[0].id,'reduce_money':activity[0].reduce_money}

    def get_good_bargain_activity(self,obj):
        now=datetime.datetime.now()
        activity = BargainActivity.objects.filter(sku__color__good_detail=obj,from_time__lte=now,to_time__gte=now,state=1)
        if activity.exists():
            return activity.values('sku_id')


class GoodSearchSerializer(serializers.ModelSerializer):
    master_graph=serializers.SerializerMethodField()
    coupons = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()
    store_lat = serializers.ReadOnlyField(source='store.latitude')
    store_lng = serializers.ReadOnlyField(source='store.longitude')

    class Meta:
        model = models.GoodDetail
        fields = ('title','master_graph','min_price','coupons','activities','store','id','store_lng','store_lat')

    def to_representation(self, instance):
        ret=super().to_representation(instance)
        request = self.context.get('request')
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        if lat and lng:
            try:
                lat=float(lat)
                lng=float(lng)

                distance=round(VincentyDistance((lat, lng),(ret['store_lat'], ret['store_lng'])).kilometers, 1)

                ret.update({
                    "distance": distance
                })
            except ValueError:
                pass
        return ret

    def get_master_graph(self,obj):
        if obj.master_graphs:
            return obj.master_graphs[0]

    def get_coupons(self,obj):
        store = obj.store
        today = datetime.date.today()
        coupon = Coupon.objects.filter(store=store,date_from__lte=today,date_to__gte=today,available_num__gt=0)
        return [cou.act_name for cou in coupon]

    def get_activities(self,obj):
        store =obj.store
        now = datetime.datetime.now()
        valid_activities=StoreActivity.objects.filter(store=store,datetime_from__lte=now,datetime_to__gte=now,state=0)
        good_activities=valid_activities.filter(Q(select_all=True)|Q(selected_goods__good=obj))

        return [activity.act_name for activity in good_activities]


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SearchHistory
        fields = '__all__'
