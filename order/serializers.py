# -*- coding:UTF-8 -*-
import datetime
from rest_framework import serializers

from django.db.models import F

from . import models
from store.models import Stores

from goods.models import SKU, GoodDeliver
from tools.contrib import get_deliver_pay
from platforms.models import DeliveryReason


class ShoppingCarItemSerializer(serializers.ModelSerializer):
    title = serializers.ReadOnlyField(source='sku.color.good_detail.title')
    price = serializers.ReadOnlyField(source='sku.price')
    color = serializers.ReadOnlyField(source='sku.color.color_name')
    color_pic = serializers.ReadOnlyField(source='sku.color.color_pic')
    stock = serializers.ReadOnlyField(source='sku.stock')
    size = serializers.ReadOnlyField(source='sku.size.size_name')
    good_id = serializers.ReadOnlyField(source='sku.color.good_detail.id')
    store = serializers.IntegerField(write_only=True)

    class Meta:
        model = models.ShoppingCarItem
        exclude = ('shopping_car',)

    def create(self, validated_data):
        ModelClass = self.Meta.model
        num = validated_data.get('num')
        price_of_added = validated_data.get('price_of_added')
        total_money = validated_data.get('total_money')
        store_id = validated_data.pop('store')
        store = Stores.objects.get(pk=store_id)
        user = validated_data.pop('user')
        shopping_car, creating = models.ShoppingCar.objects.get_or_create(defaults={'user': user, 'store': store},
                                                                          user=user, store=store)

        validated_data.update({"shopping_car": shopping_car})
        instance, created = ModelClass.objects.get_or_create(defaults=validated_data, sku=validated_data['sku'],
                                                             shopping_car=validated_data['shopping_car'])
        if not created:
            ModelClass.objects.filter(pk=instance.id).update(num=F('num') + num,
                                                             total_money=F('total_money') + total_money,
                                                             price_of_added=price_of_added)
        return instance


class ShoppingCarSerializer(serializers.ModelSerializer):
    items = ShoppingCarItemSerializer(many=True, read_only=True)
    store_name = serializers.ReadOnlyField(source='store.info.store_name')
    store_logo = serializers.ReadOnlyField(source='store.logo')
    coupons = serializers.SerializerMethodField()
    store_activities = serializers.SerializerMethodField()

    def get_store_activities(self, obj):
        now = datetime.datetime.now()
        # 取出所有活动
        activities = models.StoreActivity.objects.filter(store=obj.store, state=0, datetime_to__gte=now,
                                                         datetime_from__lte=now)
        # 取出购车车中数量总金额与数量
        car_items = models.ShoppingCarItem.objects.filter(shopping_car=obj)

        ret = []
        for activity in activities:
            car_item = car_items

            if activity.select_all == False:
                select_goods = activity.selected_goods.values_list('good', flat=True)
                car_item = car_item.filter(sku__color__good_detail__in=select_goods)
            items_num = sum([t.num for t in car_item])
            items_money = sum([t.total_money for t in car_item])

            x, y = activity.algorithm(items_num, items_money)
            ret.append({'id': activity.id, 'activity': x, 'reduction_money': y, 'item_num': items_num,
                        'items_money': items_money})

        # 返回最优惠活动
        if ret:
            ret_max = max(ret, key=lambda x: x.get('reduction_money', 0))

            return ret_max

        return ret

    def get_coupons(self, obj):
        today = datetime.date.today()
        return models.Coupon.objects.filter(store=obj.store, date_to__gte=today, date_from__lte=today,
                                            available_num__gt=0).values()

    class Meta:
        model = models.ShoppingCar
        fields = '__all__'


def check_discount(value):
    if value % 5 != 0:
        raise serializers.ValidationError('折扣面额必须是5的倍数')


class CouponSerializer(serializers.ModelSerializer):
    discount = serializers.IntegerField(validators=[check_discount])

    class Meta:
        model = models.Coupon
        fields = '__all__'


