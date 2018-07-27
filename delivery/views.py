import hashlib, datetime

from django.conf import settings
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import Response, status
from rest_framework.permissions import AllowAny

# Create your views here.
from . import models, serializers
from order.models import DwdOrder

secret = getattr(settings, 'DWD_SECRET')


def sign(params):
    B = secret + ''.join(['%s%s' % (k, params[k]) for k in sorted(params.keys())]) + secret

    return hashlib.sha1(B.encode()).hexdigest().upper()


class OrderCallbackViewSets(ModelViewSet):
    serializer_class = serializers.OrderCallbackSerializer
    queryset = models.OrderCallback.objects.all()
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sig = serializer.validated_data.get('sig')
        sign_data = serializer.validated_data.copy()
        sign_data.pop('sig')
        my_sig = sign(sign_data)
        if sig == my_sig:
            store_order_id = serializer.validated_data['order_original_id']
            dwd_store_order, created = DwdOrder.objects.get_or_create(store_order_id=store_order_id)
            dwd_status = serializer.validated_data['order_status']
            data = {
                "dwd_status": dwd_status,
                'cancel_reason': serializer.validated_data.get('cancel_reason', None),
                'rider_name': serializer.validated_data.get('rider_name', None),
                'rider_code': serializer.validated_data.get('rider_code', None),
                'rider_mobile': serializer.validated_data.get('rider_mobile', None)
            }

            # 做相应订单状态变更
            if dwd_status == 15:
                dwd_store_order.store_order.state = 3
                dwd_store_order.store_order.save()

            if dwd_status == 100:
                arrive_time = serializer.validated_data.get('time_status_update')
                arrive_time= datetime.datetime.fromtimestamp(arrive_time/1000)
                data.update({
                    "arrive_time":arrive_time
                })

            if not created:
                # 状态码只允许改大
                if dwd_store_order.dwd_status and dwd_store_order.dwd_status < dwd_status:
                    dwd_store_order.__dict__.update(data)
                if dwd_store_order.dwd_status and dwd_store_order.dwd_status > dwd_status:
                    return Response({'success': False, 'errmsg': '状态错误'})
                elif not dwd_store_order.dwd_status:
                    dwd_store_order.__dict__.update(data)
            else:
                dwd_store_order.__dict__.update(data)
            dwd_store_order.save()
            self.perform_create(serializer)
            return Response({'success': True}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errmsg': '签名不一致%s' % sig})
