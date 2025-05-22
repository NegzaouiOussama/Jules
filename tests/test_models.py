from tests.base import BaseTestCase
from app import db, bcrypt
from app.models import User, Listing, Reservation
from datetime import datetime, timedelta

class ModelTestCase(BaseTestCase):

    def test_user_creation_and_password_hashing(self):
        user = User(username='testuser', email='test@example.com', password_hash='initial_hash', role='passenger')
        # Test direct password hashing (though typically done before User object creation)
        hashed_password = bcrypt.generate_password_hash('testpassword').decode('utf-8')
        user.password_hash = hashed_password
        db.session.add(user)
        db.session.commit()

        retrieved_user = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.email, 'test@example.com')
        self.assertEqual(retrieved_user.role, 'passenger')
        self.assertTrue(bcrypt.check_password_hash(retrieved_user.password_hash, 'testpassword'))
        self.assertFalse(bcrypt.check_password_hash(retrieved_user.password_hash, 'wrongpassword'))

    def test_user_default_role_or_assigned_role(self):
        # Assuming 'passenger' is a common default or needs to be explicitly set
        user_driver = User(username='driver', email='driver@example.com', password_hash=bcrypt.generate_password_hash('pass').decode('utf-8'), role='driver')
        db.session.add(user_driver)
        db.session.commit()
        self.assertEqual(User.query.filter_by(username='driver').first().role, 'driver')

    def test_listing_creation_and_relationships(self):
        driver = User(username='driver_listing', email='driver_listing@example.com', password_hash=bcrypt.generate_password_hash('driverpass').decode('utf-8'), role='driver')
        db.session.add(driver)
        db.session.commit()

        departure = datetime.utcnow() + timedelta(days=1)
        listing = Listing(
            driver_id=driver.id,
            origin='City A',
            destination='City B',
            departure_time=departure,
            available_seats=3,
            price=25.50
        )
        db.session.add(listing)
        db.session.commit()

        retrieved_listing = Listing.query.filter_by(origin='City A').first()
        self.assertIsNotNone(retrieved_listing)
        self.assertEqual(retrieved_listing.driver_id, driver.id)
        self.assertEqual(retrieved_listing.destination, 'City B')
        self.assertEqual(retrieved_listing.available_seats, 3)
        self.assertEqual(retrieved_listing.price, 25.50)
        self.assertEqual(retrieved_listing.driver.username, 'driver_listing') # Test relationship

    def test_listing_data_integrity(self):
        # Attempting to create a listing with invalid data should ideally be caught by model validators if they exist,
        # or by database constraints. For this test, we'll focus on successful creation.
        # More advanced tests could involve trying to set negative seats, etc., if using SQLAlchemy validators.
        driver = User.query.filter_by(username='driver_listing').first()
        if not driver: # Ensure driver exists from previous test or create
             driver = User(username='driver_listing_integrity', email='driver_listing_int@example.com', password_hash=bcrypt.generate_password_hash('pass').decode('utf-8'), role='driver')
             db.session.add(driver)
             db.session.commit()

        departure = datetime.utcnow() + timedelta(hours=5)
        listing = Listing(driver_id=driver.id, origin='Test Origin', destination='Test Dest', departure_time=departure, available_seats=1, price=10.00)
        db.session.add(listing)
        db.session.commit()
        self.assertIsNotNone(Listing.query.filter_by(origin='Test Origin').first())


    def test_reservation_creation_and_relationships(self):
        passenger = User(username='passenger_res', email='passenger_res@example.com', password_hash=bcrypt.generate_password_hash('pass').decode('utf-8'), role='passenger')
        driver = User(username='driver_res', email='driver_res@example.com', password_hash=bcrypt.generate_password_hash('pass').decode('utf-8'), role='driver')
        db.session.add_all([passenger, driver])
        db.session.commit()

        listing = Listing(driver_id=driver.id, origin='Origin Res', destination='Dest Res', departure_time=datetime.utcnow() + timedelta(days=2), available_seats=2, price=30.00)
        db.session.add(listing)
        db.session.commit()

        reservation = Reservation(
            passenger_id=passenger.id,
            listing_id=listing.id,
            seats_reserved=1
        )
        db.session.add(reservation)
        db.session.commit()

        retrieved_reservation = Reservation.query.filter_by(passenger_id=passenger.id).first()
        self.assertIsNotNone(retrieved_reservation)
        self.assertEqual(retrieved_reservation.listing_id, listing.id)
        self.assertEqual(retrieved_reservation.seats_reserved, 1)
        self.assertEqual(retrieved_reservation.passenger.username, 'passenger_res') # Test passenger relationship
        self.assertEqual(retrieved_reservation.listing.origin, 'Origin Res') # Test listing relationship

    def test_reservation_data_integrity(self):
        # Similar to listing, focusing on successful creation.
        # Advanced tests could check constraints like seats_reserved > 0 if model/db enforces.
        passenger = User.query.filter_by(username='passenger_res').first()
        listing = Listing.query.filter_by(origin='Origin Res').first()

        if not passenger or not listing: # Ensure they exist
            self.skipTest("Dependent user or listing not found for reservation integrity test.")

        reservation = Reservation(passenger_id=passenger.id, listing_id=listing.id, seats_reserved=2)
        # Check if this reservation would exceed available_seats (though this logic is usually in routes)
        # For model test, just ensure it can be created.
        db.session.add(reservation)
        db.session.commit()
        self.assertGreater(Reservation.query.filter_by(passenger_id=passenger.id).count(), 0)


if __name__ == '__main__':
    unittest.main()
