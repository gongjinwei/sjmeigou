# -*- coding:UTF-8 -*-
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins


class CreateOnlyViewSet(mixins.CreateModelMixin, GenericViewSet):
    """
    A viewset that provides default `create()` actions.
    """
    pass


class CreateListDeleteViewSet(mixins.CreateModelMixin,
                              mixins.ListModelMixin,
                              mixins.DestroyModelMixin,
                              GenericViewSet):
    pass


class ListOnlyViewSet(mixins.ListModelMixin, GenericViewSet):
    pass


class CreateListViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, GenericViewSet):
    pass


class RetrieveUpdateViewSets(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    pass


class RetrieveOnlyViewSets(mixins.RetrieveModelMixin, GenericViewSet):
    pass


class ListRetrieveDeleteViewSets(mixins.ListModelMixin,mixins.RetrieveModelMixin,mixins.DestroyModelMixin):
    pass


class ListDeleteViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, GenericViewSet):
    pass


class ListDetailDeleteViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin,
                                GenericViewSet):
    pass

class ListRetrieveCreateViewSets(mixins.ListModelMixin,mixins.RetrieveModelMixin,mixins.CreateModelMixin,GenericViewSet):
    pass
