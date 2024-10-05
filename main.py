
from flask import Flask, session, render_template, request, redirect, url_for, flash, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from flask_bootstrap import Bootstrap5
from sqlalchemy import Integer, String, Boolean, Text, Column, ForeignKey, DateTime
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, AddBrand, AddCategory
from flask_uploads import IMAGES, UploadSet, configure_uploads
import secrets
import stripe
# To convert html page to pdf
import pdfkit
from flask_wkhtmltopdf import Wkhtmltopdf
# from setup import setup

from flask_msearch import Search
from flask_migrate import Migrate
import json

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField, SelectField, BooleanField, IntegerField, TextAreaField
from wtforms import FileField
from flask_wtf.file import FileRequired, FileAllowed
from wtforms.validators import DataRequired, URL, Email
from datetime import datetime, date


import os


publishable_key = os.environ.get("publishable_key", "dev")
stripe.api_key = os.environ.get("secret_key", "dev")

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FlaskConfigKey", "dev")

# Initialize wkhtmltopdf
wkhtmltopdf = Wkhtmltopdf(app)
# config = pdfkit.configuration()


# Set destination for uploaded images
app.config["UPLOADED_PHOTOS_DEST"] = os.path.join(basedir, "static/images")
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)


Bootstrap5(app)


# Configure Flask-Login's Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = "Please login first"


# Create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# CREATE DB
class Base(DeclarativeBase):
    pass


# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
db = SQLAlchemy(model_class=Base)
# Initialize the database
db.init_app(app)


# Create and initialize the search app
search = Search(db=db)
search.init_app(app)
migrate = Migrate(app, db)


# CREATE USER TABLE IN DB with the UserMixin
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(1000))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100))
    contact: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(100))
    zipcode: Mapped[str] = mapped_column(String(100))
    profile: Mapped[str] = mapped_column(String(250), nullable=False, default="profile.jpg")
    date_created: Mapped[str] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


    # def __repr__(self):
    #     return "<User %r>" % self.name


with app.app_context():
    db.create_all()


class jsonEncodedDict(db.TypeDecorator):
    impl = db.Text

    def process_bind_param(self, value, dialect):
        if value is None:
            return '{}'
        else:
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return {}
        else:
            return json.loads(value)

# Create the customer order table in the database.
class CustomerOrder(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(100), nullable=False, default="Pending")
    customer_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=False)
    date_created: Mapped[str] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    orders: Mapped[str] = mapped_column(jsonEncodedDict)

    # def __repr__(self):
    #     return "<CustomerOrder %r>" % self.invoice

# Create the product brand table in the database
class Brand(db.Model):
    __tablename__ = "brands"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    products = relationship("Product", back_populates="brand")
    # products = db.relationship('Product', backref='brand', lazy=True)


# Create the product category table in the database.
class Category(db.Model):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    products = relationship("Product", back_populates="category")


with app.app_context():
    db.create_all()


# Create the product table in the database.
class Product(db.Model):

    __tablename__ = "products"
    __searchable__ = ['product_name', 'description']
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_name: Mapped[str] = mapped_column(String(250), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    discount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    colors: Mapped[str] = mapped_column(String(250), nullable=False)

    brand_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("brands.id"))
    brand = relationship("Brand", back_populates="products")
    # brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=False)

    category_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("categories.id"))
    category = relationship("Category", back_populates="products")

    image_1: Mapped[str] = mapped_column(String(250), nullable=False, default="image.jpg")
    image_2: Mapped[str] = mapped_column(String(250), nullable=False, default="image.jpg")
    image_3: Mapped[str] = mapped_column(String(250), nullable=False, default="image.jpg")

    # image_1 = db.Column(db.String(150))
    # image_2 = db.Column(db.String(150))
    # image_3 = db.Column(db.String(150))


with app.app_context():
    db.create_all()


