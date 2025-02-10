import requests
import os, random, json
from flask import current_app as app
from flask import render_template, redirect, flash, request, session
from flask_wtf.csrf import CSRFError
from flask_wtf.csrf import generate_csrf
from werkzeug.security import generate_password_hash, check_password_hash

from pkg.forms import Restaurantsignform, Restaurantlogform
from pkg.models import db, Restaurant, Farmer, Product, Category, CartItem, Order, OrderItem, Admin, Order, Payment


@app.after_request
def after_request(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


@app.errorhandler(CSRFError)
def handle_csrf(e):
    return render_template('csrf_error.html', reason=e.description)


# Route for the home page
@app.route('/')
def home():
    farmer_id = session.get("farmer_loggedin")
    restaurant_id = session.get("restaurant_loggedin")
    admin_id = adminn_id = session.get("admin_loggedin")

    farmer_deets = None
    rest_deets = None
    admin_deets = None
    products = (
        db.session.query(Product)
        .distinct(Product.pro_category_id)
        .limit(4)
        .all()
    )

    cart_items = []
    if 'restaurant_loggedin' in session:
        restaurant_id = session['restaurant_loggedin']
        user_cart_items = db.session.query(CartItem).filter_by(restaurant_id=restaurant_id).all()
        for item in user_cart_items:
            product = db.session.query(Product).filter_by(pro_id=item.pro_id).first()
            if product:
                cart_items.append({
                    'pro_id': item.pro_id,
                    'cart_item_id': item.cart_item_id,
                    'product_name': product.pro_name,
                    'quantity': item.cart_quantity,
                    'price_per_unit': float(product.price_per_unit),
                    'total_price': float(item.cart_quantity * product.price_per_unit)
                })

    if farmer_id:
        farmer_deets = db.session.query(Farmer).get(farmer_id)

    if restaurant_id:
        rest_deets = db.session.query(Restaurant).get(restaurant_id)

    if admin_id:
        admin_deets = db.session.query(Admin).get(admin_id)

    return render_template('index.html', farmer_deets=farmer_deets, rest_deets=rest_deets, admin_deets=admin_deets, products=products, cart_items=cart_items)


# Route for the products page
@app.route('/products/', methods=['GET'])
def products():
    product_name = request.args.get('product_name')  # Get the query parameter for product_name

    if product_name:
        category = Category.query.filter_by(category_name=product_name).first()
        products_ = db.session.query(Product).filter(
            Product.pro_category_id == category.category_id,
            Product.pro_status == 'published'  # Only include published products
        ).all() if category else []
    else:
        products_ = db.session.query(Product).filter(
            Product.pro_status == 'published'  # Only include published products
        ).all()

    cart_items = []
    if 'restaurant_loggedin' in session:
        restaurant_id = session['restaurant_loggedin']
        user_cart_items = db.session.query(CartItem).filter_by(restaurant_id=restaurant_id).all()
        for item in user_cart_items:
            product = db.session.query(Product).filter_by(pro_id=item.pro_id).first()
            if product:
                cart_items.append({
                    'pro_id': item.pro_id,
                    'cart_item_id': item.cart_item_id,
                    'product_name': product.pro_name,
                    'quantity': item.cart_quantity,
                    'price_per_unit': float(product.price_per_unit),
                    'total_price': float(item.cart_quantity * product.price_per_unit)
                })

    return render_template('user_restaurant/products.html', products=products_, cart_items=cart_items)


@app.route('/product/search/', methods=['POST'])
def search_product():
    search_query = request.form.get('search', '').strip()  # Get search term
    if not search_query:
        return ''  # Return empty response if no input

    # Perform database search (modify based on your DB schema)
    results = Product.query.filter(Product.pro_name.ilike(f"%{search_query}%")).all()

    # Render partial HTML with search results
    return render_template('partials/search_results.html', products=results)

# Route for the cart page
@app.route('/cart/', methods=['GET'])
def get_cart():
    if 'restaurant_loggedin' not in session:
        flash('You need to log in to view your cart!', 'error')
        return redirect('/restaurant-login/')

    restaurant_id = session['restaurant_loggedin']
    cart_items = db.session.query(CartItem).filter_by(restaurant_id=restaurant_id).all()

    cart_details = []
    for item in cart_items:
        product = db.session.query(Product).filter_by(pro_id=item.pro_id).first()
        if product:
            cart_details.append({
                'pro_id': item.pro_id,
                'pro_picture': product.pro_picture,
                'cart_item_id': item.cart_item_id,
                'product_name': product.pro_name,
                'quantity': item.cart_quantity,
                'price_per_unit': float(product.price_per_unit),
                'total_price': float(item.cart_quantity * product.price_per_unit)
            })

    return render_template('user_restaurant/cart.html',
                           cart_items=cart_details)


@app.route('/cart/add/', methods=['POST'])
def add_to_cart():
    if 'restaurant_loggedin' not in session:
        flash('You need to log in as a restaurant owner to add items to the cart!', 'errors')
        return redirect('/restaurant-login/')

    restaurant_id = session['restaurant_loggedin']
    pro_id = request.form.get('pro_id')
    quantity = request.form.get('quantity', type=int)

    if not pro_id or quantity <= 0:
        flash('Invalid product or quantity', 'errors')
        return redirect('/products/')

    existing_cart_item = db.session.query(CartItem).filter_by(pro_id=pro_id, restaurant_id=restaurant_id).first()

    if existing_cart_item:
        existing_cart_item.cart_quantity += quantity
    else:
        new_cart_item = CartItem(
            pro_id=pro_id,
            cart_quantity=quantity,
            restaurant_id=restaurant_id
        )
        db.session.add(new_cart_item)

    db.session.commit()
    flash('Item added to cart!', 'success')
    return redirect('/cart/')


@app.route('/cart/update/<int:cart_item_id>/', methods=['POST'])
def update_cart(cart_item_id):
    if 'restaurant_loggedin' not in session:
        flash('You need to log in to update the cart!', 'error')
        return redirect('/restaurant-login/')

    quantity = request.form.get('quantity', type=int)

    if quantity <= 0:
        flash('Invalid quantity!', 'error')
        return redirect('/cart/')

    cart_item = db.session.query(CartItem).filter_by(cart_item_id=cart_item_id).first()

    if cart_item:
        cart_item.cart_quantity = quantity
        db.session.commit()
        flash('Cart item updated!', 'success')
    else:
        flash('Cart item not found!', 'error')

    return redirect('/cart/')


@app.route('/cart/remove/<int:cart_item_id>/', methods=['POST'])
def remove_from_cart(cart_item_id):
    if 'restaurant_loggedin' not in session:
        flash('You need to log in to remove items from the cart!', 'error')
        return redirect('/restaurant-login/')

    cart_item = db.session.query(CartItem).filter_by(cart_item_id=cart_item_id).first()

    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart!', 'success')
    else:
        flash('Cart item not found!', 'error')

    return redirect('/cart/')


@app.route('/checkout/', methods=['GET', 'POST'])
def checkout():
    restaurant_id = session['restaurant_loggedin']
    cart_items = db.session.query(CartItem).filter_by(
        restaurant_id=restaurant_id).all()
    if 'restaurant_loggedin' not in session:
        flash('You need to log in to proceed with checkout!', 'error')
        return redirect('/restaurant-login/')

    if not cart_items:
        flash('Your cart is empty!', 'error')
        return redirect('/cart/')

    if request.method == "GET":
        ref_no = session.get('refno')
        orddeets = db.session.query(Order).filter(Order.order_reference == ref_no).first()
        if not orddeets:
            orddeets = db.session.query(Order).filter_by(
                restaurant_id=restaurant_id,
                order_stat='Pending').first()
            if not orddeets:
                return redirect('/cart/')
        session['refno'] = orddeets.order_reference
        return redirect('/pay/')

    total_amt = sum(
        item.cart_quantity * db.session.query(Product.price_per_unit).filter_by(pro_id=item.pro_id).scalar()
        for item in cart_items
    )
    ref = int(random.random() * 10000000000)
    new_order = Order(
        restaurant_id=restaurant_id,
        order_reference=ref,
        total_amt=total_amt,
        order_stat='Pending'
        # farm_id = 

    )
    db.session.add(new_order)
    db.session.commit()
    session['refno'] = ref

    flash('Order placed successfully!', 'success')
    return redirect('/pay/')


@app.route('/pay/', methods=['GET', 'POST'])
def restaurant_payment():
    restaurant_id = session.get("restaurant_loggedin")
    ref_no = session.get('refno')

    if not restaurant_id:
        flash('Error: You must be logged in.')
        return redirect('/restaurant-login/')

    if not ref_no:
        flash('Error: Please start the transaction from here.')
        return redirect('/products/')

    rest_deets = db.session.query(Restaurant).get(restaurant_id)

    orddeets = db.session.query(Order).filter(Order.order_reference == ref_no).first()
    print(orddeets)
    if request.method == 'GET':
        return render_template('user_restaurant/pay.html',
                               rest_deets=rest_deets,
                               trxdeets=orddeets)

    pay_deets = Payment(
        pay_order_id=orddeets.order_id,
        pay_amt=orddeets.total_amt,
        reference_num=orddeets.order_reference,
        pay_rest_id=orddeets.restaurant_id
    )

    db.session.add(pay_deets)
    db.session.commit()

    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk_test_ccb7954503326136a4d8e698a2d13c455982ade2"
    }
    amt_kobo = int(orddeets.total_amt * 100)  #

    data = {
        "reference": ref_no,
        "amount": amt_kobo,
        "email": rest_deets.rest_email,
        "callback_url": "http://127.0.0.1:5000/payment_validate"
    }

    response = requests.post(url, headers=headers,
                             data=json.dumps(data))
    print(response.content)
    json_response = response.json()
    print(json_response)

    status = json_response['status']
    if status:
        authurl = json_response['data']['authorization_url']
        return redirect(authurl)
    flash('Error: ' + json_response.get(
        'message', 'Something went wrong'))
    return redirect('/products/')


