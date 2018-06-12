from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.views import Response,status

from register.viewset import ListOnlyViewSet

from . import models,serializers
from goods.serializers import FirstClassSerializer
from goods.models import FirstClass
# Create your views here.


class BannerView(ModelViewSet):
    serializer_class = serializers.BannerSerializer
    queryset = models.Banner.objects.all()

    def perform_create(self, serializer):
        serializer.save(last_operator=self.request.user)


class UmViewSets(ListOnlyViewSet):

    def list(self, request, *args, **kwargs):
        result={
            "banners":serializers.BannerSerializer(models.Banner.objects.all(),many=True).data,
            "sorts":FirstClassSerializer(FirstClass.objects.all(),many=True).data,
        }
        return Response(result)


class RecruitView(ModelViewSet):
    serializer_class = serializers.RecruitSerializer
    queryset = models.RecruitMerchant.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.update(last_operator=self.request.user)
        image,created=self.queryset.update_or_create(defaults=serializer.validated_data,name='propagate')
        return Response(image.image.url)


class ApplicationViewSets(ModelViewSet):
    serializer_class = serializers.ApplicationSerializer
    queryset = models.Application.objects.all()


    def perform_create(self, serializer):
        serializer.save(application_user=self.request.user)