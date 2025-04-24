from django.contrib import admin
from .models import *

# Register your models here.

class CartAdmin(admin.ModelAdmin):
    readonly_fields = ('customer', 'total_item')

class CustomerAdmin(admin.ModelAdmin):
    readonly_fields = ('user', 'first_name', 'last_name', 'email')


admin.site.register(Product)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem)
admin.site.register(ShippingInformation)
admin.site.register(Order)
admin.site.register(Category)
admin.site.register(CompanyDetail)
admin.site.register(OrderItem)