with app.app_context():
    brands = db.session.execute(db.select(Brand)).scalars().all()
    categories = db.session.execute(db.select(Category)).scalars().all()



class AddProduct(FlaskForm):
    brand = SelectField('Select a Brand', choices=[brand.name for brand in brands])
    category = SelectField('Select a Category', choices=[category.name for category in categories])
    product_name = StringField("Product Name", validators=[DataRequired()])
    price = IntegerField("Price", validators=[DataRequired()])
    discount = IntegerField("Discount", default=0)
    stock = IntegerField("Stock", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    colors = TextAreaField("Colors", validators=[DataRequired()])
    image_1 = FileField("Image 1", validators=[FileRequired(), FileAllowed(["jpg", "png", "gif", 'jpeg'])])
    image_2 = FileField("Image 2", validators=[FileRequired(), FileAllowed(["jpg", "png", "gif", 'jpeg'])])
    image_3 = FileField("Image 3", validators=[FileRequired(), FileAllowed(["jpg", "png", "gif", 'jpeg'])])
    submit = SubmitField("Submit")


def MagerDicts(dict1, dict2):
    if isinstance(dict1, list) and isinstance(dict2, list):
        return dict1 + dict2
    elif isinstance(dict1, dict) and isinstance(dict2, dict):
        return dict(list(dict1.items()) + list(dict2.items()))
    return False


@app.route("/")
def home():
    page = request.args.get("page", 1, type=int)
    products = Product.query.filter(Product.stock > 0).order_by(Product.id.desc()).paginate(page=page, per_page=8)
    # brands = db.session.execute(db.select(Brand)).scalars().all()
    # Join the Brand and the Product table, so we don't display empty brands
    brands = Brand.query.join(Product, (Brand.id == Product.brand_id)).all()
    # categories = db.session.execute(db.select(Category)).scalars().all()
    categories = Category.query.join(Product, (Category.id == Product.category_id)).all()
    return render_template("index.html", products=products, brands=brands, categories=categories, datetime=datetime)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        email = request.form.get("email")
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        hash_and_salted_password = generate_password_hash(request.form.get("password"), method="pbkdf2", salt_length=5)

        with app.app_context():
            new_user = User(name=request.form.get("name"),
                            email=request.form.get("email"),
                            password=hash_and_salted_password,
                            country=request.form.get("country"),
                            state=request.form.get("state"),
                            city=request.form.get("city"),
                            contact=request.form.get("contact"),
                            address=request.form.get("address"),
                            zipcode=request.form.get("zipcode"),
                            profile=request.form.get("profile"),

                            )
            db.session.add(new_user)
            db.session.commit()
            # Log in and authenticate user after adding details to database.
            login_user(new_user)
            flash(f"Welcome {form.name.data}. Thank you for registering", "success")
            return redirect(url_for("home"))
    return render_template("register.html", form=form, current_user=current_user, datetime=datetime)



@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = request.form.get("email")
        password = request.form.get("password")
        # Find user by email entered.
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        # Email doesn't exist or password incorrect.
        if not user:
            flash("That email does not exist, please try again.", "danger")
            return redirect(url_for("login"))
        # Check stored password hash against entered password hashed.
        elif not check_password_hash(user.password, password):
            flash("Password incorrect, please try again.", "danger")
            return redirect(url_for("login"))
        else:
            login_user(user)
            flash(f"Welcome! {user.name}")
            return redirect(url_for("home"))
    return render_template("login.html", form=form, current_user=current_user, datetime=datetime)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


# Remove unwanted details from shopping cart
def update_shopping_cart():
    for _key, product in session['Shoppcart'].items():
        session.modified = True
        del product['image']
        del product['colors']
    return update_shopping_cart
# Create a get_order route
@login_required
@app.route('/get_order')
def get_order():
    if current_user.is_authenticated:
        customer_id = current_user.id
        invoice = secrets.token_hex(5)
        update_shopping_cart()
        try:
            order = CustomerOrder(invoice=invoice, customer_id=customer_id, orders=session['Shoppcart'])
            print(order.customer_id)
            db.session.add(order)
            db.session.commit()
            # Clear the Shopping cart
            session.pop('Shoppcart')
            flash("Your order has been sent successfully.", "success")
            return redirect(url_for('orders', invoice=invoice))
        except Exception as e:
            print(e)
            flash("Something went wrong", "danger")
            return redirect(url_for('get_carts'))

    else:
        return redirect(url_for('login'))


# Create the orders route
@login_required
@app.route("/orders/<invoice>")
def orders(invoice):
    if current_user.is_authenticated:
        grand_total = 0
        sub_total = 0
        customer_id = current_user.id
        customer = User.query.filter_by(id=customer_id).first()
        orders = CustomerOrder.query.filter_by(customer_id=customer_id, invoice=invoice).order_by(CustomerOrder.id.desc()).first()
        for _key, product in orders.orders.items():
            discount = (product['discount']/100) * float(product['price'])
            sub_total = float(product['price']) * int(product['quantity'])
            sub_total -= discount
            tax = ("%.2f" % (.06 * float(sub_total)))
            grand_total = ("%.2f" % (1.06 * float(sub_total)))
    else:
        return redirect(url_for("login"))
    return render_template("order.html", invoice=invoice, tax=tax, sub_total=sub_total,
                           grand_total=grand_total,customer=customer, orders=orders, datetime=datetime)


@login_required
@app.route("/get_pdf/<invoice>", methods=["POST"])
def get_pdf(invoice):
    if current_user.is_authenticated:
        grand_total = 0
        sub_total = 0
        customer_id = current_user.id
        if request.method == "POST":
            customer = User.query.filter_by(id=customer_id).first()
            orders = CustomerOrder.query.filter_by(customer_id=customer_id).order_by(CustomerOrder.id.desc()).first()
            for _key, product in orders.orders.items():
                discount = (product['discount']/100) * float(product['price'])
                sub_total = float(product['price']) * int(product['quantity'])
                sub_total -= discount
                tax = ("%.2f" % (.06 * float(sub_total)))
                grand_total = float("%.2f" % (1.06 * sub_total))

            rendered = render_template("pdf.html", invoice=invoice, tax=tax, grand_total=grand_total,
                                     customer=customer, orders=orders)
            pdf = pdfkit.from_string(rendered, False)
            response = make_response(pdf)
            response.headers['content-Type'] = 'application/pdf'
            response.headers['content-Disposition'] = 'inline: filename="+invoice+".pdf'
            return response
    return request(url_for("orders"))


@login_required
@app.route("/payment", methods=["POST"])
def payment():
    invoice = request.form.get('invoice')
    amount = request.form.get('amount')
    customer = stripe.Customer.create(
        email=request.form['stripeEmail'],
        source=request.form['stripeToken'],
    )

    charge = stripe.Charge.create(
        customer=customer.id,
        description='Myshop',
        amount=amount,
        currency='usd',
    )
    orders = CustomerOrder.query.filter_by(customer_id=current_user.id, invoice=invoice).order_by(CustomerOrder.id.desc()).first()
    orders.status = "Paid"
    db.session.commit()
    return redirect(url_for('thanks'))


@app.route("/thanks")
def thanks():
    return render_template("thanks.html", datetime=datetime)



@app.route("/search")
def search():
    search_word = request.args.get('q')
    products = Product.query.msearch(search_word, fields=['product_name', 'description'], limit=6)
    # Display tha brands and categories on the navbar dropdown
    brands = Brand.query.join(Product, (Brand.id == Product.brand_id)).all()
    categories = Category.query.join(Product, (Category.id == Product.category_id)).all()
    return render_template('search.html', products=products, brands=brands, categories=categories, datetime=datetime)


# Display a single product
@app.route("/product/<int:id>", methods=["GET", "POST"])
def show_product(id):
    product = db.get_or_404(Product, id)
    # Display tha brands and categories on the navbar dropdown
    brands = Brand.query.join(Product, (Brand.id == Product.brand_id)).all()
    categories = Category.query.join(Product, (Category.id == Product.category_id)).all()
    return render_template("show_product.html", product=product, brands=brands, categories=categories, datetime=datetime)

# Add products to cart
@app.route("/add_cart", methods=["POST"])
def add_cart():
    try:
        product_id = request.form.get("product_id")
        quantity = request.form.get('quantity')
        colors = request.form.get('colors')
        product = Product.query.filter_by(id=product_id).first()
        if product_id and quantity and colors and request.method == "POST":
            DictItems = {
                product_id:{'name': product.product_name, 'price':product.price, 'discount': product.discount,
                            'color': colors, 'quantity': quantity, 'image': product.image_1, 'colors': product.colors
                            }
            }
            if 'Shoppcart' in session:
                print(session['Shoppcart'])
                # Add a product to shopping cart even if the product is already in the shopping cart
                if product_id in session['Shoppcart']:
                    # for key , item in session['Shoppcart'].items():
                    #     if int(key) == int(product_id):
                    #         session.modified = True
                    #         item['quantity'] += 1
                    #         print(item["quantity"])
                    print('This product is already in cart')
                else:
                    session['Shoppcart'] = MagerDicts(session['Shoppcart'], DictItems)
                    return redirect(request.referrer)
            else:
                session['Shoppcart'] = DictItems
                return redirect(request.referrer)
    except Exception as e:
        print(e)
    finally:
        return redirect(request.referrer)

# Display products on cart
@app.route("/cart")
def get_carts():
    # Display tha brands and categories on the navbar dropdown
    brands = Brand.query.join(Product, (Brand.id == Product.brand_id)).all()
    categories = Category.query.join(Product, (Category.id == Product.category_id)).all()
    if "Shoppcart" not in session or len(session['Shoppcart']) <= 0:
        return redirect(url_for('home'))
    subtotal = 0
    grandtotal = 0
    for key , product in session['Shoppcart'].items():
        discount = (product['discount']/100) * float(product['price']) * int(product['quantity'])
        subtotal += float(product['price']) * int(product['quantity'])
        subtotal -= discount
        tax = ("%.2f" % (0.06 * float(subtotal)))
        grandtotal = float("%.2f" % (1.06 * subtotal))
    return render_template("carts.html", brands=brands, categories=categories, tax=tax, grandtotal=grandtotal, datetime=datetime)


@app.route("/update_cart/<int:code>", methods=["GET", "POST"])
def update_cart(code):
    if 'Shoppcart' not in session or len(session['Shoppcart']) <= 0:
        return redirect(url_for('home'))
    if request.method == "POST":
        quantity = request.form.get('quantity')
        color = request.form.get('color')
        try:
            session.modified = True
            for key , item in session['Shoppcart'].items():
                if int(key) == code:
                    item['quantity'] = quantity
                    item['color'] = color
                    flash("Item updated")
                    return redirect(url_for('get_carts'))
        except Exception as e:
            print(e)
            return redirect(url_for('get_carts'))


@app.route("/delete_item/<int:id>")
def delete_item(id):
    if 'Shoppcart' not in session or len(session['Shoppcart']) <= 0:
        return redirect(url_for('home'))
    try:
        session.modified = True
        for key , item in session['Shoppcart'].items():
            if int(key) == id:
                session['Shoppcart'].pop(key, None)
                return redirect(url_for('get_carts'))
    except Exception as e:
        print(e)
        return redirect(url_for('get_carts'))


@app.route("/clear_cart", methods=["GET"])
def clear_cart():
    try:
        session.pop("Shoppcart", None)
        return redirect(url_for('home'))
    except Exception as e:
        print(e)



# Display products by brand
@app.route("/brand/<int:id>")
def get_brand(id):
    page = request.args.get("page", 1, type=int)
    get_brand= Brand.query.filter_by(id=id).first_or_404()
    brand = Product.query.filter_by(brand=get_brand).paginate(page=page, per_page=8)
    # brand = db.session.execute(db.select(Product).where(Product.brand_id==id)).scalars().all().paginate(page=page, per_page=2)
    # Display tha brands and categories on the navbar dropdown
    brands = Brand.query.join(Product, (Brand.id == Product.brand_id)).all()
    categories = Category.query.join(Product, (Category.id == Product.category_id)).all()
    return render_template("index.html", brand=brand, get_brand=get_brand, brands=brands,
                           categories=categories, datetime=datetime)

# Display products by category
@app.route("/category/<int:id>")
def get_category(id):
    page = request.args.get("page", 1, type=int)
    get_cat = Category.query.filter_by(id=id).first_or_404()
    category = Product.query.filter_by(category=get_cat).paginate(page=page, per_page=8)
    # category = db.session.execute(db.select(Product).where(Product.category_id==id)).scalars().all()
    # Display tha brands and categories on the navbar dropdown
    brands = Brand.query.join(Product, (Brand.id == Product.brand_id)).all()
    categories = Category.query.join(Product, (Category.id == Product.category_id)).all()
    return render_template("index.html", category=category, get_cat=get_cat, brands=brands,
                           categories=categories, datetime=datetime)


@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    form = AddProduct()
    if form.validate_on_submit():
        with app.app_context():
            requested_brand = request.form.get("brand")
            requested_category = request.form.get("category")
            for brand in brands:
                if brand.name == requested_brand:
                    brand_id = brand.id

                    # print(brand_id)
                    # print(requested_brand)

            for category in categories:
                if category.name == requested_category:
                    category_id = category.id

            new_product = Product(
                                  product_name=request.form.get("product_name"),
                                  price=request.form.get("price"),
                                  discount=request.form.get("discount"),
                                  stock=request.form.get("stock"),
                                  description=request.form.get("description"),
                                  colors=request.form.get("colors"),
                                  brand_id=brand_id,
                                  category_id=category_id,
                                  image_1=photos.save(request.files.get("image_1"), secrets.token_hex(10) + "."),
                                  image_2=photos.save(request.files.get("image_2"), secrets.token_hex(10) + "."),
                                  image_3=photos.save(request.files.get("image_3"), secrets.token_hex(10) + "."),

                            )

        db.session.add(new_product)
        db.session.commit()

        flash("Product added!")
        return redirect(url_for('home'))
    return render_template("add_product.html", form=form, brands=brands, categories=categories, datetime=datetime)


@app.route("/add_brand", methods=["GET", "POST"])
def add_brand():
    form = AddBrand()
    if form.validate_on_submit():
        brand = request.form.get("brand")
        result = db.session.execute(db.select(Brand).where(Brand.name == brand))
        brand = result.scalar()
        if brand:
            # Brand already exists
            flash("This brand already exist, add a category instead!")
            return redirect(url_for('add_category'))
        with app.app_context():
            new_brand = Brand(name=request.form.get("brand"))

            db.session.add(new_brand)
            db.session.commit()
            flash("Brand added!")
            return redirect(url_for('add_brand'))
    return render_template("add_brand.html", form=form, datetime=datetime)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    form = AddCategory()
    if form.validate_on_submit():
        category = request.form.get("category")
        result = db.session.execute(db.select(Category).where(Category.name == category))
        category = result.scalar()
        if category:
            # Category already exists
            flash("This category already exist, add a product instead!")
            return redirect(url_for('add_product'))
        with app.app_context():
            new_category = Category(name=request.form.get("category"))

            db.session.add(new_category)
            db.session.commit()
            return redirect(url_for('add_category'))
    return render_template("add_category.html", form=form, datetime=datetime)








if __name__ == "__main__":
    app.run(debug=True)