from flask import Blueprint, render_template, session, request, redirect, url_for, flash, jsonify, current_app
from app.models import Product, Order
from app import db
import json
from urllib.parse import quote

bp = Blueprint('main', __name__)

# Cart session key
CART_SESSION_KEY = 'shopping_cart'

@bp.route('/')
def index():
    """Homepage with featured products"""
    # Get featured products (latest 6 products)
    featured_products = Product.query.order_by(Product.created_at.desc()).limit(6).all()
    return render_template('index.html', featured_products=featured_products)

@bp.route('/products')
def products():
    """Product catalog page with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    products = Product.query.filter(Product.stock > 0).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('products.html', products=products)

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@bp.route('/cart')
def cart():
    """Shopping cart page"""
    cart_items = session.get(CART_SESSION_KEY, {})
    products = []
    total = 0
    
    for product_id, item_data in cart_items.items():
        product = Product.query.get(int(product_id))
        if product:
            quantity = item_data.get('quantity', 1)
            subtotal = product.price * quantity
            products.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
            total += subtotal
    
    return render_template('cart.html', products=products, total=total)

@bp.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart"""
    product = Product.query.get_or_404(product_id)
    
    if not product.is_in_stock():
        flash('This product is out of stock!', 'danger')
        return redirect(url_for('main.product_detail', product_id=product_id))
    
    quantity = int(request.form.get('quantity', 1))
    
    # Get current cart from session
    cart = session.get(CART_SESSION_KEY, {})
    
    # Add or update item
    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += quantity
    else:
        cart[str(product_id)] = {
            'quantity': quantity,
            'added_at': str(db.func.current_timestamp())
        }
    
    # Save cart to session
    session[CART_SESSION_KEY] = cart
    session.modified = True
    
    flash(f'{product.name} added to cart!', 'success')
    return redirect(url_for('main.cart'))

@bp.route('/update-cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    """Update cart item quantity"""
    cart = session.get(CART_SESSION_KEY, {})
    quantity = int(request.form.get('quantity', 1))
    
    if quantity > 0:
        if str(product_id) in cart:
            cart[str(product_id)]['quantity'] = quantity
    else:
        # Remove item if quantity is 0
        cart.pop(str(product_id), None)
    
    session[CART_SESSION_KEY] = cart
    session.modified = True
    
    flash('Cart updated successfully!', 'success')
    return redirect(url_for('main.cart'))

@bp.route('/remove-from-cart/<int:product_id>')
def remove_from_cart(product_id):
    """Remove item from cart"""
    cart = session.get(CART_SESSION_KEY, {})
    cart.pop(str(product_id), None)
    
    session[CART_SESSION_KEY] = cart
    session.modified = True
    
    flash('Item removed from cart!', 'success')
    return redirect(url_for('main.cart'))

@bp.route('/checkout-whatsapp')
def checkout_whatsapp():
    """Generate WhatsApp message with cart items and redirect"""
    cart_items = session.get(CART_SESSION_KEY, {})
    
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('main.products'))
    
    products_list = []
    total = 0
    message_lines = ["*NEW ORDER*", ""]
    
    for product_id, item_data in cart_items.items():
        product = Product.query.get(int(product_id))
        if product:
            quantity = item_data.get('quantity', 1)
            subtotal = product.price * quantity
            total += subtotal
            
            products_list.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': quantity,
                'subtotal': subtotal
            })
            
            message_lines.append(f"*{product.name}*")
            message_lines.append(f"ID: #{product.id}")
            message_lines.append(f"Price: ₦{product.price:,.2f}")
            message_lines.append(f"Quantity: {quantity}")
            message_lines.append(f"Subtotal: ₦{subtotal:,.2f}")
            message_lines.append("")
    
    message_lines.append("*ORDER SUMMARY*")
    message_lines.append(f"Total Items: {len(products_list)}")
    message_lines.append(f"Total Amount: ₦{total:,.2f}")
    message_lines.append("")
    message_lines.append("Please confirm my order. Thank you!")
    
    # Create order record
    order = Order(
        order_details=json.dumps(products_list, default=str),
        total_amount=total
    )
    db.session.add(order)
    db.session.commit()
    
    # Encode message for URL
    message = "\n".join(message_lines)
    encoded_message = quote(message)
    
    # Clear cart after checkout
    session.pop(CART_SESSION_KEY, None)
    
    # Redirect to WhatsApp
    whatsapp_url = f"https://wa.me/{current_app.config['WHATSAPP_NUMBER']}?text={encoded_message}"
    return redirect(whatsapp_url)

# ========== MISSING ROUTES - ADD THESE ==========

@bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@bp.route('/faq')
def faq():
    """FAQ page"""
    return render_template('faq.html')

@bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@bp.route('/search')
def search():
    """Search products"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    if query:
        products = Product.query.filter(
            (Product.name.ilike(f'%{query}%')) | 
            (Product.description.ilike(f'%{query}%'))
        ).filter(Product.stock > 0).paginate(page=page, per_page=per_page, error_out=False)
    else:
        products = Product.query.filter(Product.stock > 0).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('search_results.html', products=products, query=query)

@bp.route('/category/<int:category_id>')
def category_products(category_id):
    """Products by category"""
    from app.models import Category
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    products = Product.query.filter_by(category_id=category_id).filter(Product.stock > 0).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('category_products.html', category=category, products=products)

# ========== USER PROFILE ROUTES ==========

@bp.route('/profile')
def profile():
    """User profile page"""
    if not current_user.is_authenticated:
        flash('Please login to view your profile', 'warning')
        return redirect(url_for('auth.login'))
    return render_template('profile.html')

@bp.route('/orders')
def orders():
    """User orders page"""
    if not current_user.is_authenticated:
        flash('Please login to view your orders', 'warning')
        return redirect(url_for('auth.login'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page)
    return render_template('orders.html', orders=orders)

@bp.route('/order/<int:order_id>')
def order_detail(order_id):
    """Order detail page"""
    if not current_user.is_authenticated:
        flash('Please login to view this order', 'warning')
        return redirect(url_for('auth.login'))
    
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to view this order', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('order_detail.html', order=order)

@bp.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    """Edit user profile"""
    if not current_user.is_authenticated:
        flash('Please login to edit your profile', 'warning')
        return redirect(url_for('auth.login'))
    
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        # Add phone if you have that field
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.profile'))
    
    # Pre-populate form
    form.username.data = current_user.username
    form.email.data = current_user.email
    
    return render_template('edit_profile.html', form=form)

@bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """Change user password"""
    if not current_user.is_authenticated:
        flash('Please login to change your password', 'warning')
        return redirect(url_for('auth.login'))
    
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('main.profile'))
        else:
            flash('Current password is incorrect', 'danger')
    
    return render_template('change_password.html', form=form)

# ========== WISHLIST ROUTES ==========

@bp.route('/wishlist')
def wishlist():
    """User wishlist page"""
    if not current_user.is_authenticated:
        flash('Please login to view your wishlist', 'warning')
        return redirect(url_for('auth.login'))
    
    from app.models import Wishlist
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    products = [item.product for item in wishlist_items if item.product]
    return render_template('wishlist.html', products=products)

@bp.route('/wishlist/toggle/<int:product_id>', methods=['POST'])
def toggle_wishlist(product_id):
    """Toggle product in wishlist"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    from app.models import Wishlist
    product = Product.query.get_or_404(product_id)
    
    wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        return jsonify({'success': True, 'action': 'removed'})
    else:
        wishlist_item = Wishlist(user_id=current_user.id, product_id=product_id)
        db.session.add(wishlist_item)
        db.session.commit()
        return jsonify({'success': True, 'action': 'added'})

# ========== ADDRESS ROUTES ==========

@bp.route('/address/add', methods=['GET', 'POST'])
def add_address():
    """Add new address"""
    if not current_user.is_authenticated:
        flash('Please login to add an address', 'warning')
        return redirect(url_for('auth.login'))
    
    form = AddressForm()
    if form.validate_on_submit():
        from app.models import Address
        address = Address(
            user_id=current_user.id,
            full_name=form.full_name.data,
            phone=form.phone.data,
            address_line1=form.address_line1.data,
            address_line2=form.address_line2.data,
            city=form.city.data,
            state=form.state.data,
            postal_code=form.postal_code.data,
            country=form.country.data,
            label=form.label.data,
            is_default=form.is_default.data
        )
        
        # If this is default, unset other defaults
        if form.is_default.data:
            Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
        
        db.session.add(address)
        db.session.commit()
        flash('Address added successfully!', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('address_form.html', form=form, title='Add Address')

# ========== NEWSLETTER ==========

@bp.route('/newsletter-signup', methods=['POST'])
def newsletter_signup():
    """Newsletter signup"""
    email = request.form.get('email')
    if email:
        # Save to database or mailing list service
        flash('Thank you for subscribing to our newsletter!', 'success')
    else:
        flash('Please provide a valid email', 'danger')
    return redirect(url_for('main.index'))

# ========== API ENDPOINTS ==========

@bp.route('/api/search-suggestions')
def search_suggestions():
    """API endpoint for live search suggestions"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify({'suggestions': []})
    
    products = Product.query.filter(
        (Product.name.ilike(f'%{query}%')) |
        (Product.description.ilike(f'%{query}%'))
    ).limit(5).all()
    
    suggestions = [{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'image': url_for('static', filename='uploads/' + p.image) if p.image else None
    } for p in products]
    
    return jsonify({'suggestions': suggestions})

# ========== ERROR HANDLERS ==========

@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500