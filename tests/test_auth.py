from tests.base import BaseTestCase
from app.models import User
from app import db, bcrypt
from flask import get_flashed_messages, url_for
from flask_login import current_user

class AuthTestCase(BaseTestCase):

    def test_registration_page_loads(self):
        response = self.client.get(url_for('auth.register'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Register', response.data)

    def test_successful_registration(self):
        response = self.client.post(url_for('auth.register'), data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword',
            'confirm_password': 'newpassword',
            'role': 'passenger'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Should redirect to login
        self.assertIn(b'Login', response.data) # Check if login page content is present
        
        # Check for flash message
        # Need to access flashed messages within the test client's session context
        # This requires the route to actually call flash()
        # For simplicity, we'll check if the user is in the database
        user = User.query.filter_by(email='newuser@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.role, 'passenger')

    def test_registration_with_existing_username(self):
        self._create_user('existinguser', 'existing@example.com', 'password', 'driver')
        response = self.client.post(url_for('auth.register'), data={
            'username': 'existinguser',
            'email': 'another@example.com',
            'password': 'newpassword',
            'confirm_password': 'newpassword',
            'role': 'passenger'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on registration page
        self.assertIn(b'That username is taken', response.data)

    def test_registration_with_existing_email(self):
        self._create_user('anotheruser', 'existingemail@example.com', 'password', 'passenger')
        response = self.client.post(url_for('auth.register'), data={
            'username': 'newusername',
            'email': 'existingemail@example.com',
            'password': 'newpassword',
            'confirm_password': 'newpassword',
            'role': 'driver'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on registration page
        self.assertIn(b'That email is taken', response.data)

    def test_login_page_loads(self):
        response = self.client.get(url_for('auth.login'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_successful_login_and_logout(self):
        self._create_user('loginuser', 'login@example.com', 'loginpass', 'passenger')
        
        # Test Login
        response = self.client.post(url_for('auth.login'), data={
            'email': 'login@example.com',
            'password': 'loginpass'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        # Assuming redirect to passenger.browse_listings for passenger
        self.assertIn(b'Available Listings', response.data) 
        
        # After login, current_user should be active and authenticated
        # Need to test current_user within a request context for it to be populated by Flask-Login
        with self.client: # Use the test client as a context manager for subsequent requests
            self.client.get(url_for('main.index')) # Make a request to populate current_user
            self.assertTrue(current_user.is_authenticated)
            self.assertEqual(current_user.username, 'loginuser')

            # Test Logout
            logout_response = self.client.get(url_for('auth.logout'), follow_redirects=True)
            self.assertEqual(logout_response.status_code, 200)
            self.assertIn(b'Welcome to the Carpooling App!', logout_response.data) # Back to home page

            self.client.get(url_for('main.index')) # Make another request
            self.assertFalse(current_user.is_authenticated)


    def test_login_with_incorrect_password(self):
        self._create_user('loginuser2', 'login2@example.com', 'correctpass', 'driver')
        response = self.client.post(url_for('auth.login'), data={
            'email': 'login2@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'Login Unsuccessful', response.data)
        
        with self.client:
            self.client.get(url_for('main.index'))
            self.assertFalse(current_user.is_authenticated)

    def test_login_with_nonexistent_email(self):
        response = self.client.post(url_for('auth.login'), data={
            'email': 'nonexistent@example.com',
            'password': 'anypassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'Login Unsuccessful', response.data)
        
        with self.client:
            self.client.get(url_for('main.index'))
            self.assertFalse(current_user.is_authenticated)

    def test_redirect_if_already_logged_in(self):
        user = self._create_user('loggedin', 'loggedin@example.com', 'pass', 'passenger')
        # Manually log in user for this test or use the login route
        with self.client:
            self.client.post(url_for('auth.login'), data={'email': 'loggedin@example.com', 'password': 'pass'}, follow_redirects=True)
            
            # Try to access login page again
            response = self.client.get(url_for('auth.login'), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Available Listings', response.data) # Should be redirected away from login

            # Try to access register page again
            response = self.client.get(url_for('auth.register'), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Available Listings', response.data) # Should be redirected away from register


if __name__ == '__main__':
    unittest.main()
