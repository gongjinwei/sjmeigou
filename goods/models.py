from django.db import models
from django.contrib.auth.models import User
from jsonfield import JSONField


# Create your models here.


class FirstClass(models.Model):
    first_class_name = models.CharField(max_length=100, help_text='一级类目名称', unique=True)
    cover_path = models.ImageField(upload_to='sjmeigou/goods/firstclass/%Y%m%d')
    sort_order = models.SmallIntegerField(unique=True)
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.first_class_name

    class Meta:
        ordering = ['sort_order']


class SecondClass(models.Model):
    first_class = models.ForeignKey(to='FirstClass', on_delete=models.CASCADE, help_text='选择一级类目',
                                    related_name='second_classes')
    second_class_name = models.CharField(max_length=100, help_text='填写二级类目名称')
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return "%s:%s" % (self.first_class.first_class_name, self.second_class_name)

    class Meta:
        unique_together = ['first_class', 'second_class_name']


class ThirdClass(models.Model):
    second_class = models.ForeignKey(to='SecondClass', on_delete=models.CASCADE, help_text='选择二级类目')
    third_class_name = models.CharField(max_length=100, help_text='填写三级类目名称')
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return "%s:%s:%s" % (
            self.second_class.first_class.first_class_name, self.second_class.second_class_name, self.third_class_name)

    class Meta:
        unique_together = ['second_class', 'third_class_name']


class FirstProperty(models.Model):
    first_property_name = models.CharField(max_length=100, help_text='填写类目属性')
    third_class = models.ForeignKey(to='ThirdClass', on_delete=models.CASCADE, blank=True, help_text='选择三级类目')
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return "%s:%s:%s:%s" % (
            self.third_class.second_class.first_class.first_class_name, self.third_class.second_class.second_class_name,
            self.third_class.third_class_name, self.first_property_name)

    class Meta:
        unique_together = ['third_class', 'first_property_name']


class SecondProperty(models.Model):
    second_property_name = models.CharField(max_length=100, help_text='填写二级属性名称')
    first_property = models.ForeignKey(to='FirstProperty', on_delete=models.CASCADE, help_text='选择一级属性',
                                       related_name='secondProperties')
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        unique_together = ['first_property', 'second_property_name']


class ItemsGroupDesc(models.Model):
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE, editable=False)
    items = JSONField()


class SizeGroup(models.Model):
    group_name = models.CharField(max_length=50)
    second_class = models.ForeignKey(to='SecondClass', on_delete=models.CASCADE)

    def __str__(self):
        return '%s:%s-%s' % (self.second_class.second_class_name, self.group_name, self.id)


class SizeDesc(models.Model):
    size_group = models.ForeignKey(to='SizeGroup', on_delete=models.CASCADE, related_name='sizes')
    size_name = models.CharField(max_length=50)

    class Meta:
        unique_together = ('size_group', 'size_name')
        ordering = ('id',)


class SizeGroupClass(models.Model):
    third_class = models.ForeignKey(to='ThirdClass', on_delete=models.CASCADE, related_name='size_group_classes')
    size_group = models.ForeignKey(to='SizeGroup', on_delete=models.CASCADE, related_name='size_classes')


class SKUColor(models.Model):
    good_detail = models.ForeignKey(to='GoodDetail', on_delete=models.CASCADE, related_name='colors')
    color_name = models.CharField(max_length=20)
    color_remark = models.CharField(max_length=30, blank=True, null=True)
    color_pic = models.CharField(max_length=255)
    color_code = models.CharField(max_length=7)


class SKU(models.Model):
    color = models.ForeignKey(to='SKUColor',related_name='skus',on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=20, decimal_places=2)
    stock = models.IntegerField(default=0)
    size = models.ForeignKey(to='SizeDesc', on_delete=models.SET_NULL,null=True)
    merchant_coding = models.CharField(max_length=50,blank=True,null=True)
    barcode = models.CharField(max_length=100,blank=True,null=True)


class GoodDetail(models.Model):
    owner=models.ForeignKey(to=User,editable=False,on_delete=models.CASCADE,related_name='goodDetails')
    third_class=models.ForeignKey(to='ThirdClass',on_delete=models.DO_NOTHING,related_name='goodDetails')
    title=models.CharField(max_length=50)
    params = JSONField()
    master_graphs = JSONField()
    master_video=models.URLField(null=True,blank=True)
    min_price = models.DecimalField(max_digits=20, decimal_places=2)
    total_stock = models.IntegerField(default=0)
    merchant_coding=models.CharField(max_length=50,blank=True,null=True)
    barcode = models.CharField(max_length=100,blank=True,null=True)
    stock_count_strategy=models.IntegerField(
        choices=((0,'买家拍下减库存'),(1,'买家付款减库存')),default=0
    )
    to_deliver_hours = models.IntegerField(choices=(
        (1, '1小时内'), (2, '2小时内'), (24, '24小时内'), (48, '48小时内')
    ))
    put_on_sale_time=models.DateTimeField()
    put_on_strategy=models.SmallIntegerField(default=0,choices=((0,'立即上架'),(1,'定时上架'),(2,'放入仓库内')))
    state=models.SmallIntegerField(default=0,choices=((0,'出售中'),(1,'仓库中'),(2,'已删除')),editable=False)
    item_desc=models.OneToOneField(to='ItemsGroupDesc',on_delete=models.CASCADE)
    good_type=models.ForeignKey(to='store.GoodsType',on_delete=models.SET_NULL,blank=True,null=True,related_name='goods')
    store=models.ForeignKey(to='store.Stores',on_delete=models.CASCADE,editable=False,related_name='goods')
    create_time=models.DateTimeField(auto_now_add=True,editable=False)


class AfterSaleServices(models.Model):
    good_detail = models.ForeignKey(to='GoodDetail', on_delete=models.CASCADE,related_name='after_sale_services')
    server= models.IntegerField(
        choices=((0, '提供发票'), (1, '保修服务'), (2, '退换货承诺，凡使用微信购买本店商品，若存在质量问题或与描述不符，本店将主动退换货服务并承担来回运费'),
                 (3, '服务承诺：该类商品必须支持【七天退货服务】')),default=3)


class GoodDeliver(models.Model):
    good_detail = models.ForeignKey(to='GoodDetail',on_delete=models.CASCADE,related_name='delivers')
    server = models.ForeignKey(to='platforms.Delivers',on_delete=models.CASCADE)


class SearchHistory(models.Model):
    user = models.ForeignKey(to=User,on_delete=models.CASCADE)
    q= models.CharField(max_length=128)
    update_time=models.DateTimeField(auto_now=True)

    class Meta:
        ordering=('-update_time',)