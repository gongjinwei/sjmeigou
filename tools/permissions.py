# -*- coding:UTF-8 -*-
from rest_framework.permissions import BasePermission, SAFE_METHODS


class MerchantPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.stores:
            return request.user and request.user.is_authenticated and request.user.has_perm('store.change_stores',request.user.stores)
        else:
            return False


class MerchantOrReadOnlyPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        elif request.user.stores:
            return (
                    request.user and
                    request.user.is_authenticated and
                    request.user.has_perm('store.change_stores',request.user.stores)
            )
        else:
            return False