class GetCouponSerializer(serializers.ModelSerializer):
    date_from = serializers.ReadOnlyField(source='coupon.date_from')
    date_to = serializers.ReadOnlyField(source='coupon.date_to')
    discount = serializers.ReadOnlyField(source='coupon.discount')
    threshold_count = serializers.ReadOnlyField(source='coupon.threshold_count')
    store_name = serializers.ReadOnlyField(source='coupon.store.info.store_name')
    logo = serializers.ReadOnlyField(source='coupon.store.logo')
    store_id = serializers.ReadOnlyField(source='coupon.store.id')
    name = serializers.ReadOnlyField(source='coupon.name')

    class Meta:
        model = models.GetCoupon
        fields = '__all__'

    def create(self, validated_data):
        instance, created = models.GetCoupon.objects.get_or_create(defaults=validated_data, user=validated_data['user'],
                                                                   coupon=validated_data['coupon'])
        models.GetCoupon.objects.filter(pk=instance.id).update(has_num=F('has_num') + 1)
        # 记录领取的行为
        record = models.CouponRecords()
        record.get_coupon = instance
        record.action = 0
        record.save()
        return instance


class StoreActivitySelectedSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StoreActivitySelected
        fields = '__all__'


class StoreActivitySerializer(serializers.ModelSerializer):
    selected_goods = StoreActivitySelectedSerializer(many=True, required=False)

    class Meta:
        model = models.StoreActivity
        fields = '__all__'

    def create(self, validated_data):
        selected_data = validated_data.pop('selected_goods', [])
        activity = self.Meta.model.objects.create(**validated_data)
        for data in selected_data:
            models.StoreActivitySelected.objects.create(activity=activity, **data)
        return activity


class JoinActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.JoinActivity
        fields = '__all__'


class BalanceSkuSerializer(serializers.Serializer):
    sku = serializers.PrimaryKeyRelatedField(queryset=SKU.objects.all())
    num = serializers.IntegerField()


class BalanceListSerializer(serializers.Serializer):
    store = serializers.PrimaryKeyRelatedField(queryset=Stores.objects.all())
    skus = BalanceSkuSerializer(many=True)

    def create(self, validated_data):
        store = validated_data.get('store')
        return store


class BalanceSerializer(serializers.Serializer):
    stores = BalanceListSerializer(many=True)

    def create(self, validated_data):
        stores = validated_data.get('stores')
        return stores


class SkuDetailSerializer(serializers.ModelSerializer):
    title = serializers.ReadOnlyField(source='color.good_detail.title')
    color_name = serializers.ReadOnlyField(source='color.color_name')
    color_pic = serializers.ReadOnlyField(source='color.color_pic')
    size_name = serializers.ReadOnlyField(source='size.size_name')
    good_id = serializers.ReadOnlyField(source='color.good_detail.id')
    deliver_services = serializers.SerializerMethodField()

    def get_deliver_services(self, obj):
        delivers = GoodDeliver.objects.filter(good_detail=obj.color.good_detail)
        ret = []
        for de in delivers:
            ret.append({'id': de.id, 'deliver': de.server.name, 'server': de.server.id,
                        'server_name': de.server.deliver_server.server_name})
        return ret

    class Meta:
        model = SKU
        fields = (
            'price', 'stock', 'size_name', 'color_name', 'title', 'color_pic', 'id', 'good_id', 'deliver_services')


class ReceiveAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReceiveAddress
        fields = '__all__'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        if request:
            store_ids = request.query_params.get('stores', '')
            if store_ids:
                ret['deliver_pays'] = []
                for store_id in store_ids.split('|'):
                    try:
                        store_id = int(store_id)
                    except ValueError:
                        continue
                    if Stores.objects.filter(pk=store_id).exists():
                        store = Stores.objects.get(pk=store_id)
                        destination = '%s,%s' % (ret.get('longitude'), ret.get('latitude'))
                        origin = "%s,%s" % (store.longitude, store.latitude)
                        delivery, store_pay, deliver_distance = get_deliver_pay(origin, destination)
                        ret['deliver_pays'].append(
                            {"deliver_pay": delivery, 'store_id': store_id, 'deliver_distance': deliver_distance})
        return ret


