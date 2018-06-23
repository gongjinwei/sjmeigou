# -*- coding:UTF-8 -*-
from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='store'

router.register('checkApplication',views.CheckApplicationViewSets,base_name='checkApplication')
router.register('generateCode',views.GenerateCodeView,base_name='generateCode')

urlpatterns=router.urls