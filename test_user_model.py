"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Set up a clean database for each test."""
        db.drop_all()  # Drop all tables
        db.create_all()  # Create new tables

        # Create two sample users
        self.sample_user1 = User.signup("testuser1", "test1@email.com", "password1", None)
        self.sample_user2 = User.signup("testuser2", "test2@email.com", "password2", None)
        
        # Commit these changes to the database
        db.session.commit()

        # Assign user IDs for easier access
        self.user1_id = self.sample_user1.id
        self.user2_id = self.sample_user2.id

        # Initialize the test client
        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res


    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_following_relationships(self):
        """Test following and followers relationships between users."""
        self.sample_user1.following.append(self.sample_user2)
        db.session.commit()

        self.assertIn(self.sample_user2, self.sample_user1.following)

        self.assertIn(self.sample_user1, self.sample_user2.followers)

        self.assertEqual(len(self.sample_user1.following), 1)
        self.assertEqual(len(self.sample_user2.followers), 1)

    def test_following_status(self):
        """Test if is_following method works correctly."""
        self.sample_user1.following.append(self.sample_user2)
        db.session.commit()

        self.assertTrue(self.sample_user1.is_following(self.sample_user2))
        self.assertFalse(self.sample_user2.is_following(self.sample_user1))

    def test_followed_status(self):
        """Test if is_followed_by method works correctly."""
        self.sample_user1.following.append(self.sample_user2)
        db.session.commit()

        self.assertTrue(self.sample_user2.is_followed_by(self.sample_user1))
        self.assertFalse(self.sample_user1.is_followed_by(self.sample_user2))

    def test_unfollow_user(self):
        """Test the ability of one user to unfollow another."""
        self.sample_user1.following.append(self.sample_user2)
        db.session.commit()

        self.sample_user1.following.remove(self.sample_user2)
        db.session.commit()

        self.assertNotIn(self.sample_user2, self.sample_user1.following)
        self.assertNotIn(self.sample_user1, self.sample_user2.followers)

    def test_successful_registration(self):
        new_user = User.signup("uniqueusername", "uniqueemail@mail.com", "strongpassword", None)
        new_user_id = 101010
        new_user.id = new_user_id
        db.session.commit()

        retrieved_user = User.query.get(new_user_id)
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.username, "uniqueusername")
        self.assertEqual(retrieved_user.email, "uniqueemail@mail.com")
        self.assertNotEqual(retrieved_user.password, "strongpassword")
        self.assertTrue(retrieved_user.password.startswith("$2b$"))

    def test_registration_with_invalid_username(self):
        user_with_no_username = User.signup(None, "noname@mail.com", "password123", None)
        user_with_no_username.id = 202020
        with self.assertRaises(exc.IntegrityError):
            db.session.commit()

    def test_registration_with_invalid_email(self):
        user_with_no_email = User.signup("username123", None, "password123", None)
        user_with_no_email.id = 303030
        with self.assertRaises(exc.IntegrityError):
            db.session.commit()

    def test_registration_with_invalid_password(self):
        with self.assertRaises(ValueError):
            User.signup("username456", "email456@mail.com", "", None)

        with self.assertRaises(ValueError):
            User.signup("username789", "email789@mail.com", None, None)

    
    def test_valid_authentication(self):
        u = User.authenticate(self.u1.username, "password")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.uid1)
    
    def test_invalid_username(self):
        self.assertFalse(User.authenticate("badusername", "password"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.u1.username, "badpassword"))
