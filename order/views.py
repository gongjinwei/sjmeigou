from rest_framework.views import Response,status
from rest_framework.viewsets import ModelViewSet


# Create your views here.

from . import serializers,models
from tools.permissions import MerchantOrReadOnlyPermission


class ShoppingCarView(ModelViewSet):
    serializer_class = serializers.ShoppingCarItemSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            queryset=models.ShoppingCarItem.objects.filter(user=self.request.user)
        else:
            return models.ShoppingCarItem.objects.none()

        return queryset

    def perform_create(self, serializer):
        price_added=serializer.validated_data['sku'].price
        serializer.save(user=self.request.user,price_of_added=price_added)


class CouponView(ModelViewSet):
    serializer_class = serializers.CouponSerializer
    permission_classes = (MerchantOrReadOnlyPermission,)

    def get_queryset(self):
        store_id = self.request.query_params.get('store','0')
        try:
            store_id=int(store_id)
        except ValueError:
            return models.Coupon.objects.none()

        return models.Coupon.objects.filter(store_id=store_id)

    def perform_create(self, serializer):
        serializer.save(store=self.request.user.stores)


