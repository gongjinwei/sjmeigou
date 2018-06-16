# -*- coding:UTF-8 -*-
from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='delivery'

router.register('orderCallback',views.OrderCallbackViewSets,base_name='orderCallback')

urlpatterns=router.urls