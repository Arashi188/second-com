import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Product, User, Order, Category
from app.forms import ProductForm, CategoryForm
from functools import wraps
from PIL import Image
import secrets
from datetime import datetime

bp = Blueprint('admin', __name__)

# ========== ADMIN DECORATORS ==========

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin():
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


# ========== IMAGE HANDLING FUNCTIONS ==========

def save_product_image(form_image):
    """Save uploaded product image with secure filename and optimization"""
    if not form_image or not form_image.filename:
        return None
    
    # Generate random filename to prevent collisions
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)
    filename = random_hex + f_ext.lower()
    
    # Ensure extension is allowed
    if f_ext.lower() not in ['.png', '.jpg', '.jpeg', '.gif']:
        return None
    
    # Create upload directory if it doesn't exist
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    
    filepath = os.path.join(upload_folder, filename)
    
    # Resize and optimize image
    try:
        i = Image.open(form_image)
        
        # Convert RGBA to RGB if necessary
        if i.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', i.size, (255, 255, 255))
            background.paste(i, mask=i.split()[-1])
            i = background
        
        # Resize to max dimensions
        max_size = (800, 800)
        i.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save optimized image
        i.save(filepath, optimize=True, quality=85)
        
        return filename
    except Exception as e:
        print(f"Error saving image: {e}")
        return None


def delete_product_image(filename):
    """Delete product image file"""
    if not filename or filename == 'default-product.jpg':
        return
    
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"Error deleting image: {e}")


# ========== DASHBOARD ==========

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    # Get counts
    product_count = Product.query.count()
    order_count = Order.query.count()
    user_count = User.query.count()
    category_count = Category.query.count() if hasattr(Category, 'query') else 0
    
    # Low stock products (less than 10)
    low_stock_products = Product.query.filter(Product.stock < 10).count()
    
    # Recent products
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Order statistics
    pending_orders = Order.query.filter_by(status='pending').count()
    completed_orders = Order.query.filter_by(status='completed').count()
    cancelled_orders = Order.query.filter_by(status='cancelled').count()
    
    return render_template('admin_dashboard.html',
                         product_count=product_count,
                         order_count=order_count,
                         user_count=user_count,
                         category_count=category_count,
                         low_stock_products=low_stock_products,
                         recent_products=recent_products,
                         recent_orders=recent_orders,
                         pending_orders=pending_orders,
                         completed_orders=completed_orders,
                         cancelled_orders=cancelled_orders)


# ========== PRODUCT MANAGEMENT ==========

