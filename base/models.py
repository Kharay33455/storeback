from django.db import models
from django.contrib.auth.models import User

#creating models

class Category(models.Model):
    name1 = models.CharField(max_length = 10, default = '')
    name2 = models.CharField(max_length = 10, default = '')
    slug = models.SlugField( default = '')
    background = models.ImageField(null = True, blank= True)

    def __str__(self):
        return self.slug

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE)
    first_name = models.CharField(max_length = 20)
    last_name = models.CharField(max_length = 20)
    email = models.EmailField(max_length = 30)

    def __str__(self):
        """modelling bank users"""
        return f'{self.first_name} {self.last_name}| username = {self.user.username}'
    

class Product(models.Model):
    """model to handle all products"""
    name = models.CharField(max_length = 20)
    price = models.IntegerField()
    in_stock = models.BooleanField(default = True)
    picture1 = models.ImageField(null = True, blank= True)
    picture2 = models.ImageField(null=True, blank=True)
    categories = models.ManyToManyField(Category)
    time_added = models.DateTimeField(null =True, blank = True, auto_now_add = True)
    slug = models.SlugField(default = 'un-named')
    details = models.CharField(max_length = 2000, default = '')


    def __str__(self):
        #returns name of product on default
        return self.name
    
class Cart(models.Model):
    """model the cart"""
    customer = models.OneToOneField(Customer, on_delete = models.CASCADE)
    total_item = models.IntegerField(default = 0)
    total_cost = models.IntegerField(default = 0)

    def __str__(self):
        return f'{self.customer.first_name.title()}\'s  cart'
    
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete = models.CASCADE, null = True, blank = True)
    item = models.ForeignKey(Product, on_delete = models.CASCADE)
    quantity = models.IntegerField(default = 0)

    def __str__(self):
        quantity = self.quantity
        quantity = str(quantity)
        return f'{quantity + " " + self.item.name}'
    
class ShippingInformation(models.Model):
    customer = models.ForeignKey(Customer, on_delete = models.CASCADE)
    street = models.CharField(max_length = 100)
    street2 = models.CharField(max_length = 100, blank= True, null = True)
    city = models.CharField(max_length = 10)
    state = models.CharField(max_length = 10)
    country = models.CharField(max_length = 30)
    mobile = models.CharField(max_length = 30, null = True, blank = True)

    def __str__(self):
        return f"{self.customer.first_name}'s {self.city} shipping adress "


class Order(models.Model):
    order_id = models.CharField(max_length = 30)
    customer = models.ForeignKey(Customer, on_delete = models.CASCADE)
    ship_p1 = models.TextField()
    ship_p2 = models.TextField()
    ship_p3 = models.TextField()
    time = models.DateTimeField(auto_now_add = True)
    total = models.CharField(max_length = 20)
    successful = models.BooleanField(null= True, blank = True)
    hasPaid = models.BooleanField(null = True, blank = True)    # has user clicked that they have paid. 


    def __str__(self):
        return f'Order for {self.customer.first_name} on {str(self.time)}'
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete = models.CASCADE)
    item_name = models.CharField(max_length = 100)
    quantity = models.CharField(max_length = 20)
    unit_price = models.CharField(max_length = 100) #price of single item at time of order

    def __str__(self):
        return f'Order item {self.order} item'


class CompanyDetail(models.Model):
    name = models.CharField(max_length = 15)
    address = models.TextField()
    about = models.TextField()
    subhead = models.TextField()
    about2 = models.TextField()

    def __str__(self):
        return f'Company details for {self.name}'

class VerificationCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length = 6, default = "000000")
    created = models.DateTimeField(auto_now_add = True)
    updated = models.DateTimeField(auto_now = True)
    def __str__(self):
        return "Mail code object"