# -*- coding:UTF-8 -*-
from rest_framework.routers import DefaultRouter
from . import views

router=DefaultRouter()
app_name='register'

router.register('send',views.SendView,base_name='register_send')
router.register('check',views.CheckView,base_name='register_check')
router.register('getUserInfo',views.GetUserInfoView,base_name='getUserInfo')
router.register('images',views.ImageView,base_name='images')
router.register('vodcallback',views.VodCallbackView,base_name='vodcallback')
router.register('getVodSignature',views.GetVodSignatureView,base_name='getVodSignature')
router.register('msgCheck',views.MsgCheckView,base_name='msgCheck')

urlpatterns=router.urls