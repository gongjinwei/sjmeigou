from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.views import Response,status

from register.viewset import ListOnlyViewSet

from . import models,serializers
# Create your views here.


class BannerView(ModelViewSet):
    serializer_class = serializers.BannerSerializer
    queryset = models.Banner.objects.all()

    def perform_create(self, serializer):
        serializer.save(last_operator=self.request.user)


class SortTypeView(ModelViewSet):
    serializer_class = serializers.SortTypeSerializer
    queryset = models.SortType.objects.all()

    def perform_create(self, serializer):
        serializer.save(last_operator=self.request.user)


class UmViewSets(ListOnlyViewSet):

    def list(self, request, *args, **kwargs):
        result={
            "banners":serializers.BannerSerializer(models.Banner.objects.all(),many=True).data,
            "sorts":serializers.SortTypeSerializer(models.SortType.objects.all(),many=True).data
        }
        return Response(result)