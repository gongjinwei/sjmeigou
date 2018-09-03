# -*- coding:UTF-8 -*-
from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='store'


router.register('stores',views.StoresViewSets,base_name='stores')
# router.register('deposit',views.DepositView,base_name='deposit')
router.register('storeQRCode',views.StoreQRCodeViewSets,base_name='storeQRCode')
router.register('storeInfo',views.StoreInfoView,base_name='storeInfo')
router.register('enterpriseQualification',views.EnterpriseQualificationView,base_name='enterpriseQualification')
router.register('storeGoodType',views.StoreGoodsTypeView,base_name='storeGoodType')
router.register('goodType',views.GoodsTypeView,base_name='goodType')
router.register('storeSearch',views.StoreSearchView,base_name='storeSearch')
router.register('storeMessage',views.StoreMessageView,base_name='storeMessage')
router.register('storeFavorites',views.StoreFavoritesViewSets,base_name='storeFavorites')
router.register('goodFavorites',views.GoodFavoritesViewSets,base_name='goodFavorites')
router.register('bargainActivity',views.BargainActivityViewSets,base_name='bargainActivity')
router.register('userBargain',views.UserBargainViewSets,base_name='userBargain')
router.register('sharingReduce',views.SharingReduceViewSets,base_name='sharingReduce')

urlpatterns=router.urls