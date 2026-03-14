from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, TextAreaField, FloatField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Email, Length, ValidationError, NumberRange, EqualTo
from app.models import User

# ========== AUTHENTICATION FORMS ==========

class LoginForm(FlaskForm):
    """Admin login form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')


# ========== PRODUCT FORMS ==========

class ProductForm(FlaskForm):
    """Form for adding/editing products"""
    name = StringField('Product Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0, message="Price must be greater than 0")])
    stock = IntegerField('Stock Quantity', validators=[DataRequired(), NumberRange(min=0, message="Stock must be 0 or greater")])
    image = FileField('Product Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only! (jpg, jpeg, png, gif)')
    ])


# ========== USER PROFILE FORMS ==========

class ProfileForm(FlaskForm):
    """Form for editing user profile"""
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Length(max=20)])
    
    def validate_username(self, username):
        """Validate that username is unique"""
        from flask_login import current_user
        user = User.query.filter_by(username=username.data).first()
        if user and user.id != current_user.id:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        """Validate that email is unique"""
        from flask_login import current_user
        user = User.query.filter_by(email=email.data).first()
        if user and user.id != current_user.id:
            raise ValidationError('Email already registered. Please use a different one.')


class ChangePasswordForm(FlaskForm):
    """Form for changing password"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(), 
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(), 
        EqualTo('new_password', message="Passwords must match")
    ])


# ========== ADDRESS FORMS ==========

class AddressForm(FlaskForm):
    """Form for adding/editing addresses"""
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    address_line1 = StringField('Address Line 1', validators=[DataRequired(), Length(max=200)])
    address_line2 = StringField('Address Line 2 (Optional)', validators=[Length(max=200)])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    state = StringField('State', validators=[DataRequired(), Length(max=100)])
    postal_code = StringField('Postal Code', validators=[Length(max=20)])
    country = StringField('Country', validators=[DataRequired(), Length(max=100)], default='Nigeria')
    label = StringField('Address Label (e.g., Home, Office)', validators=[DataRequired(), Length(max=50)], default='Home')
    is_default = BooleanField('Set as default address')


# ========== SEARCH FORM ==========

class SearchForm(FlaskForm):
    """Form for searching products"""
    query = StringField('Search', validators=[DataRequired()])


# ========== REVIEW FORM ==========

class ReviewForm(FlaskForm):
    """Form for product reviews"""
    rating = IntegerField('Rating', validators=[
        DataRequired(), 
        NumberRange(min=1, max=5, message="Rating must be between 1 and 5")
    ])
    comment = TextAreaField('Comment', validators=[Length(max=500)])


# ========== CONTACT FORM ==========

class ContactForm(FlaskForm):
    """Form for contact page"""
    name = StringField('Your Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Your Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=2000)])


# ========== NEWSLETTER FORM ==========

class NewsletterForm(FlaskForm):
    """Form for newsletter subscription"""
    email = StringField('Email', validators=[DataRequired(), Email()])


# ========== CHECKOUT FORM ==========

class CheckoutForm(FlaskForm):
    """Form for checkout information"""
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    address = StringField('Delivery Address', validators=[DataRequired(), Length(max=500)])
    notes = TextAreaField('Order Notes (Optional)', validators=[Length(max=1000)])


# ========== ADMIN FORMS ==========

class AdminUserEditForm(FlaskForm):
    """Form for admin to edit users"""
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = StringField('Role', validators=[DataRequired()])
    is_active = BooleanField('Active')


class CategoryForm(FlaskForm):
    """Form for product categories"""
    name = StringField('Category Name', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[Length(max=200)])
    icon = StringField('Icon Class', validators=[Length(max=50)], 
                      description='Font Awesome icon class (e.g., "fa-laptop")')


# ========== VALIDATION HELPERS ==========

def validate_image(form, field):
    """Custom validator for image files"""
    if field.data:
        filename = field.data.filename
        if not filename or not ('.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif'}):
            raise ValidationError('Invalid image format. Allowed: jpg, jpeg, png, gif')


def validate_phone_number(form, field):
    """Custom validator for phone numbers"""
    if field.data:
        # Remove common phone number characters
        phone = ''.join(filter(str.isdigit, field.data))
        if len(phone) < 10 or len(phone) > 15:
            raise ValidationError('Please enter a valid phone number (10-15 digits)')


# ========== FORM CONFIGURATION ==========

# You can add CSRF protection settings here if needed
# class BaseForm(FlaskForm):
#     class Meta:
#         csrf = True
#         csrf_time_limit = 3600  # 1 hour