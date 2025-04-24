from django.middleware.csrf import get_token
from django.shortcuts import render
from django.urls import reverse
from .models import *
from django.http import HttpResponseRedirect
from django.db  import IntegrityError
import random, json
from django.views.decorators.clickjacking import xframe_options_sameorigin
from .serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.core.mail import send_mail
# Create your views here.

def checkAuth(_request):
    cookies = _request.headers.get("Authorization").split("Token")[1].strip()
    try:
        token = Token.objects.get(key = cookies)
        user = token.user
        return user
    except Token.DoesNotExist:
        return None

def checkValidOtp(_otp, _email):
    try:
        VerificationCode.objects.get(code = _otp, email = _email)
        return True
    except VerificationCode.DoesNotExist:
        return False

def evaluateCart(_cart):
    items = CartItem.objects.filter(cart = _cart)
    itemCount = 0
    totalPrice = 0
    for _ in items:
        itemCount += _.quantity
        totalPrice += int(_.item.price) * int(_.quantity)
    _cart.total_item = itemCount
    _cart.total_cost = totalPrice
    _cart.save()
    return _cart

def validator(_string):
    acceptables = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890-_@.+"
    for _ in _string:
        if _ not in acceptables:
            return False
    return True


@api_view(["GET", "POST"])
def login_request(request):
    if request.method == 'POST':
        
        try:
            
            username = str(request.POST['username']).strip()
            password = str(request.POST['password1']).strip()
            if username == "" or password == "":
                return Response({'err' : 'Username or Password incorrect'}, status = 400)
            if not validator(username) or not validator(password):
                return Response({'err' : 'Username or Password incorrect'}, status = 400)

            user = authenticate(request, username = username, password = password)
            
            if user is not None:
                token, created = Token.objects.get_or_create(user = user)
                print(token.key)
                return Response({'user' : request.user.username, "sessionID" : token.key}, status = 200)
            else:
                context = {'err':'Invalid username or password'}
                return Response(context , status = 400)
        except (KeyError, Customer.DoesNotExist):
            context = {'err':'User Does Not Exist'}
            return render(request, 'base/login.html', context)
    else:

        return render(request, 'base/login.html')

@api_view(['POST'])
def registration_request(request):
    # get form data
    try:
        first_name = request.POST['firstname'].strip()
        last_name = request.POST['lastname'].strip()
        username = request.POST['username'].strip()
        email = request.POST['email'].strip()
        password1 = request.POST['password1'].strip()
        password2 = request.POST['password2'].strip()
        otp = request.POST['otp'].strip()
        # check that otp is valid
        otpValid = checkValidOtp(otp, email)
        if not otpValid:
            return Response({"err" : "Invalid verification code"}, status = 400)
        if password1 != password2:
            return Response({'err' : 'Your passwords didn\'t match'}, status = 403)
        # create user
        new_user = User.objects.create_user(username=username, first_name = first_name, last_name =last_name, password=password1, email= email)
        new_user.save()
        customer = Customer.objects.create(user = new_user, first_name = first_name, last_name = last_name, email = email)
        token, created = Token.objects.get_or_create(user = new_user)
        userData = UserSerializer(new_user).data
        return Response({'user':userData, 'token' : token.key}, status = 200)
    except (IntegrityError):
        return Response({'err': 'A user with this username already exists.'}, status = 400)

@api_view(['GET'])
def logout_request(request):
    cookies = request.headers.get("Authorization").split("Token")[1].strip()
    try:
        Token.objects.get(key = cookies).delete()
        return Response({"msg" : "Signed out succesfully."}, status = 200)
    except Token.DoesNotExist:
        return Response({"err" :"Failed to sign out."}, status = 400)


