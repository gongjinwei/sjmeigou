from rest_framework.views import Response, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser

from django.utils.crypto import get_random_string

from register.viewset import CreateOnlyViewSet

from guardian.shortcuts import assign_perm
from django.contrib.auth.models import Group

# Create your views here.

from . import serializers, models
from index.models import Application


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
            'use_state': 0
        }
        serializer.save(**data)


class StoresViewSets(ModelViewSet):
    serializer_class = serializers.StoresSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code=serializer.validated_data['active_code']
        application=serializer.validated_data['info']
        if application.application_status!=5:
            return Response('你的申请未通过,请通过后进行再验证',status=status.HTTP_400_BAD_REQUEST)

        if models.CodeWarehouse.objects.filter(code=code,use_state=0).exists():

            self.perform_create(serializer)
            application.codewarehouse.use_state=1
            application.codewarehouse.active_user=request.user
            application.codewarehouse.save()
            Application.objects.filter(pk=application.pk).update(application_status=6)

            # 将申请用户加入权限组

            assign_perm('store.change_stores',request.user,request.user.stores)

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response('激活码错误或已经使用过了',status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user,active_state=True)

    def get_queryset(self):

        if self.request.user.is_staff:
            return models.Stores.objects.all()
        elif self.request.user.is_authenticated:
            return models.Stores.objects.filter(user=self.request.user)

        return models.Stores.objects.none()


class StatusChangeView(CreateOnlyViewSet):
    serializer_class = serializers.StatusChangeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj=Application.objects.filter(application_id=serializer.validated_data['application_id'])
        if obj.exists():
            obj.update(application_status=serializer.validated_data['application_status'])

            return Response('success')
        else:
            return Response('Not exists',status=status.HTTP_400_BAD_REQUEST)


class DepositView(ModelViewSet):
    serializer_class = serializers.DepositSerializer

    def get_queryset(self):

        if self.request.user.is_staff:
            return models.Deposit.objects.all()
        elif self.request.user.is_authenticated:
            return models.Deposit.objects.filter(application=self.request.user.application)

        return models.Deposit.objects.none()