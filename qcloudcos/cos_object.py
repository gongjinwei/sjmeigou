import requests
from qcloudcos.cos_auth import Auth
from django.conf import settings
from .utils import get_logger

LOGGER = get_logger('Tencent Cos')


class CosObject(object):
    def __init__(self, option=None):
        if not option:
            self.option = settings.QCLOUD_STORAGE_OPTION

    def get_object(self, name, is_private=False):
        method = 'get'
        url, authorization = self.make_params(method, name, is_private)

        s = requests.Session()
        if is_private:
            s.headers.update(authorization)

        r = s.get(url)
        return r

    def put_object(self, name, content):
        method = 'put'
        url, authorization = self.make_params(method, name)
        s = requests.Session()
        s.headers.update(authorization)

        r = s.put(url, data=content)
        if r.status_code == 200:
            return r
        else:
            LOGGER.info(r.content)

    def head_object(self, name, is_private=False):
        method = 'head'

        url, authorization = self.make_params(method, name, is_private)

        s = requests.Session()
        if is_private:
            s.headers.update(authorization)

        r = s.head(url)
        return r

    def delete_object(self, name):
        method = 'delete'
        url, authorization = self.make_params(method, name)

        s = requests.Session()
        s.headers.update(authorization)

        r = s.delete(url)
        if r.status_code == 204:
            return True

    def make_params(self, method, name, is_private=True):
        appid = self.option['Appid']
        SecretID = self.option['SecretID']
        SecretKey = self.option['SecretKey']
        region = self.option['region']
        bucket = self.option['bucket']
        if name is None:
            name = ''
        elif name[0] != '/':
            name = '/' + name
        objectName = name

        url = "http://%s-%s.%s.myqcloud.com%s" % (bucket, appid, region, objectName)
        if is_private:
            auth = Auth(appid, SecretID, SecretKey, bucket, region, method, objectName)
            authorization = {'Authorization': auth.get_authorization()}
        else:
            authorization = None

        return url, authorization
