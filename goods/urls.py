# -*- coding:UTF-8 -*-
from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='goods'

router.register('firstClass',views.FirstClassView,base_name='firstClass')
# router.register('secondClass',views.SecondClassView,base_name='secondClass')
router.register('thirdClass',views.ThirdClassView,base_name='thirdClass')
router.register('firstProperty',views.FirstPropertyView,base_name='firstProperty')
router.register('secondProperty',views.SecondPropertyView,base_name='secondProperty')
router.register('sizeGroup',views.SizeGroupView,base_name='sizeGroup')
router.register('sizeDesc',views.SizeDescView,base_name='sizeDesc')
router.register('sizeGroupClass',views.SizeGroupClassView,base_name='sizeGroupClass')
router.register('itemsDesc',views.ItemsDescView,base_name='itemsDesc')
router.register('goodDetail',views.GoodDetailView,base_name='goodDetail')
router.register('goodSearch',views.GoodSearchView,base_name='goodSearch')

urlpatterns=router.urls