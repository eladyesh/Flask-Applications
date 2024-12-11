from dataclasses import dataclass, field
from flask_sqlalchemy import SQLAlchemy
import hashlib

# Initialize the database object (This would be part of your Flask app setup)
db = SQLAlchemy()

# Enforcer as a dataclass with required attributes and methods
@dataclass
class Enforcer:
    # Declare required attributes and methods as class variables
    required_attributes: list = field(default_factory=lambda: ['name', 'id'])
    required_methods: list = field(default_factory=lambda: ['set_password', 'check_password'])

    def __post_init__(self):
        # Dynamically enforce the presence of required attributes
        for attr in self.required_attributes:
            if not hasattr(self, attr):
                raise TypeError(f"Class must have a '{attr}' attribute")

        # Dynamically enforce the presence of required methods
        for method in self.required_methods:
            if not callable(getattr(self, method, None)):
                raise TypeError(f"Class must implement '{method}' method")


# User model that combines db.Model and Enforcer dataclass
class User(db.Model, Enforcer):
    __tablename__ = 'users'

    # Define the SQLAlchemy fields
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    _password_hash = db.Column(db.String(256), nullable=False)

    def __init__(self, name: str, password: str = None):
        # Enforcer checks are automatically handled in __post_init__ from Enforcer dataclass
        super().__init__()

        # Initialize SQLAlchemy fields
        self.name = name
        if password:
            self.set_password(password)

    def set_password(self, password: str):
        """Hash the password and store the hash"""
        self._password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the stored hash"""
        return self._password_hash == hashlib.sha256(password.encode('utf-8')).hexdigest()


# Example Flask app to use the User model
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory SQLite for demo purposes
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # Create the tables in the database
    db.create_all()

    # Create a new user
    new_user = User(name="john_doe", password="supersecret")
    db.session.add(new_user)
    db.session.commit()

    # Query the user and check the password
    user_from_db = User.query.filter_by(name="john_doe").first()
    print(user_from_db.check_password("supersecret"))  # True
    print(user_from_db.check_password("wrongpassword"))  # False