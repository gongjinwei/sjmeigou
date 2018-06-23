# -*- coding:UTF-8 -*-
from rest_framework import serializers
from . import models

from index.serializers import ApplicationSerializer
from index.models import Application


class CheckApplicationSerializer(serializers.ModelSerializer):
    application = serializers.SerializerMethodField()

    class Meta:
        model = models.CheckApplication
        fields = '__all__'

    def get_application(self, obj):
        queryset = Application.objects.filter(application_status=1)
        return ApplicationSerializer(queryset=queryset, many=True)
