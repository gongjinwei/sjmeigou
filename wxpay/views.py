import time, copy
from django.conf import settings
from rest_framework.views import Response
from rest_framework.permissions import AllowAny
from register.models import UserInfo
from decimal import Decimal

from tools import viewset

from weixin.pay import WeixinPay

from . import serializers,models
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


class NotifyOrderView(viewset.CreateOnlyViewSet):
    serializer_class = serializers.NotifyOrderSerializer
    queryset = models.NotifyOrderModel.objects.all()
    permission_classes = (AllowAny,)
    renderer_classes = (CustomerXMLRender,)
    parser_classes = (CustomerXMLParser,)

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data=copy.copy(serializer.validated_data)
        received_sign=data.pop('sign','')
        sign=weixinpay.sign(data)
        if received_sign==sign:
            self.perform_create(serializer)
            return Response({"return_code":"SUCCESS","return_msg":"OK"})
        else:
            return Response({"return_code":"False","return_msg":"sign error"})