@bp.route('/products')
@login_required
@admin_required
def products():
    """Manage products - list all products"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get filter parameters
    search = request.args.get('search', '')
    stock_filter = request.args.get('stock', '')
    
    # Base query
    query = Product.query
    
    # Apply search filter
    if search:
        query = query.filter(
            (Product.name.ilike(f'%{search}%')) | 
            (Product.description.ilike(f'%{search}%'))
        )
    
    # Apply stock filter
    if stock_filter == 'low':
        query = query.filter(Product.stock < 10)
    elif stock_filter == 'out':
        query = query.filter(Product.stock == 0)
    elif stock_filter == 'in':
        query = query.filter(Product.stock > 0)
    
    # Order by
    query = query.order_by(Product.created_at.desc())
    
    products = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin_products.html', 
                         products=products,
                         search=search,
                         stock_filter=stock_filter)


@bp.route('/product/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_product():
    """Add new product"""
    form = ProductForm()
    
    # Get categories for dropdown if needed
    categories = Category.query.all() if hasattr(Category, 'query') else []
    
    if form.validate_on_submit():
        # Handle image upload
        image_file = None
        if form.image.data:
            image_file = save_product_image(form.image.data)
            if not image_file:
                flash('Error uploading image. Please try again.', 'danger')
                return render_template('admin_product_form.html', form=form, title='Add Product', categories=categories)
        
        # Create product
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock=form.stock.data,
            image=image_file or 'default-product.jpg'
        )
        
        # Add category if selected
        # if form.category.data:
        #     product.category_id = form.category.data
        
        db.session.add(product)
        db.session.commit()
        
        flash(f'Product "{product.name}" has been added successfully!', 'success')
        return redirect(url_for('admin.products'))
    
    return render_template('admin_product_form.html', 
                         form=form, 
                         title='Add Product',
                         categories=categories,
                         product=None)


@bp.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    """Edit existing product"""
    product = Product.query.get_or_404(product_id)
    form = ProductForm()
    
    # Get categories for dropdown
    categories = Category.query.all() if hasattr(Category, 'query') else []
    
    if form.validate_on_submit():
        # Update product fields
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.stock = form.stock.data
        
        # Handle image upload
        if form.image.data:
            # Delete old image if not default
            delete_product_image(product.image)
            
            # Save new image
            image_file = save_product_image(form.image.data)
            if image_file:
                product.image = image_file
            else:
                flash('Error uploading new image. Keeping old image.', 'warning')
        
        # Update category if selected
        # if form.category.data:
        #     product.category_id = form.category.data
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash(f'Product "{product.name}" has been updated successfully!', 'success')
        return redirect(url_for('admin.products'))
    
    # Pre-populate form with existing data
    elif request.method == 'GET':
        form.name.data = product.name
        form.description.data = product.description
        form.price.data = product.price
        form.stock.data = product.stock
        # form.category.data = product.category_id
    
    return render_template('admin_product_form.html', 
                         form=form, 
                         title='Edit Product',
                         categories=categories,
                         product=product)


@bp.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    """Delete product"""
    product = Product.query.get_or_404(product_id)
    product_name = product.name
    
    # Delete image file if not default
    delete_product_image(product.image)
    
    db.session.delete(product)
    db.session.commit()
    
    flash(f'Product "{product_name}" has been deleted!', 'success')
    return redirect(url_for('admin.products'))


@bp.route('/product/bulk-delete', methods=['POST'])
@login_required
@admin_required
def bulk_delete_products():
    """Delete multiple products at once"""
    product_ids = request.form.getlist('product_ids')
    
    if not product_ids:
        flash('No products selected.', 'warning')
        return redirect(url_for('admin.products'))
    
    count = 0
    for product_id in product_ids:
        product = Product.query.get(int(product_id))
        if product:
            delete_product_image(product.image)
            db.session.delete(product)
            count += 1
    
    db.session.commit()
    flash(f'{count} product(s) deleted successfully!', 'success')
    return redirect(url_for('admin.products'))


# ========== ORDER MANAGEMENT ==========

@bp.route('/orders')
@login_required
@admin_required
def orders():
    """View all orders"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    status = request.args.get('status', '')
    
    # Base query
    query = Order.query
    
    # Apply status filter
    if status:
        query = query.filter_by(status=status)
    
    # Order by
    query = query.order_by(Order.created_at.desc())
    
    orders = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Get counts for filter badges
    total_orders = Order.query.count()
    pending_count = Order.query.filter_by(status='pending').count()
    completed_count = Order.query.filter_by(status='completed').count()
    cancelled_count = Order.query.filter_by(status='cancelled').count()
    
    return render_template('admin_orders.html', 
                         orders=orders,
                         status=status,
                         total_orders=total_orders,
                         pending_count=pending_count,
                         completed_count=completed_count,
                         cancelled_count=cancelled_count)


@bp.route('/order/<int:order_id>')
@login_required
@admin_required
def order_detail(order_id):
    """View order details"""
    order = Order.query.get_or_404(order_id)
    return render_template('admin_order_detail.html', order=order)


@bp.route('/order/<int:order_id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    """Update order status"""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'completed', 'cancelled']:
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order.id} status updated to {new_status}!', 'success')
    else:
        flash('Invalid status.', 'danger')
    
    return redirect(url_for('admin.order_detail', order_id=order.id))


@bp.route('/order/<int:order_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_order(order_id):
    """Delete order"""
    order = Order.query.get_or_404(order_id)
    order_id_num = order.id
    
    db.session.delete(order)
    db.session.commit()
    
    flash(f'Order #{order_id_num} has been deleted!', 'success')
    return redirect(url_for('admin.orders'))


# ========== USER MANAGEMENT ==========

@bp.route('/users')
@login_required
@admin_required
def users():
    """Manage users"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin_users.html', users=users)


@bp.route('/user/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """Toggle user admin status"""
    if user_id == current_user.id:
        flash('You cannot change your own admin status.', 'danger')
        return redirect(url_for('admin.users'))
    
    user = User.query.get_or_404(user_id)
    user.role = 'admin' if user.role != 'admin' else 'customer'
    db.session.commit()
    
    flash(f'User {user.username} role updated to {user.role}.', 'success')
    return redirect(url_for('admin.users'))


@bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user"""
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    user = User.query.get_or_404(user_id)
    username = user.username
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} has been deleted!', 'success')
    return redirect(url_for('admin.users'))


