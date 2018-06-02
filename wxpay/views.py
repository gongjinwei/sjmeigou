import time, json
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from rest_framework.views import Response, status
from rest_framework.permissions import AllowAny
from register.models import UserInfo

from register import viewset

from weixin.pay import WeixinPay

from . import serializers
from register.views import CustomerXMLRender,CustomerXMLParser

# Create your views here.
mch_id = getattr(settings, "WEIXIN_MCH_ID")
mch_key = getattr(settings, "WEIXIN_MCH_KEY")
notify_url = getattr(settings, "WEIXIN_NOTIFY_URL")
mch_key_file = getattr(settings, "WEIXIN_MCH_KEY_FILE")
mch_cert_file = getattr(settings, "WEIXIN_MCH_CERT_FILE")
app_id = getattr(settings, "APPID")
app_secret = getattr(settings, "APPSECRET")


weixinpay = WeixinPay(app_id, mch_id, mch_key, notify_url)


class UnifiedOrderView(viewset.CreateOnlyViewSet):
    serializer_class = serializers.UnifiedOrderSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        userId = serializer.validated_data.pop('userId')
        if UserInfo.objects.filter(id=userId).exists():
            user = UserInfo.objects.get(pk=userId)
            res = weixinpay.unified_order(trade_type="JSAPI", openid=user.openId, **serializer.validated_data)
            if res.get('return_code') == "SUCCESS":
                package = res.get('prepay_id')
                data = {
                    "appId": weixinpay.app_id,
                    "timeStamp": str(int(time.time())),
                    "nonceStr": weixinpay.nonce_str,
                    "package": "prepay_id=%s" % package,
                    "signType": "MD5"
                }
                data.update(paySign=weixinpay.sign(data))
                return Response(data)
            else:
                return Response(res.get('return_msg'))
        else:
            return Response('用户不存在')


class NotifyOrderView(viewset.CreateOnlyViewSet):
    serializer_class = serializers.NotifyOrderSerializer
    permission_classes = (AllowAny,)
    renderer_classes = (CustomerXMLRender,)
    parser_classes = (CustomerXMLParser,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"return_code":"SUCCESS","return_msg":"OK"})


