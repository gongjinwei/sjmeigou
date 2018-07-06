import datetime

from django.db.models import F

from rest_framework.views import Response, status
from rest_framework.viewsets import ModelViewSet

# Create your views here.

from . import serializers, models
from tools.permissions import MerchantOrReadOnlyPermission
from tools.viewset import CreateListDeleteViewSet


class ShoppingCarView(ModelViewSet):
    serializer_class = serializers.ShoppingCarItemSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            queryset = models.ShoppingCarItem.objects.filter(user=self.request.user)
        else:
            return models.ShoppingCarItem.objects.none()

        return queryset

    def perform_create(self, serializer):
        price_added = serializer.validated_data['sku'].price
        serializer.save(user=self.request.user, price_of_added=price_added)


class CouponView(CreateListDeleteViewSet):
    serializer_class = serializers.CouponSerializer
    permission_classes = (MerchantOrReadOnlyPermission,)

    def get_queryset(self):
        store_id = self.request.query_params.get('store', '')
        today = datetime.date.today()
        try:
            store_id = int(store_id)
        except ValueError:
            return models.Coupon.objects.none()

        return models.Coupon.objects.filter(store_id=store_id, date_from__lte=today, date_to__gte=today,
                                            available_num__gt=0)

    def perform_create(self, serializer):
        serializer.save(store=self.request.user.stores)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.available_num=0
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetCouponView(ModelViewSet):
    serializer_class = serializers.GetCouponSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        coupon = serializer.validated_data['coupon']
        today = datetime.date.today()

        if coupon.date_from <= today and coupon.date_to >= today and coupon.available_num > 0:
            if models.GetCoupon.objects.filter(user=self.request.user,coupon=coupon).exists():
                user_coupon=models.GetCoupon.objects.filter(user=self.request.user,coupon=coupon)[0]
                if user_coupon.has_num>=coupon.limit_per_user:
                    return Response('你可领的券数超限',status=status.HTTP_400_BAD_REQUEST)
            self.perform_create(serializer)
            coupon.available_num=F('available_num')-1
            coupon.save()
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response('该券不可领取或可领取数量为0')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            queryset=models.GetCoupon.objects.filter(user=self.request.user)
        else:
            queryset=models.GetCoupon.objects.none()
        return queryset

