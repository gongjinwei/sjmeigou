# -*- coding:UTF-8 -*-
from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='store'

router.register('checkApplication',views.CheckApplicationViewSets,base_name='checkApplication')
router.register('generateCode',views.GenerateCodeView,base_name='generateCode')
router.register('stores',views.StoresViewSets,base_name='stores')
router.register('storeStatus',views.StoreStatusView,base_name='storeStatus')
router.register('statusChange',views.StatusChangeView,base_name='statusChange')

urlpatterns=router.urls