# -*- coding:UTF-8 -*-
from rest_framework import serializers
from . import models

from index.serializers import ApplicationSerializer
from index.models import Application


class CheckApplicationSerializer(serializers.ModelSerializer):
    # application=serializers.SerializerMethodField()

    class Meta:
        model = models.CheckApplication
        fields = '__all__'

    # def get_application(self, obj):
    #     queryset =obj.application if obj.application.application_status==1 else Application.objects.none()
    #     return ApplicationSerializer(queryset).data
