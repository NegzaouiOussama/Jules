from flask import Blueprint, render_template, redirect, url_for, flash, abort
from app import db
from flask_login import login_required, current_user
from app.models import User, Listing, Reservation
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Decorator for admin-only access
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You must be an admin to access this page.', 'danger')
            return redirect(url_for('main.index')) # Or auth.login if preferred
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    return render_template('admin/admin_dashboard.html', title='Admin Dashboard')

@admin_bp.route('/users')
@login_required
@admin_required
def view_users():
    users = User.query.all()
    return render_template('admin/admin_view_users.html', title='View Users', users=users)

@admin_bp.route('/listings')
@login_required
@admin_required
def view_listings():
    listings = Listing.query.join(User).all() # Ensure User model is joined for driver info
    return render_template('admin/admin_view_listings.html', title='View Listings', listings=listings)

@admin_bp.route('/reservations')
@login_required
@admin_required
def view_reservations():
    reservations = Reservation.query.join(User, Reservation.passenger_id == User.id)\
                                    .join(Listing, Reservation.listing_id == Listing.id)\
                                    .all()
    # The default relationship backrefs 'passenger' and 'listing' should work.
    # If specific columns are needed, add_columns might be used, but usually not necessary
    # if relationships are well-defined in models.
    return render_template('admin/admin_view_reservations.html', title='View Reservations', reservations=reservations)
