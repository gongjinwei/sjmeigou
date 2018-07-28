# -*- coding:UTF-8 -*-
from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='platforms'

router.register('checkApplication',views.CheckApplicationViewSets,base_name='checkApplication')
router.register('storeActivityType',views.StoreActivityViewSets,base_name='storeActivityType')
router.register('delivers',views.DeliversViewSets,base_name='delivers')
router.register('deliverServices',views.DeliverServicesViewSets,base_name='deliverServices')
router.register('account',views.AccountViewSets,base_name='account')
router.register('accountRecharge',views.AccountRechargeViewSets,base_name='accountRecharge')
router.register('deliveryReason',views.DeliveryReasonView,base_name='deliveryReason')
router.register('protocol',views.ProtocolViewSets,base_name='protocol')

urlpatterns=router.urls