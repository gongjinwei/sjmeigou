# -*- coding:UTF-8 -*-
import math
import requests
from django.conf import settings

gd_key = getattr(settings,'GDKEY')

def get_deliver_pay(origin,destination):
    url = 'https://restapi.amap.com/v4/direction/bicycling?origin={}&destination={}&key={}'.format(origin, destination,
                                                                                                   gd_key)
    res = requests.get(url)
    # 返回米
    meters = res.json()['data']['paths'][0]['distance']
    kilometers=math.ceil(meters/1000)
    if kilometers<=1:
        return (1,1.5,1.5)
    else:
        plat_to_pay=(2+kilometers)/2
        return (kilometers,plat_to_pay)