class SkuOrderSerializer(serializers.ModelSerializer):
    title = serializers.ReadOnlyField(source='sku.color.good_detail.title')
    size = serializers.ReadOnlyField(source='sku.size.size_name')
    color = serializers.ReadOnlyField(source='sku.color.color_name')
    color_pic = serializers.ReadOnlyField(source='sku.color.color_pic')
    price = serializers.ReadOnlyField(source='sku.price')

    class Meta:
        model = models.SkuOrder
        fields = ('sku', 'num', 'title', 'color', 'size', 'price', 'color_pic')


class DwdOrderInfoSerializer(serializers.ModelSerializer):
    status_name = serializers.ReadOnlyField(source='get_dwd_status_display')

    class Meta:
        model = models.DwdOrder
        fields = ('dwd_status', 'status_name')


class StoreOrderSerializer(serializers.ModelSerializer):
    sku_orders = SkuOrderSerializer(many=True, required=False)
    logo = serializers.ReadOnlyField(source='store.logo')
    store_name = serializers.ReadOnlyField(source='store.name')
    dwd_order_info = DwdOrderInfoSerializer(read_only=True)
    delivery_name = serializers.ReadOnlyField(source='deliver_server.server.name')
    refund = serializers.SerializerMethodField()

    class Meta:
        model = models.StoreOrder
        fields = '__all__'

    def create(self, validated_data):
        sku_data = validated_data.pop('sku_orders', [])
        store_order = self.Meta.model.objects.create(**validated_data)
        for sku in sku_data:
            models.SkuOrder.objects.create(store_order=store_order, **sku)
        return store_order

    def get_refund(self,obj):
        refunds= models.OrderRefund.objects.filter(result=1,store_order=obj)
        if refunds.exists():
            return refunds.values('id','state','get_state_display')


class UnifyOrderSerializer(serializers.ModelSerializer):
    store_orders = StoreOrderSerializer(many=True)

    class Meta:
        model = models.UnifyOrder
        fields = '__all__'

    def create(self, validated_data):
        store_data = validated_data.pop('store_orders', [])
        unify_order = self.Meta.model.objects.create(**validated_data)
        for store in store_data:
            sku_data = store.pop('sku_orders', [])
            store_order = models.StoreOrder.objects.create(unify_order=unify_order, **store)
            for sku in sku_data:
                models.SkuOrder.objects.create(store_order=store_order, **sku)
        return unify_order


class InitiatePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InitiatePayment
        fields = '__all__'


state_change = [1, 2, 3, 7]


class StoreStateChangeSerializer(serializers.Serializer):
    store_order = serializers.PrimaryKeyRelatedField(queryset=models.StoreOrder.objects.filter(state__in=state_change))
    op = serializers.ChoiceField(choices=((1, '确认收货'), (2, '取消订单'), (3, '同意退款')))


class StorePriceChangeSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=30, decimal_places=2)


class OrderTradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrderTrade
        fields = '__all__'


class InitialTradeSerializer(serializers.Serializer):
    order = serializers.PrimaryKeyRelatedField(queryset=models.StoreOrder.objects.filter(state=1))


class DwdOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DwdOrder
        fields = '__all__'


class DwdRiderSerializer(serializers.ModelSerializer):
    status_name = serializers.ReadOnlyField(source='get_dwd_status_display')

    class Meta:
        model = models.DwdOrder
        fields = ('dwd_status', 'rider_name', 'rider_mobile', 'status_name')


class CommentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CommentImage
        fields = ('id', 'image')


def check_image_id(value):
    if not models.CommentImage.objects.filter(pk=value).exists():
        raise serializers.ValidationError('id不存在')


class ImageCommentSerializer(serializers.Serializer):
    image = serializers.IntegerField(validators=[check_image_id])


