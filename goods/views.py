from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet
from rest_framework.views import Response,status


from . import models,serializers

from register.viewset import ListOnlyViewSet
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

    def perform_create(self, serializer):
        serializer.save(last_operator=self.request.user)


class SecondPropertyView(ModelViewSet):
    serializer_class = serializers.SecondPropertySerializer
    queryset = models.SecondProperty.objects.all()

    def perform_create(self, serializer):
        serializer.save(last_operator=self.request.user)


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


