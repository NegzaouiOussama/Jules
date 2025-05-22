import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt # Import Bcrypt

# Create instances of Flask, SQLAlchemy, and LoginManager
app = Flask(__name__)
bcrypt = Bcrypt(app) # Initialize Bcrypt
db = SQLAlchemy()
login_manager = LoginManager()

# Configure the Flask app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')  # It's good practice to use environment variables for secret keys
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize db and login_manager with the app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # Specify the login view for @login_required decorator
login_manager.login_message_category = 'info' # Optional: customize the flash message category

# Import models here to ensure they are registered with SQLAlchemy before db.create_all() is called
from app.models import User, Listing, Reservation # Adjusted to import all defined models

# (Optional) Register blueprints for routes later
from app.routes.auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

from app.routes.driver import driver_bp # Import driver blueprint
app.register_blueprint(driver_bp) # Register driver blueprint

from app.routes.passenger import passenger_bp # Import passenger blueprint
app.register_blueprint(passenger_bp) # Register passenger blueprint

from .routes.main import main_bp # Import main blueprint
app.register_blueprint(main_bp) # Register main blueprint

from .routes.admin import admin_bp # Import admin blueprint
app.register_blueprint(admin_bp) # Register admin blueprint

# It's important to import routes after the app object is created to avoid circular imports
# from app import routes # General routes, if you have any in app/routes.py or similar

# Create database tables if they don't exist
# This is a common pattern but consider using Flask-Migrate for more robust database schema management
with app.app_context():
    db.create_all() # This line can be problematic if models are not imported correctly or if run at the wrong time.
                    # For more complex applications, Flask-Migrate is recommended.

# Basic route example (optional, can be removed if you use blueprints or define routes elsewhere)
# @app.route('/') # This is now handled by main_bp
# def home():
#     return "Welcome to the Carpooling App!"

# The following is necessary to make SQLAlchemy work correctly with Flask patterns.
# Import models after db has been initialized and configured with the app.
# This also helps avoid circular dependencies if your models need to import 'db' or 'app'.
# Example:
# from .models import User, Ride # Adjust based on your actual model names and structure

# Ensure you have a user_loader callback for Flask-Login
# Example:
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) # Assuming you have a User model with an 'id' primary key

# For now, the user_loader and model imports are commented out as models are not yet defined.
# These will be essential once you start adding user authentication and database models.