class DwdOrderCommentSerializer(serializers.ModelSerializer):
    satisfied_reasons=serializers.PrimaryKeyRelatedField(queryset=DeliveryReason.objects.all(),many=True)

    class Meta:
        model = models.DwdOrderComment
        fields = '__all__'

    def create(self, validated_data):
        sats = validated_data.pop('satisfied_reasons',[])
        instance = self.Meta.model.objects.create(**validated_data)
        for sat in sats:
            instance.satisfied_reasons.add(sat)
        return instance


class CommentContentSerializer(serializers.ModelSerializer):
    comment_images = ImageCommentSerializer(many=True,required=False)
    dwd_order_comment = DwdOrderCommentSerializer(required=False)

    class Meta:
        model = models.CommentContent
        fields = '__all__'

    def create(self, validated_data):
        order = validated_data.pop('order')
        image_data = validated_data.pop('comment_images',[])
        dwd_order_comment_data=validated_data.pop('dwd_order_comment',None)
        image_ids = [image['image'] for image in image_data]
        request = self.context.get('request')
        user = request.user
        op = request.query_params.get('op', '')
        order_comment, created = models.OrderComment.objects.get_or_create(defaults={"order": order}, order=order)
        if order.user == user and op != 'backend':
            validated_data.update({
                "order_comment": order_comment,
                "is_buyer_comment": True
            })

            if order_comment.state == 0:
                order_comment.state = 1
            elif order_comment.state == 2:
                order_comment.state = 3
                order.state = 5
        else:
            validated_data.update({
                "order_comment": order_comment,
                "is_buyer_comment": False
            })

            if order_comment.state == 0:
                order_comment.state = 2
            elif order_comment.state == 1:
                order_comment.state = 3
                order.state = 5
        order.save()
        order_comment.save()
        instance, created = models.CommentContent.objects.get_or_create(defaults=validated_data,
                                                                        order_comment=validated_data['order_comment'],
                                                                        is_buyer_comment=validated_data[
                                                                            'is_buyer_comment'])

        models.CommentImage.objects.filter(store_order=order, id__in=image_ids).update(comment_content=instance)

        # 判断是否有点我达订单且妥投
        if dwd_order_comment_data and models.DwdOrder.objects.filter(store_order=order,dwd_status=100).exists():
            dwd_order = models.DwdOrder.objects.get(store_order=order,dwd_status=100)
            dwd_order_comment_data.update({"has_comment":True,"dwd_order":dwd_order})
            DwdOrderCommentSerializer().create(dwd_order_comment_data)

        return instance


class ChangeDwdArriveTimeSerializer(serializers.Serializer):
    arrive_time=serializers.DateTimeField()
    dwd_order = serializers.PrimaryKeyRelatedField(queryset=models.DwdOrder.objects.filter(user_arrive_time__isnull=True))


class OrderRefundSerializer(serializers.ModelSerializer):
    refund_images = ImageCommentSerializer(many=True,required=False)
    state_name = serializers.ReadOnlyField(source='get_state_display')

    class Meta:
        model = models.OrderRefund
        fields = '__all__'

    def create(self, validated_data):
        order = validated_data.get('store_order')
        image_data = validated_data.pop('refund_images',[])
        image_ids = [image['image'] for image in image_data]
        order_refund = models.OrderRefund.objects.create(**validated_data)
        models.CommentImage.objects.filter(store_order=order, id__in=image_ids).update(refund=order_refund)
        return order_refund


class OrderReviewSerializer(serializers.ModelSerializer):
    review_images = ImageCommentSerializer(many=True,required=False)

    class Meta:
        model = models.OrderReview
        fields = '__all__'

    def create(self, validated_data):
        order = validated_data.get('order')
        image_data = validated_data.pop('review_images',[])
        image_ids = [image['image'] for image in image_data]
        order_review = models.OrderReview.objects.create(**validated_data)
        models.CommentImage.objects.filter(store_order=order, id__in=image_ids).update(review_content=order_review)
        return order_review
