# -*- coding:UTF-8 -*-
from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='index'

router.register('banner',views.BannerView,base_name='banner')
router.register('recruit',views.RecruitView,base_name='recruit')
router.register('um',views.UmViewSets,base_name='Um')
router.register('application',views.ApplicationViewSets,base_name='application')

urlpatterns=router.urls