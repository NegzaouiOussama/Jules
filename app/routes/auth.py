from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db, app # Importing app to initialize bcrypt
from flask_bcrypt import Bcrypt # Import Bcrypt
from flask_login import login_user, logout_user, current_user
from app.models import User
from app.forms import RegistrationForm, LoginForm

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt(app) # Initialize Bcrypt with the app instance

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home')) # Assuming 'home' is the main page route name
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password, role=form.role.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', title='Register', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home')) # Assuming 'home' is the main page route name
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if current_user.role == 'driver':
                return redirect(url_for('driver.my_listings'))
            elif current_user.role == 'passenger':
                return redirect(url_for('passenger.browse_listings'))
            else: # Admin or other roles
                return redirect(url_for('main.index')) # Default redirect
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index')) # Redirect to home/index page on logout
