# -*- coding:UTF-8 -*-

from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='order'

router.register('shoppingCar',views.ShoppingCarView,base_name='shoppingCar')

urlpatterns=router.urls