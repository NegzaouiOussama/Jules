from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from app import db
from flask_login import login_required, current_user
from app.models import Listing, Reservation, User
from app.forms import ReservationForm
from functools import wraps

passenger_bp = Blueprint('passenger', __name__)

# Decorator for passenger-only access
def passenger_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'passenger':
            flash('You must be a passenger to access this page.', 'danger')
            return redirect(url_for('auth.login')) # Or a suitable 'unauthorized' page
        return f(*args, **kwargs)
    return decorated_function

@passenger_bp.route('/listings')
def browse_listings():
    listings = Listing.query.join(User).filter(Listing.available_seats > 0).order_by(Listing.departure_time.asc()).all()
    return render_template('browse_listings.html', title='Browse Listings', listings=listings)

@passenger_bp.route('/listings/<int:listing_id>')
def view_listing(listing_id): # Renamed from view_listing_detail to avoid conflict if any
    listing = Listing.query.get_or_404(listing_id)
    form = ReservationForm()
    return render_template('view_listing_detail.html', title='Listing Details', listing=listing, form=form)

@passenger_bp.route('/listings/<int:listing_id>/reserve', methods=['POST'])
@login_required
@passenger_required
def reserve_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    form = ReservationForm()

    if form.validate_on_submit():
        seats_to_reserve = form.seats_reserved.data
        if listing.available_seats >= seats_to_reserve:
            # Prevent driver from reserving their own listing
            if listing.driver_id == current_user.id:
                flash('You cannot reserve seats in your own listing.', 'warning')
                return redirect(url_for('passenger.view_listing', listing_id=listing.id))

            # Prevent passenger from reserving multiple times for the same listing (optional, can be complex)
            existing_reservation = Reservation.query.filter_by(passenger_id=current_user.id, listing_id=listing.id).first()
            if existing_reservation:
                flash('You have already reserved seats for this listing. Please manage your existing reservation.', 'info')
                return redirect(url_for('passenger.my_reservations'))


            reservation = Reservation(
                passenger_id=current_user.id,
                listing_id=listing.id,
                seats_reserved=seats_to_reserve
            )
            listing.available_seats -= seats_to_reserve
            db.session.add(reservation)
            db.session.commit()
            flash(f'Successfully reserved {seats_to_reserve} seat(s) for the trip from {listing.origin} to {listing.destination}!', 'success')
            return redirect(url_for('passenger.my_reservations'))
        else:
            flash('Not enough available seats for your request.', 'danger')
            # It's better to re-render the page with the form and errors if any, but redirect is simpler for now
            return redirect(url_for('passenger.view_listing', listing_id=listing.id))
    else:
        # If form validation fails, it's better to re-render the detail page with the form and its errors
        # For simplicity in this step, redirecting back. A more robust solution would pass form errors.
        flash('Invalid input for reservation. Please check your details.', 'danger')
        return redirect(url_for('passenger.view_listing', listing_id=listing.id))


@passenger_bp.route('/my-reservations')
@login_required
@passenger_required
def my_reservations():
    reservations = Reservation.query.filter_by(passenger_id=current_user.id)\
                                    .join(Listing, Reservation.listing_id == Listing.id)\
                                    .add_columns(Listing.origin, Listing.destination, Listing.departure_time, User.username.label("driver_username"), Reservation.seats_reserved, Listing.id.label("listing_id"))\
                                    .join(User, Listing.driver_id == User.id)\
                                    .order_by(Listing.departure_time.asc())\
                                    .all()
    # The query above returns tuples. We can convert them to dicts or objects for easier template access if needed,
    # or access by index/attribute name if the template is structured accordingly.
    # For now, the template is expected to handle these as `reservation.origin`, `reservation.driver_username` etc.
    return render_template('my_reservations.html', title='My Reservations', reservations=reservations)
