# -*- coding:UTF-8 -*-

from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='order'

router.register('shoppingCar',views.ShoppingCarView,base_name='shoppingCar')
router.register('coupon',views.CouponView,base_name='coupon')
router.register('getCoupon',views.GetCouponView,base_name='getCoupon')
router.register('reductionActivity',views.ReductionActivityView,base_name='reductionActivity')

urlpatterns=router.urls