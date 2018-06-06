# -*- coding:UTF-8 -*-
from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='goods'

router.register('firstClass',views.FirstClassView,base_name='firstClass')
router.register('secondClass',views.SecondClassView,base_name='secondClass')
router.register('firstProperty',views.FirstPropertyView,base_name='firstProperty')
router.register('secondProperty',views.SecondPropertyView,base_name='secondProperty')

urlpatterns=router.urls