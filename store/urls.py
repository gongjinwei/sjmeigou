# -*- coding:UTF-8 -*-
from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='store'

router.register('checkApplication',views.CheckApplicationViewSets,base_name='checkApplication')

urlpatterns=router.urls