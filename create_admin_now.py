from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Delete any existing admin
    User.query.filter_by(username='admin').delete()
    
    # Create new admin
    admin = User(
        username='admin',
        email='admin@example.com',
        role='admin'
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    
    # Verify
    check = User.query.filter_by(username='admin').first()
    if check:
        print("=" * 50)
        print("✓ ADMIN CREATED SUCCESSFULLY!")
        print("=" * 50)
        print("Login URL: http://127.0.0.1:5000/auth/login")
        print("Username: admin")
        print("Password: admin123")
        print("=" * 50)
    else:
        print("✗ Failed to create admin")