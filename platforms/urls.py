# -*- coding:UTF-8 -*-
from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='platforms'

router.register('checkApplication',views.CheckApplicationViewSets,base_name='checkApplication')
router.register('storeActivityType',views.StoreActivityViewSets,base_name='storeActivityType')
router.register('delivers',views.DeliversViewSets,base_name='delivers')
router.register('deliverServices',views.DeliverServicesViewSets,base_name='deliverServices')
router.register('generateCode',views.GenerateCodeView,base_name='generateCode')

urlpatterns=router.urls