# -*- coding:UTF-8 -*-
from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='store'

router.register('generateCode',views.GenerateCodeView,base_name='generateCode')
router.register('stores',views.StoresViewSets,base_name='stores')
router.register('statusChange',views.StatusChangeView,base_name='statusChange')
router.register('deposit',views.DepositView,base_name='deposit')
router.register('storeQRCode',views.StoreQRCodeViewSets,base_name='storeQRCode')
router.register('storeInfo',views.StoreInfoView,base_name='storeInfo')
router.register('enterpriseQualification',views.EnterpriseQualificationView,base_name='enterpriseQualification')
router.register('storeGoodType',views.StoreGoodsTypeView,base_name='storeGoodType')
router.register('goodType',views.GoodsTypeView,base_name='goodType')

urlpatterns=router.urls