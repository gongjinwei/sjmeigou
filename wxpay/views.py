from django.shortcuts import render
from django.conf import settings
from rest_framework.views import Response,status
from rest_framework.permissions import AllowAny

from register import viewset

from weixin.pay import WeixinPay

from . import serializers

# Create your views here.
mch_id = getattr(settings,"WEIXIN_MCH_ID")
mch_key = getattr(settings,"WEIXIN_MCH_KEY")
notify_url = getattr(settings,"WEIXIN_NOTIFY_URL")
mch_key_file = getattr(settings,"WEIXIN_MCH_KEY_FILE")
mch_cert_file = getattr(settings,"WEIXIN_MCH_CERT_FILE")
app_id = getattr(settings,"APPID")
app_secret = getattr(settings,"APPSECRET")


class UnifiedOrderView(viewset.CreateOnlyViewSet):
    serializer_class = serializers.UnifiedOrderSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer=self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        weixinpay=WeixinPay(app_id,mch_id,mch_key,notify_url)
        res=weixinpay.unified_order(**serializer.validated_data)

        return Response(res)


class NotifyOrderView(viewset.CreateOnlyViewSet):
    serializer_class = serializers.NotifyOrderSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        return Response('hello')