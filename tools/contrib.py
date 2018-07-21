# -*- coding:UTF-8 -*-
import math
import requests
from django.conf import settings
from django.core.cache import cache

gd_key = getattr(settings,'GDKEY')


def get_deliver_pay(origin,destination):
    ret=cache.get('%s:%s' % (origin,destination))
    if not ret:
        url = 'https://restapi.amap.com/v4/direction/bicycling?origin={}&destination={}&key={}'.format(origin, destination,
                                                                                                       gd_key)
        res = requests.get(url)
        # 返回米
        meters = res.json()['data']['paths'][0]['distance']
        kilometers=math.ceil(meters/1000)
        if kilometers<=1:
            ret=(1,1.5)
        else:
            plat_to_pay=(2+kilometers)/2
            ret=(kilometers,plat_to_pay)
        cache.set('%s:%s' % (origin, destination),ret,timeout=24*3600*7)
    return ret