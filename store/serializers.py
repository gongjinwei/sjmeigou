# -*- coding:UTF-8 -*-
import datetime,random
from itertools import groupby
from rest_framework import serializers


from django.db.models import Avg,Count,Sum,Max,Min

from geopy.distance import VincentyDistance

from . import models
from order.models import CommentContent, Coupon, StoreActivity,SkuOrder
from goods.models import GoodDetail
from order.serializers import StoreOrderSerializer


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
                  'receive_address', 'longitude', 'latitude', 'store_phone', 'store_images', 'take_off','profile')


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
        fields = ('sku','num','color','price','size','good_title','id')


class StoreMessageSerializer(serializers.ModelSerializer):
    score_avg = serializers.SerializerMethodField()
    coupons = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()
    had_been_favored=serializers.SerializerMethodField()
    has_bargain = serializers.SerializerMethodField()

    class Meta:
        model = models.Stores
        fields = ('logo', 'name', 'take_off', 'activities', 'score_avg', 'coupons','receive_address','had_been_favored','has_bargain')

    def get_score_avg(self, obj):
        orders = obj.store_orders.all()
        comments = CommentContent.objects.filter(sku_order__store_order__in=orders)
        return comments.aggregate(Avg('score')).get('score__avg', 0.0)

    def get_has_bargain(self,obj):
        now =datetime.datetime.now()
        return obj.bargain_activities.filter(from_time__lte=now,to_time__gte=now,activity_stock__gt=0).exists()

    def get_coupons(self, obj):
        today = datetime.date.today()
        coupon = Coupon.objects.filter(store=obj, date_from__lte=today, date_to__gte=today, available_num__gt=0)
        return [cou.act_name for cou in coupon]

    def get_activities(self, obj):
        now = datetime.datetime.now()
        valid_activities = StoreActivity.objects.filter(store=obj, datetime_from__lte=now, datetime_to__gte=now,
                                                        state=0)

        return [activity.act_name for activity in valid_activities]

    def get_had_been_favored(self,obj):
        request= self.context.get('request',None)
        if request and hasattr(request,'user') and request.user.is_authenticated and models.StoreFavorites.objects.filter(user=request.user,store=obj).exists():
            return True
        else:
            return False


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


class StoreFavoritesSerializer(serializers.ModelSerializer):
    store_name = serializers.ReadOnlyField(source='store.name')
    store_logo = serializers.ReadOnlyField(source='store.logo')

    class Meta:
        model = models.StoreFavorites
        exclude = ('user',)

    def create(self, validated_data):
        instance,created=self.Meta.model.objects.get_or_create(**validated_data)
        return instance


class GoodFavoritesSerializer(serializers.ModelSerializer):
    title = serializers.ReadOnlyField(source='good.title')
    master_graph = serializers.SerializerMethodField()
    min_price = serializers.ReadOnlyField(source='good.min_price')
    favorites_num = serializers.SerializerMethodField()
    store_id = serializers.ReadOnlyField(source='good.store.id')

    class Meta:
        model = models.GoodFavorites
        exclude=('user',)

    def get_master_graph(self,obj):
        if obj.good.master_map:
            return obj.good.master_map
        else:
            return obj.good.master_graphs[0]

    def get_favorites_num(self,obj):
        return models.GoodFavorites.objects.filter(good=obj.good).aggregate(Count('user'))['user__count']

    def create(self, validated_data):
        instance,created=self.Meta.model.objects.get_or_create(**validated_data)
        return instance


class HistoryDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField()


