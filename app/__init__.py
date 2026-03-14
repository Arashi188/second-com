from flask import Flask 
from flask_sqlalchemy import SQLAlchemy 
from flask_login import LoginManager 
from flask_migrate import Migrate 
from config import Config 
import os 
 
db = SQLAlchemy() 
login_manager = LoginManager() 
migrate = Migrate() 
 
def create_app(config_class=Config): 
    app = Flask(__name__) 
    app.config.from_object(config_class) 
 
    # Ensure instance folder exists 
    try: 
        os.makedirs(app.instance_path) 
    except OSError: 
        pass 
 
    # Ensure upload folder exists 
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) 
 
    # Initialize extensions 
    db.init_app(app) 
    login_manager.init_app(app) 
    migrate.init_app(app, db) 
 
    # Login manager configuration 
    login_manager.login_view = 'auth.login' 
    login_manager.login_message = 'Please log in to access this page.' 
    login_manager.login_message_category = 'info' 
 
    # Register blueprints 
    from app.routes import bp as routes_bp 
    app.register_blueprint(routes_bp) 
 
    from app.auth import bp as auth_bp 
    app.register_blueprint(auth_bp, url_prefix='/auth') 
 
    from app.admin import bp as admin_bp 
    app.register_blueprint(admin_bp, url_prefix='/admin') 
 
    return app 
