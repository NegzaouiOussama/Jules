from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from app import db
from flask_login import login_required, current_user
from app.models import Listing
from app.forms import ListingForm
from datetime import datetime
from functools import wraps

driver_bp = Blueprint('driver', __name__)

# Decorator for driver-only access
def driver_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'driver':
            flash('You must be a driver to access this page.', 'danger')
            return redirect(url_for('auth.login')) # Or a suitable 'unauthorized' page
        return f(*args, **kwargs)
    return decorated_function

@driver_bp.route('/listings/new', methods=['GET', 'POST'])
@login_required
@driver_required
def create_listing():
    form = ListingForm()
    if form.validate_on_submit():
        listing = Listing(
            driver_id=current_user.id,
            origin=form.origin.data,
            destination=form.destination.data,
            departure_time=form.departure_time.data,
            available_seats=form.available_seats.data,
            price=form.price.data
        )
        db.session.add(listing)
        db.session.commit()
        flash('Your listing has been created!', 'success')
        return redirect(url_for('driver.my_listings'))
    return render_template('create_listing.html', title='Create Listing', form=form)

@driver_bp.route('/my-listings')
@login_required
@driver_required
def my_listings():
    listings = Listing.query.filter_by(driver_id=current_user.id).order_by(Listing.departure_time.desc()).all()
    return render_template('my_listings.html', title='My Listings', listings=listings)

@driver_bp.route('/listings/<int:listing_id>/edit', methods=['GET', 'POST'])
@login_required
@driver_required
def edit_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if listing.driver_id != current_user.id:
        abort(403)  # Forbidden
    
    form = ListingForm(obj=listing) # Populate form with existing data on GET
    if form.validate_on_submit():
        listing.origin = form.origin.data
        listing.destination = form.destination.data
        listing.departure_time = form.departure_time.data
        listing.available_seats = form.available_seats.data
        listing.price = form.price.data
        db.session.commit()
        flash('Your listing has been updated!', 'success')
        return redirect(url_for('driver.my_listings'))
    
    return render_template('create_listing.html', title='Edit Listing', form=form, listing=listing) # Pass listing for context

@driver_bp.route('/listings/<int:listing_id>/delete', methods=['POST'])
@login_required
@driver_required
def delete_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if listing.driver_id != current_user.id:
        abort(403)
    db.session.delete(listing)
    db.session.commit()
    flash('Your listing has been deleted!', 'success')
    return redirect(url_for('driver.my_listings'))
