import hashlib

from django.conf import settings
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import Response, status
from rest_framework.permissions import AllowAny

# Create your views here.
from . import models, serializers
from dianwoda import DianWoDa

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

        sig = serializer.validated_data.pop('sig')
        my_sig = sign(serializer.validated_data)
        if sig == my_sig:
            self.perform_create(serializer)
            return Response({'success': True}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errmsg': '签名不一致%s' % sig})
