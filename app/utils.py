"""
Utility functions module
"""
import os
import secrets
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
import cloudinary.api

def save_image(file):
    """
    Save uploaded image with optimization
    
    Args:
        file: FileStorage object
        
    Returns:
        str: URL or filename of saved image
    """
    # Configure Cloudinary if credentials exist
    if current_app.config.get('dapuaw0u6'):
        cloudinary.config(
            cloud_name=current_app.config['dapuaw0u6'],
            api_key=current_app.config['738952696443951'],
            api_secret=current_app.config['CzRSL1UUAnGoOI1xnrc1NwlMIiU']
        )
    
    # Check if we're in production (Vercel) or using Cloudinary
    if os.environ.get('VERCEL_ENV') or current_app.config.get('dapuaw0u6'):
        # Production: Upload to Cloudinary
        try:
            # Open and optimize image
            image = Image.open(file)
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Save temporarily
            temp_filename = f"temp_{secrets.token_hex(8)}.jpg"
            temp_path = os.path.join('/tmp', temp_filename)
            image.save(temp_path, optimize=True, quality=85)
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                temp_path,
                folder="ecommerce_products",
                transformation=[
                    {'width': 1200, 'height': 1200, 'crop': 'limit'},
                    {'quality': 'auto'}
                ]
            )
            
            # Clean up temp file
            os.remove(temp_path)
            
            return result['public_id']
        except Exception as e:
            print(f"Cloudinary upload error: {e}")
            return "default_product.jpg"
    else:
        # Development: Save locally
        filename = secure_filename(file.filename)
        random_hex = secrets.token_hex(8)
        filename = f"{random_hex}_{filename}"
        
        # Ensure upload folder exists
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Optimize image
        image = Image.open(file)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        max_size = (1200, 1200)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        image.save(filepath, optimize=True, quality=85)
        
        return filename

def get_image_url(image_path):
    """
    Get image URL (local or cloudinary)
    """
    if not image_path or image_path == 'default-product.jpg':
        return '/static/images/default-product.jpg'
    
    # Check if we're in production or using Cloudinary
    if os.environ.get('VERCEL_ENV') or current_app.config.get('dapuaw0u6'):
        try:
            # Configure Cloudinary
            cloudinary.config(
                cloud_name=current_app.config['dapuaw0u6'],
                api_key=current_app.config['738952696443951'],
                api_secret=current_app.config['CzRSL1UUAnGoOI1xnrc1NwlMIiU']
            )
            # Return Cloudinary URL
            return cloudinary.CloudinaryImage(image_path).build_url(
                width=600,
                height=600,
                crop='fill',
                quality='auto'
            )
        except:
            # Fallback to local URL
            return f"/static/uploads/{image_path}"
    else:
        # Development: Return local URL
        return f"/static/uploads/{image_path}"

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def format_whatsapp_url(phone_number, message):
    """
    Format WhatsApp URL with message
    
    Args:
        phone_number: WhatsApp phone number
        message: Message to send
        
    Returns:
        str: WhatsApp URL
    """
    from urllib.parse import quote
    # Remove any non-digit characters from phone number
    phone = ''.join(filter(str.isdigit, phone_number))
    encoded_message = quote(message)
    return f"https://wa.me/{phone}?text={encoded_message}"