@api_view(['GET', 'POST'])
def store(request):
    
    # gather generic data
    _products = Product.objects.all().order_by("?")
    products = ProductSerializer(_products, many=True)
    _cats = Category.objects.all().order_by('?')[:5]
    cats = CategorySerializer(_cats, many = True)
    
    for _ in cats.data:
        _prodForCat = Product.objects.filter(categories = _['id']).order_by('?')
        prodForCat = ProductSerializer(_prodForCat, many = True)
        _['products'] = prodForCat.data
    
    user = checkAuth(request)   # check auth. returns None is not authenticated
    if user:
        _customer = Customer.objects.get(user = user)
        customer =  CustomerSerializer(_customer).data
        customer_cart, created = Cart.objects.get_or_create(customer = _customer)
        cart_data = CartSerializer(customer_cart).data
        userData = UserSerializer(user).data
        context = {'products': products.data, 'customer': customer, 'customer_cart': cart_data, 'cats':cats.data, 'user':userData}
        return Response(context, status = 200)
    else:
        context={'products': products.data, 'cats':cats.data }
        return Response(context, status = 200)

@api_view(['GET'])
def category(request):  # category view
    # serialize catalouge
    _cats = Category.objects.all()
    cats = CategorySerializer(_cats, many=True)
    context = {'categories': cats.data}
    return Response(context, status = 200)

def new(request):
    if request.user.is_authenticated:

        customer =  Customer.objects.get(user = request.user)
        customer_cart, created = Cart.objects.get_or_create(customer = customer)
        products = Product.objects.all().order_by('-time_added')[:20]
        context = {'products':products, 'customer':customer, 'customer_cart': customer_cart}
        return render(request, 'base/new.html', context)
    else:
        products = Product.objects.all().order_by('-time_added')[:20]
        context = {'products':products}
        return render(request, 'base/new.html', context)

@api_view(['GET'])
def cat(request, slug):
    # get cat object and all mathcing products; serailize
    _cat = Category.objects.get(slug = slug)
    _products = Product.objects.filter(categories = _cat)
    cat = CategorySerializer(_cat).data
    products = ProductSerializer(_products, many = True).data

    if request.user.is_authenticated:
        customer =  Customer.objects.get(user = request.user)
        customer_cart, created = Cart.objects.get_or_create(customer = customer)
        context = {'products':products, 'cat': cat, 'customer':customer, 'customer_cart': customer_cart}
        return render(request, 'base/cat.html', context)
    else:
        # return
        context = {'products':products, 'cat': cat}
        return Response(context, status = 200)

@xframe_options_sameorigin
def test(request, catslug):
    if request.user.is_authenticated:
        cat = Category.objects.get(slug = catslug)

        products = Product.objects.filter(categories = cat).order_by('-time_added')[:10]
        context = {'products':products, 'cat':cat}
        return render(request, 'base/test.html', context)
    else:

        cat = Category.objects.get(slug = catslug)

        products = Product.objects.filter(categories = cat).order_by('-time_added')[:10]
        context = {'products':products, 'cat':cat}
        return render(request, 'base/test.html', context)

@xframe_options_sameorigin
def catframe(request):
    if request.user.is_authenticated:

        cat = Category.objects.all()[:10]
        context = {'cat':cat}
        return render(request, 'base/catframe.html', context)
    else:
        cat = Category.objects.all()[:10]
        context = {'cat':cat}
        return render(request, 'base/catframe.html', context)

@api_view(['GET'])
def product(request, prodslug):
    product = ProductSerializer(Product.objects.get(slug = prodslug)).data
    if request.user.is_authenticated:
        customer = Customer.objects.get(user = request.user)
        context ={'customer': customer, 'product':product}
        return render (request, 'base/product.html', context)
    else:
        context ={ 'product':product}
        return Response(context, status = 200)

@api_view(["GET"])
def more(request, prodslug):    # more like product
    # get product and all categories associated
    product = Product.objects.get(slug = prodslug)
    cats = product.categories.all()
    # get all id of associated categories and store in list
    catsId = []
    for _ in cats:
        catsId.append(_.id)
    # filter all objects matching categories
    products = ProductSerializer(Product.objects.filter(categories__in = catsId).order_by("?"), many = True).data
    context = {'more' : products}
    return Response(context, status = 200)

def cart(request):
    if request.user.is_authenticated:

        customer =  Customer.objects.get(user = request.user)
        customer_cart, created = Cart.objects.get_or_create(customer = customer)
        customer_cart.save()
        items = CartItem.objects.filter(cart = customer_cart)
        total = 0

        for item in items:

            price = item.item.price
            quantity = item.quantity
            item.ppi = price * quantity

            total += item.ppi
        customer_cart.total_cost = total
        customer_cart.save()


        context = {'customer': customer, 'total':total, 'items':items, 'customer_cart': customer_cart}
        return render(request, 'base/cart.html', context)
    else:
        return HttpResponseRedirect(reverse('store:login'))


