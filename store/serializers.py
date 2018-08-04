# -*- coding:UTF-8 -*-
import datetime

from rest_framework import serializers

from django.db.models import Avg

from geopy.distance import VincentyDistance

from . import models
from order.models import CommentContent, Coupon, StoreActivity,OrderComment,SkuOrder
from goods.models import GoodDetail


class StoresSerializer(serializers.ModelSerializer):
    active_code = serializers.CharField(write_only=True)

    class Meta:
        model = models.Stores
        fields = '__all__'


class DepositSerializer(serializers.ModelSerializer):
    application = serializers.CharField(max_length=20, required=True)

    class Meta:
        model = models.Deposit
        fields = '__all__'


class StoreQRCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StoreQRCode
        fields = '__all__'


class StoreInfoSerializer(serializers.ModelSerializer):
    store_images = serializers.SerializerMethodField()

    def get_store_images(self, obj):
        return obj.info.store_images.values('store_image')

    class Meta:
        model = models.Stores
        fields = ('id', 'business_hour_from', 'business_hour_to', 'logo', 'active_state', 'create_time', 'name',
                  'receive_address', 'longitude', 'latitude', 'store_phone', 'store_images', 'take_off')


class EnterpriseQualificationSerializer(serializers.ModelSerializer):
    license_unit_name = serializers.ReadOnlyField(source='info.license_unit_name')
    license_legal_representative = serializers.ReadOnlyField(source='info.license_legal_representative')
    store_licence_pic = serializers.ReadOnlyField(source='info.store_licence_pic')

    class Meta:
        model = models.Stores
        fields = ('license_unit_name', 'license_legal_representative', 'store_licence_pic')


class GoodDetailSerializer(serializers.ModelSerializer):
    good_type_name = serializers.ReadOnlyField(source='good_type.name')
    master_graph = serializers.SerializerMethodField()

    class Meta:
        model = GoodDetail
        fields = ('id', 'title', 'good_type', 'create_time', 'min_price', 'state', 'good_type_name', 'master_graph')

    def get_master_graph(self, obj):
        if obj.master_graphs:
            return obj.master_graphs[0]


class GoodsTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GoodsType
        exclude = ('store_goods_type',)


class SkuOrderSerializer(serializers.ModelSerializer):
    color = serializers.ReadOnlyField(source='sku.color.color_name')
    price = serializers.ReadOnlyField(source='sku.price')
    size = serializers.ReadOnlyField(source='sku.size.size_name')
    good_title =serializers.ReadOnlyField(source='sku.color.good_detail.title')


    class Meta:
        model = SkuOrder
        fields = ('sku','num','color','price','size','good_title')


class StoreMessageSerializer(serializers.ModelSerializer):
    score_avg = serializers.SerializerMethodField()
    coupons = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()

    class Meta:
        model = models.Stores
        fields = ('logo', 'name', 'take_off', 'activities', 'score_avg', 'coupons','receive_address')

    def get_score_avg(self, obj):
        orders = obj.store_orders.all()
        comments = CommentContent.objects.filter(is_buyer_comment=True, order_comment__order__in=orders)
        return comments.aggregate(Avg('score')).get('score__avg', 0.0)

    def get_coupons(self, obj):
        today = datetime.date.today()
        coupon = Coupon.objects.filter(store=obj, date_from__lte=today, date_to__gte=today, available_num__gt=0)
        return [cou.act_name for cou in coupon]

    def get_activities(self, obj):
        now = datetime.datetime.now()
        valid_activities = StoreActivity.objects.filter(store=obj, datetime_from__lte=now, datetime_to__gte=now,
                                                        state=0)

        return [activity.act_name for activity in valid_activities]


class StoreGoodsTypeSerializer(serializers.ModelSerializer):
    good_types = GoodsTypeSerializer(many=True)

    class Meta:
        model = models.StoreGoodsType
        fields = '__all__'

    def create(self, validated_data):
        type_data = validated_data.pop('good_types')
        store_good_type, created = models.StoreGoodsType.objects.update_or_create(defaults=validated_data,
                                                                                  **validated_data)

        for data in type_data:
            data.update(store_goods_type=store_good_type)

            models.GoodsType.objects.update_or_create(defaults=data, order_num=data.get('order_num'),
                                                      store_goods_type=store_good_type)
        return store_good_type


class AddGoodsSerializer(serializers.Serializer):
    good_list = serializers.ListField(required=False)
    put_on_sale_list = serializers.ListField(required=False)


class StoreSearchSerializer(serializers.ModelSerializer):
    coupons = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()
    goods_recommend = serializers.SerializerMethodField()

    class Meta:
        model = models.Stores
        fields = (
        'name', 'logo', 'receive_address', 'latitude', 'longitude', 'coupons', 'activities', 'goods_recommend',
        'take_off', 'id')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        if lat and lng:
            try:
                lat = float(lat)
                lng = float(lng)
                distance = round(VincentyDistance((lat, lng), (ret['latitude'], ret['longitude'])).kilometers, 1)

                ret.update({
                    "distance": distance
                })
            except ValueError:
                pass
        return ret

    def get_coupons(self, obj):
        today = datetime.date.today()
        coupon = Coupon.objects.filter(store=obj, date_from__lte=today, date_to__gte=today, available_num__gt=0)
        return [cou.act_name for cou in coupon]

    def get_activities(self, obj):
        now = datetime.datetime.now()
        valid_activities = StoreActivity.objects.filter(store=obj, datetime_from__lte=now, datetime_to__gte=now,
                                                        state=0)

        return [activity.act_name for activity in valid_activities]

    def get_goods_recommend(self, obj):
        if obj.goods.values('title', 'master_graphs', 'min_price', 'id'):
            return obj.goods.values('title', 'master_graphs', 'min_price', 'id')[:3]


class CommentContentSerializer(serializers.ModelSerializer):
    comment_images =serializers.SerializerMethodField()
    comment_name = serializers.SerializerMethodField()
    sku_orders = serializers.SerializerMethodField()

    class Meta:
        model = CommentContent
        fields = ('id','comment_images','comment','score','comment_name','is_buyer_comment','comment_time','sku_orders')

    def get_comment_images(self,obj):
        images = obj.comment_images.all()
        return [image.image.url for image in images]

    def get_comment_name(self,obj):
        if obj.is_anonymous and obj.is_buyer_comment:
            return '匿名用户'
        elif obj.is_buyer_comment:
            return obj.order_comment.order.user.userinfo.nickName
        else:
            return obj.order_comment.order.store.user.userinfo.nickName

    def get_sku_orders(self,obj):
        skus = SkuOrder.objects.filter(store_order=obj.order_comment.order)
        return SkuOrderSerializer(skus,many=True).data


class OrderCommentSerializer(serializers.ModelSerializer):
    comment_contents = CommentContentSerializer(many=True,read_only=True)
    paid_time = serializers.ReadOnlyField(source='order.paid_time')

    class Meta:
        model = OrderComment
        fields ='__all__'


class StoreCommentSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField()

    class Meta:
        model = models.Stores
        fields = ('comments','name','logo','id')

    def get_comments(self,obj):
        com = OrderComment.objects.filter(order__store=obj)
        return OrderCommentSerializer(com,many=True).data