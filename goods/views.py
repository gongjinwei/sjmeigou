from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet
from rest_framework.views import Response, status
from rest_framework.decorators import action
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.query import EmptyQuerySet

from . import models, serializers
from tools.permissions import MerchantOrReadOnlyPermission
from tools.viewset import ListOnlyViewSet
from store.models import GoodsType


# Create your views here.


class FirstClassView(ModelViewSet):
    serializer_class = serializers.FirstClassSerializer
    queryset = models.FirstClass.objects.all()

    def perform_create(self, serializer):
        serializer.save(last_operator=self.request.user)


class SecondClassView(ModelViewSet):
    serializer_class = serializers.SecondClassSerializer
    queryset = models.SecondClass.objects.all()

    def perform_create(self, serializer):
        serializer.save(last_operator=self.request.user)


class FirstPropertyView(ModelViewSet):
    serializer_class = serializers.FirstPropertySerializer
    queryset = models.FirstProperty.objects.all()

    def get_queryset(self):
        try:
            third_class = int(self.request.query_params.get('third_class', '0'))
        except ValueError:
            return models.FirstProperty.objects.none()

        return models.FirstProperty.objects.filter(third_class_id=third_class)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)

        try:
            third_class_id = int(self.request.query_params.get('third_class', '0'))
        except ValueError:
            return Response('类目不存在', status=status.HTTP_400_BAD_REQUEST)

        if models.ThirdClass.objects.filter(pk=third_class_id).exists():
            third_class = models.ThirdClass.objects.get(pk=third_class_id)
            third_class_data = serializers.ThirdClassSerializer(instance=third_class).data
        else:
            third_class_data = []

        return Response({
            'properties': serializer.data,
            'third_class_sizes': third_class_data
        })

    def perform_create(self, serializer):
        serializer.save(last_operator=self.request.user)


class SecondPropertyView(ModelViewSet):
    serializer_class = serializers.SecondPropertySerializer

    def perform_create(self, serializer):
        serializer.save(last_operator=self.request.user)

    def get_queryset(self):
        try:
            first_property = int(self.request.query_params.get('first_property', '0'))
        except ValueError:
            return models.SecondProperty.objects.none()

        return models.SecondProperty.objects.filter(first_property_id=first_property)


class ThirdClassView(ModelViewSet):
    serializer_class = serializers.ThirdClassSerializer

    def get_queryset(self):
        try:
            second_class = int(self.request.query_params.get('second_class', '0'))
        except ValueError:
            return models.ThirdClass.objects.none()
        return models.ThirdClass.objects.filter(second_class_id=second_class)

    def perform_create(self, serializer):
        serializer.save(last_operator=self.request.user)


class SizeGroupView(ModelViewSet):
    serializer_class = serializers.SizeGroupSerializer
    queryset = models.SizeGroup.objects.all()


class SizeDescView(ModelViewSet):
    serializer_class = serializers.SizeDescSerializer
    queryset = models.SizeDesc.objects.all()


class SizeGroupClassView(ModelViewSet):
    serializer_class = serializers.SizeGroupClassSerializer
    queryset = models.SizeGroupClass.objects.all()


class ItemsDescView(ModelViewSet):
    serializer_class = serializers.ItemsGroupDescSerializer
    queryset = models.ItemsGroupDesc.objects.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PriceFilterClass(FilterSet):
    class Meta:
        model = models.GoodDetail
        fields = {
            'min_price': ['lte', 'gte'],
            'title': ['contains'],
            'store':['exact'],
            'good_type':['exact']
        }


class GoodDetailView(ModelViewSet):
    serializer_class = serializers.GoodDetailSerializer
    queryset = models.GoodDetail.objects.filter(state=0)
    filter_backends = (DjangoFilterBackend,)
    filter_class = PriceFilterClass
    filter_fields = ('title__contains', 'min_price__lte', 'min_price__gte','store','good_type')
    permission_classes = (MerchantOrReadOnlyPermission,)

    def perform_create(self, serializer):
        good_type=serializer.validated_data.get('good_type',None)
        if good_type:
            owner_good_type=GoodsType.objects.filter(store_goods_type__store=self.request.user.stores)
            if good_type not in owner_good_type:
                return Response('你没有此操作权限',status=status.HTTP_400_BAD_REQUEST)
        put_on_strategy = serializer.validated_data.get('put_on_strategy', 0)
        if put_on_strategy == 0:
            state = 0
        else:
            state = 1
        serializer.save(owner=self.request.user, store=self.request.user.stores, state=state)

    @action(methods=['get'],detail=True,serializer_class=serializers.SKUColorSerializer)
    def get_sku(self,request,pk=None):
        queryset=models.SKUColor.objects.filter(good_detail_id=pk)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)


class GoodSearchView(ListOnlyViewSet):
    serializer_class = serializers.GoodSearchSerializer
    queryset = models.GoodDetail.objects.filter(state=0)

    def list(self, request, *args, **kwargs):
        # 记录搜索历史
        q= request.query_params.get('q','')
        if q:
            models.SearchHistory.objects.update_or_create(defaults={
                'user':request.user,'q':q
            },user=request.user,q=q)

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SearchHistoryView(ListOnlyViewSet):
    serializer_class = serializers.SearchHistorySerializer
    queryset = models.SearchHistory.objects.all()

    def list(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            queryset=models.SearchHistory.objects.filter(user=self.request.user)
            if queryset is not EmptyQuerySet:
                return Response(queryset.values_list('q',flat=True)[:10])

        return Response([])







