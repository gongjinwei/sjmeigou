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
router.register('initialPayment',views.InitialPaymentView,base_name='initialPayment')
router.register('storeOrder',views.StoreOrderView,base_name='storeOrder')
router.register('orderRefund',views.OrderRefundView,base_name='orderRefund')
router.register('userCommentContent',views.UserCommentContentView,base_name='userCommentContent')
router.register('shoppingConsult',views.ShoppingConsultViewSets,base_name='shoppingConsult')

urlpatterns=router.urls