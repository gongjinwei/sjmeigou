# -*- coding:UTF-8 -*-
from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='platforms'

router.register('checkApplication',views.CheckApplicationViewSets,base_name='checkApplication')
router.register('storeActivityType',views.StoreActivityViewSets,base_name='storeActivityType')

urlpatterns=router.urls