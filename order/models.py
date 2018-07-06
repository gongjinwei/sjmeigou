from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class ShoppingCarItem(models.Model):
    user=models.ForeignKey(to=User,on_delete=models.CASCADE,related_name='shopping_items',editable=False)
    price_of_added=models.DecimalField(decimal_places=2,max_digits=30,editable=False)
    num=models.IntegerField()
    sku=models.ForeignKey(to='goods.SKU',on_delete=models.SET_NULL,null=True)
    state=models.SmallIntegerField(choices=((0,'正常'),(1,'失效')),default=0,editable=False)
    create_time=models.DateTimeField(auto_now_add=True)


class Coupon(models.Model):
    store=models.ForeignKey(to='store.Stores',on_delete=models.CASCADE)
    name=models.CharField(max_length=10)
    date_from=models.DateField()
    date_to=models.DateField()
    discount=models.IntegerField()
    threshold_count=models.IntegerField()
    available_num=models.IntegerField()
    limit_per_user=models.SmallIntegerField()
    create_date=models.DateField(auto_now_add=True)





class Reduction(models.Model):
    pass