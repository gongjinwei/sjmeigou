# -*- coding:UTF-8 -*-
from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth.models import Group


class MerchantPermission(BasePermission):
    def has_permission(self, request, view):

        group=Group.objects.get_or_create(defaults={"name":'merchant0'},name='merchant0')

        return request.user and request.user.is_authenticated and request.user.has_perm('change_merchant0',group)


class MerchantOrReadOnlyPermission(BasePermission):
    def has_permission(self, request, view):
        group = Group.objects.get_or_create(defaults={"name": 'merchant0'}, name='merchant0')

        return (
                request.method in SAFE_METHODS or
                request.user and
                request.user.is_authenticated and
                request.user.has_perm('change_merchant0', group)
        )
