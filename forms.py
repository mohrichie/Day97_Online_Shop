from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField, SelectField, BooleanField, IntegerField, TextAreaField
from wtforms import FileField
from flask_wtf.file import FileRequired, FileAllowed
from wtforms.validators import DataRequired, EqualTo, URL, Email
from flask_ckeditor import CKEditorField
from flask_ckeditor.utils import cleanify


# Create a Registration Form
class RegistrationForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), EqualTo('confirm', message='Both passwords must match')])
    confirm = PasswordField("Repeat Password", validators=[DataRequired()])
    country = StringField("Country", validators=[DataRequired()])
    state = StringField("State/Region", validators=[DataRequired()])
    city = StringField("City", validators=[DataRequired()])
    contact = StringField("Contact", validators=[DataRequired()])
    address = StringField("Address", validators=[DataRequired()])
    zipcode = StringField("Zip Code", validators=[DataRequired()])
    profile = FileField("Profile", validators=[FileRequired(), FileAllowed(["jpg", "png", "gif", 'jpeg'],
                                                                           "Image only please")])
    submit = SubmitField("Register")


# Create a Login Form
class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    login = SubmitField("Login")


# Create the add product brand Form
class AddBrand(FlaskForm):
    brand = StringField("Brand Name", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Create the add product Category Form
class AddCategory(FlaskForm):
    category = StringField("Category", validators=[DataRequired()])
    submit = SubmitField("Submit")



# class AddProduct(FlaskForm):
#     brand = SelectField('Select a Brand', choices=['Apple', 'Samsung',  'Google Pixel'])
#     category = SelectField('Select a Category', choices=['Cell Phones', 'Smart Watches',  'Laptops'])
#     product_name = StringField("Product Name", validators=[DataRequired()])
#     price = IntegerField("Price", validators=[DataRequired()])
#     discount = IntegerField("Discount", default=0)
#     stock = IntegerField("Stock", validators=[DataRequired()])
#     description = TextAreaField("Description", validators=[DataRequired()])
#     colors = TextAreaField("Colors", validators=[DataRequired()])
#     image_1 = FileField("Image 1", validators=[FileRequired(), FileAllowed(["jpg", "png", "gif", 'jpeg'])])
#     image_2 = FileField("Image 2", validators=[FileRequired(), FileAllowed(["jpg", "png", "gif", 'jpeg'])])
#     image_3 = FileField("Image 3", validators=[FileRequired(), FileAllowed(["jpg", "png", "gif", 'jpeg'])])
#     submit = SubmitField("Submit")