# ========== CATEGORY MANAGEMENT ==========

@bp.route('/categories')
@login_required
@admin_required
def categories():
    """Manage categories"""
    if not hasattr(Category, 'query'):
        flash('Categories feature not enabled.', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin_categories.html', categories=categories)


@bp.route('/category/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_category():
    """Add new category"""
    if not hasattr(Category, 'query'):
        flash('Categories feature not enabled.', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    form = CategoryForm()
    
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data,
            icon=form.icon.data
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash(f'Category "{category.name}" created!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin_category_form.html', form=form, title='Add Category')


@bp.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    """Edit category"""
    if not hasattr(Category, 'query'):
        flash('Categories feature not enabled.', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    category = Category.query.get_or_404(category_id)
    form = CategoryForm()
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        category.icon = form.icon.data
        db.session.commit()
        
        flash(f'Category "{category.name}" updated!', 'success')
        return redirect(url_for('admin.categories'))
    
    # Pre-populate form
    form.name.data = category.name
    form.description.data = category.description
    form.icon.data = category.icon
    
    return render_template('admin_category_form.html', form=form, title='Edit Category', category=category)


@bp.route('/category/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    """Delete category"""
    if not hasattr(Category, 'query'):
        flash('Categories feature not enabled.', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    category = Category.query.get_or_404(category_id)
    category_name = category.name
    
    db.session.delete(category)
    db.session.commit()
    
    flash(f'Category "{category_name}" deleted!', 'success')
    return redirect(url_for('admin.categories'))


# ========== REPORTS ==========

@bp.route('/reports')
@login_required
@admin_required
def reports():
    """Sales and inventory reports"""
    # Get date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Default to last 30 days
    if not end_date:
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
    if not start_date:
        from datetime import timedelta
        start = datetime.utcnow() - timedelta(days=30)
        start_date = start.strftime('%Y-%m-%d')
    
    # Convert to datetime objects
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Get orders in date range
    orders = Order.query.filter(
        Order.created_at >= start_dt,
        Order.created_at <= end_dt
    ).all()
    
    # Calculate totals
    total_sales = sum(order.total_amount for order in orders)
    total_orders = len(orders)
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0
    
    # Get top products
    product_sales = {}
    for order in orders:
        try:
            items = json.loads(order.order_details) if isinstance(order.order_details, str) else order.order_details
            for item in items:
                product_id = item.get('id')
                if product_id:
                    if product_id not in product_sales:
                        product_sales[product_id] = {
                            'name': item.get('name'),
                            'quantity': 0,
                            'revenue': 0
                        }
                    product_sales[product_id]['quantity'] += item.get('quantity', 0)
                    product_sales[product_id]['revenue'] += item.get('subtotal', 0)
        except:
            pass
    
    top_products = sorted(product_sales.values(), key=lambda x: x['revenue'], reverse=True)[:10]
    
    return render_template('admin_reports.html',
                         start_date=start_date,
                         end_date=end_date,
                         total_sales=total_sales,
                         total_orders=total_orders,
                         avg_order_value=avg_order_value,
                         top_products=top_products)


# ========== SETTINGS ==========

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Admin settings"""
    if request.method == 'POST':
        # Update settings
        whatsapp_number = request.form.get('whatsapp_number')
        if whatsapp_number:
            # Save to database or config
            flash('Settings updated successfully!', 'success')
        else:
            flash('Error updating settings.', 'danger')
        
        return redirect(url_for('admin.settings'))
    
    return render_template('admin_settings.html')


# ========== API ENDPOINTS ==========

@bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API endpoint for dashboard statistics"""
    # Get today's date
    today = datetime.utcnow().date()
    
    # Today's orders
    today_orders = Order.query.filter(
        db.func.date(Order.created_at) == today
    ).count()
    
    # Today's sales
    today_sales = db.session.query(db.func.sum(Order.total_amount)).filter(
        db.func.date(Order.created_at) == today
    ).scalar() or 0
    
    return jsonify({
        'today_orders': today_orders,
        'today_sales': today_sales,
        'total_products': Product.query.count(),
        'total_orders': Order.query.count(),
        'total_users': User.query.count(),
        'low_stock': Product.query.filter(Product.stock < 10).count()
    })


@bp.route('/api/products/low-stock')
@login_required
@admin_required
def api_low_stock():
    """API endpoint for low stock products"""
    products = Product.query.filter(Product.stock < 10).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'stock': p.stock,
        'price': p.price
    } for p in products])