def update(request, id, do):
    if request.user.is_authenticated:
        cart = Cart.objects.get(customer = Customer.objects.get(user = request.user))
        item = CartItem.objects.get(id = id)

        if do == 'up':
            item.quantity +=1
            cart.total_item += 1
        if do == 'down':
            item.quantity -=1
            cart.total_item -= 1
        item.save()
        cart.save()
        if item.quantity < 1:
            item.delete()
            return HttpResponseRedirect(reverse('store:cart'))

        return HttpResponseRedirect(reverse('store:cart'))
    else:
        return HttpResponseRedirect(reverse('store:login'))




@api_view(['GET'])
def checkout(request):
    user = checkAuth(request)

    if not user:
        return Response({'path' : "/auth"}, status = 301)

    customer =  Customer.objects.get(user = user)
    customer_cart, created = Cart.objects.get_or_create(customer = customer)
    customer_cart = evaluateCart(customer_cart)
    items = CartItem.objects.filter(cart = customer_cart)
    shipping = ShippingInformation.objects.filter(customer = customer)

    products = []

    for _ in items:
        _product = Product.objects.get(id = _.item.id)
        product = ProductSerializer(_product).data
        product['quantity'] = _.quantity
        product['totalCost'] = str(int(_.quantity) * int(_product.price))
        products.append(product)

    cartData = CartSerializer(customer_cart).data
    shippingData = ShippingInformationSerializer(shipping, many = True).data

    context = {'shipping':shippingData, 'items':products, 'customer_cart': cartData}
    return Response(context, status = 200)

@api_view(['POST'])
def add_to_cart(request):
    user = checkAuth(request)
    if not user:
        return Response({'path' : '/auth'} , status = 301)
    _id = int(request.data['itemID'])
    print(request.data)
    
    try:

        update = int(str(request.data['update']).strip())
    except ValueError:
        return Response({"err" : 'Number of items must be numeric. If you are using commas ",", remove them and all other special characters'}, status = 400)

    product = Product.objects.get(pk = _id)
    cart, created = Cart.objects.get_or_create(customer = Customer.objects.get(user = user))

    if update < 0:  # just adding one
        # check if this item already exists in cart
        try:
            cartItem = CartItem.objects.get(cart = cart, item = product)
            cartItem.quantity += 1  # increase wuantity if so
            cartItem.save()
        except CartItem.DoesNotExist:
            CartItem.objects.create(item = product, cart = cart, quantity= 1)   # create new item
        msg = f"{product.name} was added to cart. Click on cart to change order quantity."
    elif update == 0:
        _carts = CartItem.objects.filter(cart = cart, item = product)
        for _ in _carts:
            _.delete()
        msg = f'{product.name} was deleted from your cart succesfully.'
        
    else:
        _cartItem = CartItem.objects.get(item = product, cart = cart)
        _cartItem.quantity = update
        _cartItem.save()
        msg = f"{update} {product.name}(s) placed in cart"

    cart = evaluateCart(cart)
    
    return Response({'cartCount' : cart.total_item, "msg" : msg}, status = 200)

def details(request, catslug, prodslug):
    if request.user.is_authenticated:
        customer = Customer.objects.get(user = request.user)
        customer_cart = Cart.objects.get(customer = customer)
        cat = Category.objects.get(slug = catslug)
        product = Product.objects.get(slug = prodslug)
        context = {'cat':cat, 'product':product, 'customer':customer, 'customer_cart':customer_cart}
        return render(request, 'base/details.html', context)
    else:
        return HttpResponseRedirect(reverse('store:login'))