class BargainActivitySerializer(serializers.ModelSerializer):
    color_pic = serializers.ReadOnlyField(source='sku.color.color_pic')
    good_id = serializers.ReadOnlyField(source='sku.color.good_detail.id')
    color_name = serializers.ReadOnlyField(source='sku.color.color_name')
    size_name = serializers.ReadOnlyField(source='sku.size.size_name')
    cut_price_from = serializers.FloatField(write_only=True)
    cut_price_to = serializers.FloatField(write_only=True)
    my_bargain = serializers.SerializerMethodField()
    poster_url = serializers.ReadOnlyField(source='poster.image.url')
    participator_nums = serializers.SerializerMethodField()
    paid_info = serializers.SerializerMethodField()


    class Meta:
        model = models.BargainActivity
        fields = '__all__'

    def get_my_bargain(self,obj):
        request = self.context.get('request',None)
        if request and hasattr(request,'user') and request.user.is_authenticated:
            if models.UserBargain.objects.filter(user=request.user,activity=obj).exists():
                return models.UserBargain.objects.get(user=request.user,activity=obj).id

    def get_participator_nums(self,obj):
        return models.HelpCutPrice.objects.filter(user_bargain__activity=obj).aggregate(joiners=Count('userId'))['joiners']

    def get_paid_info(self,obj):
        paid_activities=models.UserBargain.objects.filter(activity=obj,had_paid=True)
        paid_num=paid_activities.aggregate(joiners=Count('userId'))['joiners']
        max_paid = paid_activities.aggregate(max_p=Max('paid_money'))['max_p']
        min_paid = paid_activities.aggregate(min_p=Min('paid_money'))['min_p']
        avg_paid = paid_activities.aggregate(ave_p=Avg('paid_money'))['avg_p']

        return {'paid_nums':paid_num,'max_paid':max_paid,'min_paid':min_paid,'avg_paid':avg_paid}



class HelpCutPriceSerializer(serializers.ModelSerializer):
    avatarUrl = serializers.ReadOnlyField(source='userId.avatarUrl')
    nickName = serializers.ReadOnlyField(source='userId.nickName')

    class Meta:
        model = models.HelpCutPrice
        exclude=('userId',)


class UserBargainSerializer(serializers.ModelSerializer):
    activity = serializers.PrimaryKeyRelatedField(queryset=models.BargainActivity.objects.filter(from_time__lte=datetime.datetime.now(),to_time__gte=datetime.datetime.now(),state=1,activity_stock__gt=0))
    help_cuts = serializers.SerializerMethodField()
    cut_num = serializers.SerializerMethodField()
    cut_price_all= serializers.SerializerMethodField()
    size_name = serializers.ReadOnlyField(source='activity.sku.size.size_name')
    color_name=serializers.ReadOnlyField(source='activity.sku.color.color_name')
    sharer_avatar_url = serializers.ReadOnlyField(source='user.userinfo.avatarUrl')
    sharer_nick_name = serializers.ReadOnlyField(source='user.userinfo.nickName')
    is_sharer = serializers.SerializerMethodField()
    activity_data = serializers.SerializerMethodField()

    class Meta:
        model = models.UserBargain
        fields='__all__'

    def get_help_cuts(self,obj):
        queryset= obj.help_cuts.all()[:10]
        return HelpCutPriceSerializer(queryset,many=True).data

    def get_cut_num(self,obj):
        return len(obj.help_cuts.all())

    def get_cut_price_all(self,obj):
        queryset=obj.help_cuts.all().aggregate(cut_sum=Sum('cut_price'))
        return queryset['cut_sum']

    def get_is_sharer(self,obj):
        request=self.context.get('request',None)
        user_id = request.query_params.get('userId',None) if request else None
        if user_id:
            return obj.user.userinfo.id == user_id
        elif request and hasattr(request,'user') and request.user.is_authenticated:
            return obj.user == request.user
        else:
            return False

    def get_activity_data(self,obj):
        return BargainActivitySerializer(obj.activity,context=self.context).data


class BargainBalanceSerializer(serializers.Serializer):
    price = serializers.FloatField(help_text='当前价格,用于验证')


class BargainOrderSerializer(serializers.ModelSerializer):
    store_order = StoreOrderSerializer()

    class Meta:
        model = models.BargainOrder
        fields = '__all__'

    def create(self, validated_data):
        store_order_data = validated_data.pop('store_order')
        store_order=StoreOrderSerializer().create(store_order_data)
        validated_data['store_order']=store_order
        return super().create(validated_data)


class SharingReduceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SharingReduceActivity
        fields = '__all__'

    def create(self, validated_data):
        instance,created=self.Meta.model.objects.update_or_create(defaults=validated_data,store=validated_data['store'])
        return instance


class JoinSharingReduceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.JoinSharingReduce
        fields = '__all__'

    def create(self, validated_data):
        instance,created=self.Meta.model.objects.get_or_create(defaults=validated_data,**validated_data)
        if not created:
            instance.sharing_times +=1
            instance.has_paid=False
            instance.save()
        return instance