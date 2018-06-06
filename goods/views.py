from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet


from . import models,serializers
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
