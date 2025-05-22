import unittest
from app import app, db, bcrypt # Import global app, db, bcrypt
from app.models import User # Import User model for helper

class BaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up for all tests in this class."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing forms
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        # It's important that db.create_all() is called after the URI is set to in-memory
        
        # The original db.create_all() in app/__init__.py might have already created 'site.db'.
        # For tests, we want a fresh in-memory database.
        with app.app_context():
            # If there was an existing db connection, we might need to re-initialize or drop first.
            # For :memory:, each connection is separate, but let's be explicit.
            db.drop_all() # Ensure any existing tables (e.g. from site.db) are gone from this session
            db.create_all() # Create tables in the in-memory database

    @classmethod
    def tearDownClass(cls):
        """Tear down after all tests in this class."""
        with app.app_context():
            db.drop_all()

    def setUp(self):
        """Set up for each test method."""
        self.app = app
        self.client = self.app.test_client()
        self.app_context = self.app.app_context() # Get app context
        self.app_context.push() # Push app context for each test

        # db.session.begin_nested() # Optional: if you want to rollback transactions per test

    def tearDown(self):
        """Tear down for each test method."""
        # db.session.rollback() # Optional: if using nested transactions
        db.session.remove() # Clean up the session
        self.app_context.pop() # Pop app context

    # Helper method to create a user
    def _create_user(self, username, email, password, role):
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password_hash=hashed_password, role=role)
        db.session.add(user)
        db.session.commit()
        return user

# This check is important if you want to run this file directly,
# but usually tests are run by a test runner.
if __name__ == '__main__':
    unittest.main()
