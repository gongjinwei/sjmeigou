# -*- coding:UTF-8 -*-
from rest_framework.permissions import BasePermission, SAFE_METHODS


class MerchantPermission(BasePermission):
    def has_permission(self, request, view):

        return request.user and request.user.is_authenticated and request.user.has_perm('store.change_stores',request.user.stores)


class MerchantOrReadOnlyPermission(BasePermission):
    def has_permission(self, request, view):

        return (
                request.method in SAFE_METHODS or
                request.user and
                request.user.is_authenticated and
                request.user.has_perm('store.change_stores',request.user.stores)
        )
