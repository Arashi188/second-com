import os
import sys

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User

print("Starting database initialization...")

# Create app
app = create_app()

with app.app_context():
    # Print database path
    db_path = app.config['SQLALCHEMY_DATABASE_URI']
    print(f"Database URI: {db_path}")
    
    # Extract file path from URI
    file_path = db_path.replace('sqlite:///', '')
    print(f"Database file will be: {file_path}")
    
    # Check if directory is writable
    db_dir = os.path.dirname(file_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"Created directory: {db_dir}")
    
    # Delete existing database if it exists
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Removed existing database: {file_path}")
        except Exception as e:
            print(f"Could not remove existing database: {e}")
    
    # Create all tables
    try:
        db.create_all()
        print("✓ Database tables created successfully!")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        raise
    
    # Create admin user
    try:
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✓ Admin user created successfully!")
        else:
            print("Admin user already exists")
    except Exception as e:
        print(f"✗ Error creating admin: {e}")
        raise
    
    # Verify
    if os.path.exists(file_path):
        print(f"✓ Database file created at: {file_path}")
        print(f"File size: {os.path.getsize(file_path)} bytes")
    else:
        print(f"✗ Database file NOT found at: {file_path}")

print("Initialization complete!")