@app.route('/restaurant-signup/', methods=['GET', 'POST'])
def rest_signup():
    restaurant = Restaurantsignform()
    if request.method == 'GET':
        return render_template('user_restaurant/restaurant_signup.html', restaurant=restaurant)
    else:
        if restaurant.validate_on_submit():
            name = request.form.get('name')
            address = request.form.get('address')
            contact_email = request.form.get('contact_email')
            contact_num = request.form.get('contact_num')
            password = request.form.get('password')
            cpassword = request.form.get('cpassword')
            if password != cpassword:
                flash('Password mismatch, please try again', 'error')
                return redirect('/restaurant-signup/')
            else:
                hashed = generate_password_hash(password.strip())
                push_to_db = Restaurant(
                    rest_name=name,
                    rest_phone_number=contact_num,
                    rest_address=address,
                    rest_email=contact_email,
                    rest_password=hashed
                )
                db.session.add(push_to_db)
                db.session.commit()
                print(f"Hashed Password from DB: {hashed}")
                print(f"Plain Password: {password}")
                flash('An account has been created for you', 'success')
                return redirect('/restaurant-login/')

    return render_template('user_restaurant/restaurant_signup.html', restaurant=restaurant)


@app.route('/restaurant-login/', methods=['GET', 'POST'])
def rest_login():
    restaurant = Restaurantlogform()
    if request.method == "GET":
        return render_template('user_restaurant/restaurant_login.html', restaurant=restaurant)
    else:
        if restaurant.validate_on_submit():
            email = restaurant.email.data
            password = restaurant.password.data
            print(f"Entered Password: {password}")
            check_record = db.session.query(Restaurant).filter(Restaurant.rest_email == email).first()
            print(f"DB Record: {check_record}")

            if check_record:
                if check_record.rest_account == "restricted":
                    flash('Sorry, you cannot log in right now. You can file a complaint at info@harvesthub.com.', 'errors')
                    return redirect('/restaurant-login/')
                else:
                    hashed_password = check_record.rest_password
                    print(f"Hashed Password from DB: {hashed_password}")
                    chk = check_password_hash(hashed_password.strip(), password.strip())
                    print(f"Password Check Result: {chk}")

                    if chk:
                        session["restaurant_loggedin"] = check_record.rest_id
                        return redirect('/restaurant-dashboard/')
                    else:
                        flash('Invalid Password', 'errors')
                        return redirect('/restaurant-login/')
            else:
                flash('Invalid Email', 'errors')
                return redirect('/restaurant-login/')

    return render_template('user_restaurant/restaurant_login.html', restaurant=restaurant)


