# -*- coding:UTF-8 -*-
from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='wxpay'

router.register('notifyOrder',views.NotifyOrderView,base_name='notifyOrder')


urlpatterns=router.urls