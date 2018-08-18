# -*- coding:UTF-8 -*-
from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='index'

router.register('banner',views.BannerView,base_name='banner')
router.register('recruit',views.RecruitView,base_name='recruit')
router.register('um',views.UmViewSets,base_name='Um')
router.register('application',views.ApplicationViewSets,base_name='application')
router.register('messageOfMine',views.MessageOfMineView,base_name='messageOfMine')
router.register('userGoodTrack',views.GoodTrackViewSets,base_name='userGoodTrack')

urlpatterns=router.urls