@api_view(['GET'])
def payment(request, tfid):
    user = checkAuth(request)
    if not user:
        return Response({'path': '/auth'}, status = 301)

    customer = Customer.objects.get(user = user)
    customer_cart, created = Cart.objects.get_or_create(customer = customer)
    ship = ShippingInformation.objects.get(id = tfid)
    print(ship)
    order_id = random.randint(2222222222222222,9999999999999999)
    cartData = CartSerializer(customer_cart).data
    order = Order.objects.create(customer = customer, order_id = order_id,
            ship_p1 = f"{ship.street}, {ship.street2}", ship_p2 = f"{ship.city},{ship.state}", ship_p3 = f"{ship.country}, {ship.mobile}", total = customer_cart.total_cost)
    cartItems = CartItem.objects.filter(cart = customer_cart)
    for _ in cartItems:
        OrderItem.objects.create(order = order, item_name = _.item.name, quantity = _.quantity, unit_price = _.item.price)

    context = {'order_id' : order.order_id}
    return Response(context, status = 200)


@api_view(['GET', 'POST'])
def has_paid(request, orderId):
    user = checkAuth(request)   # returns nonw for unauth users
    try:
        order = Order.objects.get(order_id = orderId)
    except Order.DoesNotExist:
        return Response({'err' : 'The specified order could not be found.'}, status = 200)


    if not user:    # not authenticated
        return Response({'path' : '/auth'}, status = 301)

    if request.method == "POST":
        # mark as paid and save
        order.hasPaid = True
        order.save()
        return Response({'msg' : 'seen'}, status = 200)
    
    if order.hasPaid:
        if order.successful != None:
            # order has been processed
            print(order.successful)
            context = {'amount' : f'{order.total}', 'status' : order.successful}
        else:    
            # alert has already been paid. Show pending    
            context = {'amount' : f'{order.total}', 'hasPaid' : True}
        return Response(context, status = 200)
    return Response({'amount' : f'{order.total}'}, status = 200)

    
def order_status(request, ship_id, status, transaction_id, tx_ref):
    if request.user.is_authenticated:
        customer = Customer.objects.get(user = request.user)

        customer_cart = Cart.objects.get(customer = customer)
        status = status
        transaction_id = transaction_id
        tx_ref = tx_ref

        context={'status':status, 'tx_ref':tx_ref, 'transaction_id':transaction_id, 'customer_cart' :customer_cart, 'customer':customer}
        return render(request, 'base/order_test.html', context)
    else:
        return HttpResponseRedirect(reverse('store:login'))



@api_view(['POST'])
def create_shipping(request, coe):
    user = checkAuth(request)
    if user:
        customer = Customer.objects.get(user = user)
        if coe == 'create':
            request.method == "POST"
            address = request.POST['address1']
            address2 = request.POST['address2']
            city = request.POST['city']
            state = request.POST['state']
            number = request.POST['number']
            country = request.POST['country']
            new_ship = ShippingInformation.objects.create(customer = customer, street = str(address), street2 = str(address2),
                            city = str(city), state = str(state), mobile = str(number), country = country)
            new_ship.save()
        if coe == 'delete':
            ShippingInformation.objects.get(pk = request.data['id']).delete()
            pass

        shipping = ShippingInformationSerializer(ShippingInformation.objects.filter(customer = customer), many = True).data
        context = {'shipping' : shipping}
        return Response(context, status = 200)
    else:
        return Response({'path' : "/auth"}, status = 301)


def change(request):
    if request.user.is_authenticated:

        request.method == 'POST'
        customer = Customer.objects.get(user = request.user)
        first = request.POST['fname']
        last = request.POST['lname']
        email = request.POST['email']
        customer.first_name = first
        customer.last_name = last
        customer.email = email
        customer.save()
        return HttpResponseRedirect(reverse('store:checkout'))
    else:
        return HttpResponseRedirect(reverse('store:login'))

def empty(request):
    if request.user.is_authenticated:

        customer = Customer.objects.get(user = request.user)
        cart = Cart.objects.get(customer = customer)
        items = CartItem.objects.filter(cart = cart)
        if None:
            pass
        else:
            cart.delete()
            return HttpResponseRedirect(reverse('store:cart'))
    else:
        return HttpResponseRedirect(reverse('store:login'))