@app.route('/restaurant-dashboard/')
def restaurant_dashboard():
    restaurant_id = session.get("restaurant_loggedin")
    if restaurant_id:
        restaurant = db.session.query(Restaurant).filter(Restaurant.rest_id == restaurant_id).first()
        paydeets = db.session.query(Payment).filter(Payment.pay_rest_id==restaurant_id, Payment.pay_status=='paid').all()
        if restaurant:
            restaurant_name = f"{restaurant.rest_name}"
            return render_template('user_restaurant/restaurant_dashboard.html', restaurant_name=restaurant_name, paydeets=paydeets)
    flash('errors', 'You need to log in first!')
    return redirect('/restaurant-login/')


@app.route("/restaurant-logout/")
def restaurant_logout():
    session.pop('restaurant_loggedin', None)
    return redirect('/')


@app.route("/payment_validate")
def validate_payment():
   
    reference = request.args.get('reference')
    if not reference:
        return "Invalid request: Missing reference number.", 400  
    payment_details = db.session.query(Payment).filter(Payment.reference_num == reference).first()
    if payment_details and payment_details.pay_status == "paid":
        return redirect("/products/")  # Redirect if payment is already completed

    # Verify the payment with Paystack
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer sk_test_ccb7954503326136a4d8e698a2d13c455982ade2"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        json_response = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error verifying payment: {e}")
        return "Error verifying payment. Please try again later.", 500

    # Extract data from the response
    data = json_response.get("data")
    if not data or data.get("status") != "success":
        print(f"Payment verification failed: {json_response}")
        return render_template('user_restaurant/order_completed.html', successful=False)

    # Update order and payment details
    order_details = db.session.query(Order).filter(Order.order_reference == reference).first()
    if not order_details or not payment_details:
        return "Order or payment details not found.", 404  # Return not found if details are missing

    # Update statuses
    order_details.order_stat = "successful"
    payment_details.pay_status = "paid"
    payment_details.paystack_transaction_reference = data.get('reference')
    cart_items = db.session.query(CartItem
                                  ).filter_by(
        restaurant_id=order_details.restaurant_id).all()
    for item in cart_items:
        order_item = OrderItem(
            order_id=order_details.order_id,
            pro_id=item.pro_id,
            quantity=item.cart_quantity
        )
        db.session.add(order_item)
        db.session.delete(item)
    db.session.commit()

    # Render the success page
    return render_template('user_restaurant/order_completed.html',
                           successful=True)
    
