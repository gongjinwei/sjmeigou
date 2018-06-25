from rest_framework.views import Response, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser

from django.utils.crypto import get_random_string

from register.viewset import CreateOnlyViewSet

# Create your views here.

from . import serializers, models


class CheckApplicationViewSets(ModelViewSet):
    queryset = models.CheckApplication.objects.all()
    serializer_class = serializers.CheckApplicationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data['application']
        if application.application_status == 1:
            application.application_status = serializer.validated_data['apply_status']
            application.save()
        else:
            return Response('该状态无法被更改', status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class GenerateCodeView(CreateOnlyViewSet):
    queryset = models.CodeWarehouse.objects.all()
    serializer_class = serializers.GenerateCodeSerializer
    permission_classes = (IsAdminUser,)

    def perform_create(self, serializer):
        code = get_random_string()
        while models.CodeWarehouse.objects.filter(code=code).exists():
            code = get_random_string()
        data = {
            'code': code,
            'use_state': 0,
            'active_user': self.request.user
        }
        serializer.save(**data)


class CreateStoreViewSets(ModelViewSet):
    queryset = models.CreateStore.objects.all()
    serializer_class = serializers.CreateStoreSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code=serializer.validated_data['active_code']
        application=serializer.validated_data['info']
        if application.application_status!=3:
            return Response('你的申请未通过,请通过后进行再验证',status=status.HTTP_400_BAD_REQUEST)

        if models.CodeWarehouse.objects.filter(code=code,use_state=0).exists():

            self.perform_create(serializer)
            application.codewarehouse.save(use_state=1,active_user=request.user)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response('激活码错误或已经使用过了',status=status.HTTP_400_BAD_REQUEST)