@api_view(['GET'])
def profile(request):
    user = checkAuth(request)

    if not user:    # not auth
        return Response(status = 301)
    
    # generate customer data
    customer = Customer.objects.get(user = user)
    customerData = CustomerSerializer(customer).data
    customerData['Username'] = user.username

    # generate order data
    _orders = Order.objects.filter(customer = customer).order_by('-time')
    success = 0
    failed = 0
    pending = 0
    for _ in _orders:
        match _.successful:
            case None:
                pending += 1
            case True:
                success += 1
            case False:
                failed += 1
    orders = {'Successful Orders' : success, "Failed Orders" : failed, "Pending" : pending}

    context = {'customer': customerData, 'orders':orders}
    return Response(context, status = 200)




def search(request):
    if request.method == 'POST':

        if request.user.is_authenticated:
            customer = Customer.objects.get(user =  request.user)
            customer_cart = Cart.objects.get(customer = customer)
            search = request.POST['search']
            search = str(search)
            products = Product.objects.filter(name__icontains=search)
            cats = Category.objects.filter(name1__icontains = search)
            cats2 = Category.objects.filter(name2__icontains = search)
            context = {'customer': customer, 'customer_cart': customer_cart, 'search':search, 'products':products, 'cats': cats, 'cats2':cats2}
            return render(request, 'base/search.html', context)

        else:
            
            search = request.POST['search']
            products = Product.objects.filter(name__icontains=search)
            cats = Category.objects.filter(name1__icontains = search)
            cats2 = Category.objects.filter(name2__icontains = search)
            context = {'search':search, 'products':products, 'cats':cats, 'cats2':cats2}
            return render(request, 'base/search.html', context)

@api_view(['GET'])
def get_global_context(request): #get global context
    user = checkAuth(request)
    
    # general data
    company = CompanyDetailSerializer(CompanyDetail.objects.first())

    context = {'company' : company.data, 'cartCount' : 0}
    
    # auth user data
    if user:
        print("authenticated")
        userData = UserSerializer(user).data
        cartCount, created = Cart.objects.get_or_create(customer = Customer.objects.get(user = user))
        cartCount = cartCount.total_item
        context['user'] = userData
        context['cartCount'] = cartCount
    return Response(context, status = 200)

@api_view(['GET'])
def get_csrf(request):
    token = get_token(request)
    context = {'csrfToken' : token}
    return Response(context , status =200)

@api_view(['GET', 'POST'])
def getOtp(request):
    email = str(request.data['email']).strip()
    otp = str(random.randint(100000, 900000))
    vcode, created = VerificationCode.objects.get_or_create(email = email)
    vcode.code = otp
    vcode.save()
    send_mail("subject", f"Welcome, your verification code is {otp}", "admin@artmarketplace.online", [email], fail_silently = False)
    return Response(status = 200)

@api_view(['GET'])
def getCart(request):
    user = checkAuth(request)
    if not user:
        return Response({'path' : "/auth"}, status = 301)
    cart, created = Cart.objects.get_or_create(customer = Customer.objects.get(user = user))
    _cartItems = CartItem.objects.filter(cart = cart)
    cartItems = []
    for _ in _cartItems:
        product = ProductSerializer(Product.objects.get(id = _.item.id)).data
        product['quantity'] = _.quantity
        product['total'] = str(int(_.quantity) * product['price'])
        cartItems.append(product)
    cartData = CartSerializer(cart).data
    context = {'cart' : cartData, 'cartItems' : cartItems}
    return Response(context, status = 200)

@api_view(['GET'])
def history(request):
    user = checkAuth(request)
    if not user:
        return Response({'path' : '/auth'}, status = 301)
    
    # generater order data
    cus = Customer.objects.get(user = user)
    _orders = Order.objects.filter(customer = cus)
    orders = OrderSerializer(_orders, many = True).data

    context = {'orders' : orders}
    return Response(context, status = 200)

@api_view(['GET'])
def summary(request, order_id):
    user = checkAuth(request)
    if not user:
        return Response({'path' : '/auth'}, status = 301)
    
    # generic variables
    cus = Customer.objects.get(user = user)
    order = Order.objects.get(customer = cus, order_id = order_id)

    # get items data
    _items = OrderItem.objects.filter(order = order)
    items = OrderItemSerializer(_items, many= True).data
    for _ in items:
        _['total'] = int(_['unit_price']) * int(_['quantity'])

    # get order data
    order = OrderSerializer(order).data
    context = {'items' : items, 'order' : order}
    return Response(context, status = 200)
    

    
