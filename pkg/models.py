from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class State(db.Model):
    __tablename__ = 'states'
    state_id = db.Column(db.Integer, primary_key=True)
    state_name = db.Column(db.String(15), nullable=False)


class Farmer(db.Model):
    __tablename__ = 'farmers'
    farm_id = db.Column(db.Integer, primary_key=True)
    farm_name = db.Column(db.String(50), nullable=False)
    farmer_first_name = db.Column(db.String(45), nullable=False)
    farmer_last_name = db.Column(db.String(45), nullable=False)
    farmer_phone_number = db.Column(db.String(20), nullable=False)
    farmer_email = db.Column(db.String(20), nullable=False)
    farmer_state_id = db.Column(db.Integer, db.ForeignKey('states.state_id'), nullable=False)
    farmer_address = db.Column(db.Text, nullable=False)
    farmer_username = db.Column(db.String(20), unique=True, nullable=False)
    farmer_image = db.Column(db.String(200), unique=True, nullable=True)
    farmer_password = db.Column(db.String(200), nullable=False)
    date_registered = db.Column(db.DateTime(), default=datetime.utcnow)
    farmer_account = db.Column(db.Enum('activated', 'restricted'),
                               nullable=False,
                               server_default="activated")
    products = db.relationship('Product', back_populates='farmer', lazy=True)


class Category(db.Model):
    __tablename__ = 'category'
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(25), nullable=False)
    product = db.relationship('Product', back_populates='category')


class Product(db.Model):
    __tablename__ = 'products'
    pro_id = db.Column(db.Integer, primary_key=True)
    pro_name = db.Column(db.String(300), nullable=False)
    pro_category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=False)
    qua_avail = db.Column(db.Float, nullable=False)
    price_per_unit = db.Column(db.Numeric(10, 2), nullable=False)
    farm_id = db.Column(db.Integer, db.ForeignKey('farmers.farm_id'), nullable=False)
    pro_picture = db.Column(db.String(100))
    pro_status = db.Column(db.Enum('published', 'unpublished', 'activated'),
                           nullable=False,
                           server_default="activated")

    order_items = db.relationship('OrderItem', back_populates='product', lazy=True)  # One-to-Many
    category = db.relationship('Category', back_populates='product')
    farmer = db.relationship('Farmer', back_populates='products', lazy=True)


class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    rest_id = db.Column(db.Integer, primary_key=True)
    rest_name = db.Column(db.String(40), nullable=False)
    rest_phone_number = db.Column(db.String(20), nullable=False)
    rest_address = db.Column(db.Text, nullable=False)
    rest_email = db.Column(db.String(45), nullable=False)
    rest_image = db.Column(db.String(200), unique=True, nullable=True)
    rest_password = db.Column(db.Text(100), nullable=False)
    date_registered = db.Column(db.DateTime(), default=lambda: datetime.utcnow())
    rest_account = db.Column(db.Enum('activated', 'restricted'),
                             nullable=False,
                             server_default="activated")
    orders = db.relationship('Order', back_populates='restaurant', lazy=True)


class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.rest_id'), nullable=False)
    order_date = db.Column(db.DateTime(), default=datetime.utcnow)
    total_amt = db.Column(db.Numeric(10, 2), nullable=False)
    order_stat = db.Column(db.String(45), nullable=False)
    order_reference = db.Column(db.String(45), nullable=False)

    restaurant = db.relationship('Restaurant', back_populates='orders')  # Backref to Restaurant
    order_items = db.relationship('OrderItem', back_populates='order', lazy=True)


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    pro_id = db.Column(db.Integer, db.ForeignKey('products.pro_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    order = db.relationship('Order', back_populates='order_items')  # Backref to Order
    product = db.relationship('Product', back_populates='order_items')


class Payment(db.Model):
    __tablename__ = 'payments'
    pay_id = db.Column(db.Integer, primary_key=True)
    pay_order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    pay_rest_id = db.Column(db.Integer, db.ForeignKey('restaurants.rest_id'))
    pay_farm_id = db.Column(db.Integer, db.ForeignKey('farmers.farm_id'))
    pay_amt = db.Column(db.Float(), nullable=True)
    pay_status = db.Column(db.Enum('pending', 'paid', 'failed'),
                           nullable=False,
                           server_default="pending")

    reference_num = db.Column(db.String(45), nullable=False)
    date_paid = db.Column(db.DateTime(), default=datetime.utcnow)
    paystack_transaction_reference = db.Column(db.String(200), nullable=True)

    rest = db.relationship("Restaurant", backref="mypayments")


class Admin(db.Model):
    __tablename__ = 'admin'
    admin_id = db.Column(db.Integer, primary_key=True)
    admin_username = db.Column(db.String(75), unique=True, nullable=False)
    admin_password = db.Column(db.String(200), nullable=False)
    admin_last_login = db.Column(db.DateTime, nullable=True)


class CartItem(db.Model):
    __tablename__ = 'cart_items'
    cart_item_id = db.Column(db.Integer, primary_key=True)
    pro_id = db.Column(db.Integer, db.ForeignKey('products.pro_id'), nullable=False)
    cart_quantity = db.Column(db.Integer, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.rest_id'), nullable=False)
