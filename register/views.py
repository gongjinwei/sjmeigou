# from django.shortcuts import render
import string, random, json, base64, hashlib, datetime
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User

from rest_framework.views import Response, status
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework_jwt.settings import api_settings
from rest_framework.viewsets import ModelViewSet
import requests
from Crypto.Cipher import AES

from qcloudsms_py import SmsSingleSender
from qcloudsms_py.httpclient import HTTPError

from . import serializers, viewset, models

# Create your views here.


sms_appid = getattr(settings, 'QCLOUD_SMS_APPID')
sms_appkey = getattr(settings, 'QCLOUD_SMS_APPKEY')
sms_timeout = getattr(settings, 'QCLOUD_SMS_TIMEOUT')
appId = getattr(settings, 'APPID')
appSecret = getattr(settings, 'APPSECRET')
template_id = '125560'

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class SendView(viewset.CreateOnlyViewSet):
    serializer_class = serializers.SendSerializer
    permission_classes = (AllowAny,)

    def random_digits(self):
        char = string.digits
        return ''.join(random.choice(char) for _ in range(6))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        mobile = serializer.validated_data['mobile']

        ttl = cache.ttl(mobile + '_timeout')
        ssender = SmsSingleSender(sms_appid, sms_appkey)
        if ttl > 0:
            return Response({'errmsg': "请在1分钟后再试"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            userId = request.query_params.get('userId', '')
            if models.UserInfo.objects.filter(id=userId).exists():
                tts = cache.get(userId + '_send_nums', 0)
                if tts == 0:
                    cache.set(userId + '_send_nums', 0, timeout=60 * 60)
                if userId and tts <= 10:
                    try:
                        code = self.random_digits()
                        params = [code, sms_timeout]
                        result = ssender.send_with_param(86, mobile, template_id, params)
                        cache.incr(userId + '_send_nums')
                        cache.set(mobile + '_timeout', code, 60)
                        cache.set(mobile + '_code', code, sms_timeout * 60)
                        return Response(result)
                    except HTTPError as e:
                        return Response(e, status=status.HTTP_400_BAD_REQUEST)
                    except Exception as e:
                        return Response(e, status=status.HTTP_400_BAD_REQUEST)
                else:
                    if tts > 10:
                        return Response({'errmsg': '您发送验证码的次数过多，请稍后再试'},status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({'errmsg': '请带参数访问'},status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'errmsg':'用户不存在'},status=status.HTTP_400_BAD_REQUEST)


class CheckView(viewset.CreateOnlyViewSet):
    serializer_class = serializers.CheckSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mobile = serializer.validated_data['mobile']
        client_code = serializer.validated_data['code']
        server_code = cache.get(mobile + '_code')

        if client_code == server_code:
            cache.delete(mobile+'_code')
            userId=serializer.validated_data['userId']

            if models.UserInfo.objects.filter(id=userId).exists():
                # 创建或获取用户
                user,created = User.objects.get_or_create(defaults={'username':mobile},username=mobile)
                user.set_password(userId)
                user.save()

                # 生成token
                payload = jwt_payload_handler(user)
                token = jwt_encode_handler(payload)

                return Response({'token': token})
            else:
                return Response({'errmsg':'用户不存在'},status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'errmsg': "验证不通过"}, status=status.HTTP_400_BAD_REQUEST)


class WXBizDataCrypt:
    def __init__(self, appId, sessionKey):
        self.appId = appId
        self.sessionKey = sessionKey

    def decrypt(self, encryptedData, iv):
        # base64 decode
        sessionKey = base64.b64decode(self.sessionKey)
        encryptedData = base64.b64decode(encryptedData)
        iv = base64.b64decode(iv)

        cipher = AES.new(sessionKey, AES.MODE_CBC, iv)

        decrypted = json.loads(self._unpad(cipher.decrypt(encryptedData)))

        if decrypted['watermark']['appid'] != self.appId:
            raise Exception('Invalid Buffer')

        return decrypted

    def _unpad(self, s):
        return s[:-ord(s[len(s) - 1:])]


class GetUserInfoView(viewset.CreateOnlyViewSet):
    serializer_class = serializers.GetUserInfoSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        js_code = serializer.validated_data.get('js_code', '')

        payload = {
            'appid': appId,
            'secret': appSecret,
            'js_code': js_code,
            'grant_type': 'authorization_code'
        }
        r = requests.get('https://api.weixin.qq.com/sns/jscode2session', params=payload).json()
        errmsg = r.get('errmsg', '')

        if errmsg:
            return Response(errmsg, status=status.HTTP_400_BAD_REQUEST)

        session_key = r.get('session_key', '')
        wbxiz = WXBizDataCrypt(appId, session_key)
        try:
            decrypted_data = wbxiz.decrypt(serializer.validated_data['encrypted_data'], serializer.validated_data['iv'])
        except:
            return Response({'error_data': True}, status=status.HTTP_400_BAD_REQUEST)
        m_id = hashlib.md5(str(decrypted_data['openId']).encode()).hexdigest()
        decrypted_data.pop('watermark')
        # 注册小程序id
        obj, created = models.UserInfo.objects.get_or_create(defaults=decrypted_data, id=m_id)

        res = {'userId': m_id, 'created': created, 'nickName': obj.nickName, 'gender': obj.gender}

        return Response(res, status=status.HTTP_200_OK)


class ImageView(ModelViewSet):
    serializer_class = serializers.ImageSerializer
    queryset = models.Image.objects.all()
    permission_classes = (IsAuthenticated,)
