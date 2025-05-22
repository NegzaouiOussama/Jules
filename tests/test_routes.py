from tests.base import BaseTestCase
from app.models import User, Listing, Reservation
from app import db, bcrypt
from flask import url_for, get_flashed_messages
from flask_login import current_user, login_user, logout_user
from datetime import datetime, timedelta

class RoutesTestCase(BaseTestCase):

    def setUp(self):
        super().setUp() # Call BaseTestCase.setUp()
        # Create users with different roles for testing
        self.driver_user = self._create_user('testdriver', 'driver@example.com', 'driverpass', 'driver')
        self.passenger_user = self._create_user('testpassenger', 'passenger@example.com', 'passengerpass', 'passenger')
        self.admin_user = self._create_user('testadmin', 'admin@example.com', 'adminpass', 'admin')

    # Helper to log in a user
    def _login(self, email, password):
        return self.client.post(url_for('auth.login'), data={'email': email, 'password': password}, follow_redirects=True)

    # Helper to log out
    def _logout(self):
        return self.client.get(url_for('auth.logout'), follow_redirects=True)

    # === Test Access Control ===
    def test_unauthenticated_access_redirects(self):
        protected_routes = [
            url_for('driver.create_listing'),
            url_for('driver.my_listings'),
            # url_for('driver.edit_listing', listing_id=1), # Needs a listing_id
            # url_for('driver.delete_listing', listing_id=1), # Needs a listing_id
            url_for('passenger.my_reservations'),
            # url_for('passenger.reserve_listing', listing_id=1), # Needs a listing_id, POST
            url_for('admin.dashboard'),
            url_for('admin.view_users'),
            url_for('admin.view_listings'),
            url_for('admin.view_reservations'),
        ]
        for route in protected_routes:
            response = self.client.get(route, follow_redirects=False) # Don't follow, check redirect location
            self.assertEqual(response.status_code, 302, f"Route {route} did not redirect.")
            self.assertTrue(url_for('auth.login') in response.location, f"Route {route} did not redirect to login.")
    
    def test_role_based_access_driver_routes(self):
        # Passenger trying to access driver routes
        self._login('passenger@example.com', 'passengerpass')
        response = self.client.get(url_for('driver.create_listing'), follow_redirects=True)
        self.assertNotIn(b'Create New Listing', response.data) # Should be redirected
        self.assertIn(b'You must be a driver to access this page.', response.data) # Check flash message
        self._logout()

        # Admin trying to access driver routes (assuming admin is not also a driver)
        self._login('admin@example.com', 'adminpass')
        response = self.client.get(url_for('driver.create_listing'), follow_redirects=True)
        self.assertNotIn(b'Create New Listing', response.data)
        self.assertIn(b'You must be a driver to access this page.', response.data)
        self._logout()

    def test_role_based_access_passenger_routes(self):
        # Driver trying to access passenger routes
        self._login('driver@example.com', 'driverpass')
        response = self.client.get(url_for('passenger.my_reservations'), follow_redirects=True)
        self.assertNotIn(b'My Reservations', response.data)
        self.assertIn(b'You must be a passenger to access this page.', response.data)
        self._logout()

    def test_role_based_access_admin_routes(self):
        # Driver trying to access admin routes
        self._login('driver@example.com', 'driverpass')
        response = self.client.get(url_for('admin.dashboard'), follow_redirects=True)
        self.assertNotIn(b'Admin Dashboard', response.data)
        self.assertIn(b'You must be an admin to access this page.', response.data)
        self._logout()

        # Passenger trying to access admin routes
        self._login('passenger@example.com', 'passengerpass')
        response = self.client.get(url_for('admin.dashboard'), follow_redirects=True)
        self.assertNotIn(b'Admin Dashboard', response.data)
        self.assertIn(b'You must be an admin to access this page.', response.data)
        self._logout()

    # === Test Driver Routes ===
    def test_driver_create_listing_page_loads(self):
        self._login('driver@example.com', 'driverpass')
        response = self.client.get(url_for('driver.create_listing'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create New Listing', response.data)
        self._logout()

    def test_driver_create_listing_success(self):
        self._login('driver@example.com', 'driverpass')
        departure_time_str = (datetime.utcnow() + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
        response = self.client.post(url_for('driver.create_listing'), data={
            'origin': 'Driver Origin',
            'destination': 'Driver Destination',
            'departure_time': departure_time_str,
            'available_seats': 3,
            'price': 22.50
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'My Listings', response.data) # Should redirect to my_listings
        self.assertIn(b'Your listing has been created!', response.data)
        listing = Listing.query.filter_by(origin='Driver Origin').first()
        self.assertIsNotNone(listing)
        self.assertEqual(listing.driver_id, self.driver_user.id)
        self._logout()

    def test_driver_view_my_listings(self):
        self._login('driver@example.com', 'driverpass')
        # Create a listing for this driver first
        Listing(driver_id=self.driver_user.id, origin='MyListOrigin', destination='MyListDest', departure_time=datetime.utcnow()+timedelta(days=1), available_seats=2, price=10).save()
        db.session.commit()

        response = self.client.get(url_for('driver.my_listings'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'My Listings', response.data)
        self.assertIn(b'MyListOrigin', response.data) # Check if listing is present
        self._logout()
        
    def test_driver_edit_own_listing(self):
        self._login('driver@example.com', 'driverpass')
        departure_time = datetime.utcnow() + timedelta(days=2)
        listing = Listing(driver_id=self.driver_user.id, origin='Editable', destination='OriginalDest', departure_time=departure_time, available_seats=4, price=50)
        db.session.add(listing)
        db.session.commit()

        response = self.client.get(url_for('driver.edit_listing', listing_id=listing.id))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Edit Listing', response.data)
        self.assertIn(b'Editable', response.data)

        updated_departure_time_str = (datetime.utcnow() + timedelta(days=4)).strftime('%Y-%m-%d %H:%M:%S')
        response = self.client.post(url_for('driver.edit_listing', listing_id=listing.id), data={
            'origin': 'Editable Updated',
            'destination': 'NewDest',
            'departure_time': updated_departure_time_str,
            'available_seats': 2,
            'price': 55.00
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Your listing has been updated!', response.data)
        updated_listing = Listing.query.get(listing.id)
        self.assertEqual(updated_listing.origin, 'Editable Updated')
        self.assertEqual(updated_listing.available_seats, 2)
        self._logout()

    def test_driver_delete_own_listing(self):
        self._login('driver@example.com', 'driverpass')
        listing_to_delete = Listing(driver_id=self.driver_user.id, origin='Deletable', destination='Dest', departure_time=datetime.utcnow()+timedelta(days=1), available_seats=1, price=5)
        db.session.add(listing_to_delete)
        db.session.commit()
        listing_id = listing_to_delete.id

        response = self.client.post(url_for('driver.delete_listing', listing_id=listing_id), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Your listing has been deleted!', response.data)
        self.assertIsNone(Listing.query.get(listing_id))
        self._logout()

    def test_driver_cannot_edit_or_delete_others_listing(self):
        other_driver = self._create_user('otherdriver', 'other@example.com', 'otherpass', 'driver')
        other_listing = Listing(driver_id=other_driver.id, origin='Others', destination='Listing', departure_time=datetime.utcnow()+timedelta(days=1), available_seats=3, price=20)
        db.session.add(other_listing)
        db.session.commit()

        self._login('driver@example.com', 'driverpass') # Log in as our main test driver
        
        # Attempt to edit
        response_edit = self.client.get(url_for('driver.edit_listing', listing_id=other_listing.id), follow_redirects=False)
        self.assertEqual(response_edit.status_code, 403) # Forbidden

        # Attempt to delete
        response_delete = self.client.post(url_for('driver.delete_listing', listing_id=other_listing.id), follow_redirects=False)
        self.assertEqual(response_delete.status_code, 403) # Forbidden
        self.assertIsNotNone(Listing.query.get(other_listing.id)) # Ensure it wasn't deleted
        self._logout()

    # === Test Passenger Routes ===
    def test_passenger_browse_listings(self):
        # Create some listings
        Listing(driver_id=self.driver_user.id, origin='Browse1', destination='Dest1', departure_time=datetime.utcnow()+timedelta(days=1), available_seats=2, price=10).save()
        Listing(driver_id=self.driver_user.id, origin='Browse2', destination='Dest2', departure_time=datetime.utcnow()+timedelta(days=2), available_seats=0, price=15).save() # No seats
        db.session.commit()
        
        response = self.client.get(url_for('passenger.browse_listings'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Available Listings', response.data)
        self.assertIn(b'Browse1', response.data)
        self.assertNotIn(b'Browse2', response.data) # Should not show listings with 0 available seats

    def test_passenger_view_listing_detail(self):
        listing = Listing(driver_id=self.driver_user.id, origin='DetailOrigin', destination='DetailDest', departure_time=datetime.utcnow()+timedelta(days=1), available_seats=3, price=25)
        db.session.add(listing)
        db.session.commit()

        response = self.client.get(url_for('passenger.view_listing', listing_id=listing.id))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Listing Details', response.data)
        self.assertIn(b'DetailOrigin', response.data)
        self.assertIn(b'Reserve Seats', response.data) # Assuming logged out or passenger

    def test_passenger_make_reservation_success(self):
        self._login('passenger@example.com', 'passengerpass')
        listing = Listing(driver_id=self.driver_user.id, origin='ReserveOrigin', destination='ReserveDest', departure_time=datetime.utcnow()+timedelta(days=1), available_seats=3, price=30)
        db.session.add(listing)
        db.session.commit()

        response = self.client.post(url_for('passenger.reserve_listing', listing_id=listing.id), data={
            'seats_reserved': 2
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'My Reservations', response.data) # Redirects to my_reservations
        self.assertIn(b'Successfully reserved 2 seat(s)', response.data)
        
        updated_listing = Listing.query.get(listing.id)
        self.assertEqual(updated_listing.available_seats, 1)
        reservation = Reservation.query.filter_by(listing_id=listing.id, passenger_id=self.passenger_user.id).first()
        self.assertIsNotNone(reservation)
        self.assertEqual(reservation.seats_reserved, 2)
        self._logout()

    def test_passenger_reservation_not_enough_seats(self):
        self._login('passenger@example.com', 'passengerpass')
        listing = Listing(driver_id=self.driver_user.id, origin='FewSeatsOrigin', destination='FewSeatsDest', departure_time=datetime.utcnow()+timedelta(days=1), available_seats=1, price=10)
        db.session.add(listing)
        db.session.commit()

        response = self.client.post(url_for('passenger.reserve_listing', listing_id=listing.id), data={
            'seats_reserved': 2
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on detail page or similar
        self.assertIn(b'Not enough available seats', response.data)
        self.assertEqual(Listing.query.get(listing.id).available_seats, 1) # Seats unchanged
        self._logout()

    def test_driver_cannot_reserve_own_listing(self):
        # Log in as the driver who owns the listing
        self._login('driver@example.com', 'driverpass')
        listing = Listing(driver_id=self.driver_user.id, origin='SelfReserveOrigin', destination='SelfReserveDest', departure_time=datetime.utcnow()+timedelta(days=1), available_seats=2, price=10)
        db.session.add(listing)
        db.session.commit()
        
        # Need to temporarily change user role to passenger to pass the @passenger_required decorator,
        # or the route logic itself should prevent this. The current passenger.reserve_listing checks driver_id == current_user.id.
        # For this test, we assume the @passenger_required decorator is the first hurdle.
        # So, a driver trying to POST to this route would be blocked by @passenger_required.
        # Let's adjust the test to reflect that.

        # A driver (current_user.role == 'driver') trying to POST to reserve_listing.
        # The @passenger_required decorator in passenger.py should kick in.
        response = self.client.post(url_for('passenger.reserve_listing', listing_id=listing.id), data={
            'seats_reserved': 1
        }, follow_redirects=True)
        self.assertIn(b'You must be a passenger to access this page.', response.data)
        self._logout()

    def test_passenger_view_my_reservations(self):
        self._login('passenger@example.com', 'passengerpass')
        listing = Listing(driver_id=self.driver_user.id, origin='MyResListing', destination='MyResListingDest', departure_time=datetime.utcnow()+timedelta(days=1), available_seats=2, price=10)
        db.session.add(listing)
        db.session.commit()
        Reservation(passenger_id=self.passenger_user.id, listing_id=listing.id, seats_reserved=1).save()
        db.session.commit()

        response = self.client.get(url_for('passenger.my_reservations'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'My Reservations', response.data)
        self.assertIn(b'MyResListing', response.data)
        self._logout()

    # === Test Admin Routes ===
    def test_admin_dashboard_access(self):
        self._login('admin@example.com', 'adminpass')
        response = self.client.get(url_for('admin.dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Admin Dashboard', response.data)
        self.assertIn(b'View All Users', response.data)
        self._logout()

    def test_admin_view_users(self):
        self._login('admin@example.com', 'adminpass')
        response = self.client.get(url_for('admin.view_users'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'All Users', response.data)
        self.assertIn(b'testdriver', response.data) # From setUp
        self.assertIn(b'testpassenger', response.data) # From setUp
        self.assertIn(b'testadmin', response.data) # From setUp
        self._logout()

    def test_admin_view_listings(self):
        self._login('admin@example.com', 'adminpass')
        Listing(driver_id=self.driver_user.id, origin='AdminViewListing', destination='AdminViewDest', departure_time=datetime.utcnow()+timedelta(days=1), available_seats=2, price=10).save()
        db.session.commit()

        response = self.client.get(url_for('admin.view_listings'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'All Listings', response.data)
        self.assertIn(b'AdminViewListing', response.data)
        self.assertIn(b'testdriver', response.data) # Driver's username
        self._logout()

    def test_admin_view_reservations(self):
        self._login('admin@example.com', 'adminpass')
        listing = Listing(driver_id=self.driver_user.id, origin='AdminResListing', destination='AdminResDest', departure_time=datetime.utcnow()+timedelta(days=1), available_seats=2, price=10)
        db.session.add(listing)
        db.session.commit()
        Reservation(passenger_id=self.passenger_user.id, listing_id=listing.id, seats_reserved=1).save()
        db.session.commit()

        response = self.client.get(url_for('admin.view_reservations'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'All Reservations', response.data)
        self.assertIn(b'AdminResListing', response.data) # Listing info
        self.assertIn(b'testpassenger', response.data) # Passenger's username
        self._logout()


if __name__ == '__main__':
    unittest.main()
