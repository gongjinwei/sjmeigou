from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet
from rest_framework.views import Response,status


from . import models,serializers
from tools.permissions import MerchantOrReadOnlyPermission
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
            third_class=int(self.request.query_params.get('third_class','0'))
        except ValueError:
            return models.FirstProperty.objects.none()

        return models.FirstProperty.objects.filter(third_class_id=third_class)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)

        try:
            third_class_id=int(self.request.query_params.get('third_class','0'))
        except ValueError:
            return Response('类目不存在',status=status.HTTP_400_BAD_REQUEST)

        if models.ThirdClass.objects.filter(pk=third_class_id).exists():
            third_class=models.ThirdClass.objects.get(pk=third_class_id)
            third_class_data = serializers.ThirdClassSerializer(instance=third_class).data
        else:
            third_class_data=[]

        return Response({
            'properties':serializer.data,
            'third_class_sizes':third_class_data
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
            second_class=int(self.request.query_params.get('second_class','0'))
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


class GoodDetailView(ModelViewSet):
    serializer_class = serializers.GoodDetailSerializer
    queryset = models.GoodDetail.objects.all()
    permission_classes = (MerchantOrReadOnlyPermission,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user,store=self.request.user.stores)





