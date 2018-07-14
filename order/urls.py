# -*- coding:UTF-8 -*-

from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='order'

router.register('shoppingCar',views.ShoppingCarView,base_name='shoppingCar')
router.register('shoppingCarItem',views.ShoppingCarItemView,base_name='shoppingCarItem')
router.register('coupon',views.CouponView,base_name='coupon')
router.register('getCoupon',views.GetCouponView,base_name='getCoupon')
router.register('storeActivity',views.StoreActivityView,base_name='storeActivity')
router.register('balance',views.BalanceView,base_name='balance')
router.register('receiveAddress',views.ReceiveAddressViewSets,base_name='receiveAddress')
router.register('unifyOrder',views.UnifyOrderView,base_name='unifyOrder')

urlpatterns=router.urls