@app.route('/restaurant/profile/', methods=['GET'])
def rest_show_profile():
    rest_id = session.get('restaurant_loggedin')
    if rest_id:
        rest_deets = db.session.query(Restaurant).get(rest_id)
        csrf_token = generate_csrf()  
        return render_template(
            'user_restaurant/rest_show_profile.html', 
            rest_deets=rest_deets,
            csrf_token=csrf_token  
        )
    else:
        flash('errormsg','You must be logged in')
        return redirect('/')
    
@app.route('/restaurant-nav/')
def rest_nav():
    restaurant_id = session.get("restaurant_loggedin")
    print("Restaurant ID from session:", restaurant_id)  # Debugging step
    
    if restaurant_id:
        restaurant = db.session.query(Restaurant).filter_by(rest_id=restaurant_id).first()
        if restaurant:
            rest_name = restaurant.rest_name
            return render_template('user_restaurant/rest_nav.html', rest_name=rest_name)
    
    flash('You need to log in first!', 'error')
    return redirect('/restaurant-login/')



import secrets  

@app.route('/profile/<rest_id>/update/', methods=['GET', 'POST'])
def update_rest_profile(rest_id):
    loggedin_rest_id = session.get('restaurant_loggedin')  
    if not loggedin_rest_id:
        flash('You must be logged in', 'errormsg')
        return redirect("/restaurant_login/")
    
    if str(loggedin_rest_id) != str(rest_id):  
        flash("Unauthorized access.", "errormsg")
        return redirect("/restaurant/profile/")

    rest_deets = db.session.query(Restaurant).get(rest_id)
    
    if not rest_deets:
        flash("Restaurant profile not found", "errormsg")
        return redirect("/restaurant/profile/")

    if request.method == 'POST':
        rest_name = request.form.get("rest_name")
        rest_phone_number = request.form.get("rest_phone_number")
        rest_address = request.form.get("rest_address")
        rest_email = request.form.get("rest_email")

        # Retrieve file data
        file = request.files.get('rest_image')
        allowed_ext = ['.jpg', '.jpeg', '.png', '.gif']
        filename = rest_deets.rest_image  
        
        if file and file.filename:
            _, ext = os.path.splitext(file.filename)
            if ext.lower() in allowed_ext:
                rand_str = secrets.token_hex(10)
                filename = f'{rand_str}{ext}'
                file_path = os.path.join("pkg/static/uploaded", filename)
                file.save(file_path)
            else:
                flash("Your cover image must be an image file", "errormsg")
                return redirect('/restaurant/profile/')

        # Update the restaurant details
        rest_deets.rest_name = rest_name
        rest_deets.rest_phone_number = rest_phone_number
        rest_deets.rest_address = rest_address
        rest_deets.rest_email = rest_email
        rest_deets.rest_image = filename  

        try:
            db.session.flush() 
            db.session.commit()
            flash('Profile details updated successfully', 'feedback')
        except Exception as e:
            db.session.rollback()
            print("Error updating profile:", str(e))
            flash("An error occurred while updating your profile", "errormsg")

        return redirect('/restaurant/profile/')
    
    return redirect('/restaurant/profile/')
