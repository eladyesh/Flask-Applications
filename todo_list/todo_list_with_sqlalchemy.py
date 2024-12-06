from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import registry
from abc import ABC, abstractmethod

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.secret_key = 'your_secret_key'  # Needed for using sessions securely
db = SQLAlchemy(app)

# Abstract base model class
class BaseUserModel(ABC):
    id: int
    username: str
    password: str

    @abstractmethod
    def __init__(self, id: int = None, username: str = None, password: str = None):
        self.id = id
        self.username = username
        self.password = password

    def set_password(self, password: str) -> None:
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)


# User data model class that inherits from BaseUserModel and is mapped to the table
class UserDataModel(BaseUserModel):
    id = None  # Placeholder; will be set later
    username = None
    password = None

    def __init__(self, username: str, password: str, id: int = None):
        super().__init__(id, username, password)  # Call the base class constructor
        self.username = username
        self.password = password

    def __repr__(self):
        return f"<User {self.username}>"


# Todo data model class
class TodoDataModel:
    id = None
    title = None
    description = None
    user_id = None

    def __init__(self, title: str, description: str, user_id: int, id: int = None):
        self.id = id
        self.title = title
        self.description = description
        self.user_id = user_id

    def __repr__(self):
        return f"<Todo {self.title}>"


# SQLAlchemy registry object for classical mapping
mapper_registry = registry()


# Mapping UserDataModel to a table using SQLAlchemy's `map_imperatively`
def setup_user():
    # Create a table for UserDataModel using SQLAlchemy's db.Table directly
    user_table = db.Table(
        'user_data',
        db.metadata,
        db.Column('id', db.Integer, primary_key=True),
        db.Column('username', db.String(80), unique=True, nullable=False),
        db.Column('password', db.String(120), nullable=False)
    )

    # Now we manually map the class to the table using `map_imperatively()`
    mapper_registry.map_imperatively(UserDataModel, user_table)


# Mapping TodoDataModel to a table using SQLAlchemy's `map_imperatively`
def setup_todo():
    # Create a table for TodoDataModel using SQLAlchemy's db.Table directly
    todo_table = db.Table(
        'todo_data',
        db.metadata,
        db.Column('id', db.Integer, primary_key=True),
        db.Column('title', db.String(120), nullable=False),
        db.Column('description', db.String(500), nullable=True),
        db.Column('user_id', db.Integer, db.ForeignKey('user_data.id'), nullable=False)
    )

    # Now we manually map the class to the table using `map_imperatively()`
    mapper_registry.map_imperatively(TodoDataModel, todo_table)


# DatabaseSession Singleton
class DatabaseSession:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if self.__class__.__dict__.get('_instance') is not None:
            raise Exception("This class is a singleton!")
        self.session = db.session

    def commit(self):
        self.session.commit()

    def add(self, obj):
        self.session.add(obj)

    def delete(self, obj):
        self.session.delete(obj)

    def query(self, model):
        return self.session.query(model)


# UserRepository that uses DatabaseSession
class UserRepository:
    def __init__(self):
        self.db_session = DatabaseSession.get_instance()

    def add(self, user: UserDataModel) -> None:
        self.db_session.add(user)
        self.db_session.commit()

    def remove(self, user: UserDataModel) -> None:
        self.db_session.delete(user)
        self.db_session.commit()

    def get_by_id(self, id: int) -> UserDataModel:
        return self.db_session.query(UserDataModel).get(id)

    def get_by_username(self, username: str) -> UserDataModel:
        return self.db_session.query(UserDataModel).filter_by(username=username).first()


# TodoRepository that uses DatabaseSession
class TodoRepository:
    def __init__(self):
        self.db_session = DatabaseSession.get_instance()

    def add(self, todo: TodoDataModel) -> None:
        self.db_session.add(todo)
        self.db_session.commit()

    def remove(self, todo: TodoDataModel) -> None:
        self.db_session.delete(todo)
        self.db_session.commit()

    def get_by_id(self, id: int) -> TodoDataModel:
        return self.db_session.query(TodoDataModel).get(id)

    def get_by_user_id(self, user_id: int) -> list:
        return self.db_session.query(TodoDataModel).filter_by(user_id=user_id).all()


# Routes
@app.before_first_request
def create_tables():
    setup_user()  # This explicitly sets up the mapping for UserDataModel
    setup_todo()   # This explicitly sets up the mapping for TodoDataModel
    db.create_all()  # Create all tables


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user_repo = UserRepository()
    existing_user = user_repo.get_by_username(username)
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400

    new_user = UserDataModel(username=username, password='')
    new_user.set_password(password)

    user_repo.add(new_user)

    return jsonify({'message': 'User registered successfully'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user_repo = UserRepository()
    user = user_repo.get_by_username(username)

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Store user data in the session after successful login
    session['user_id'] = user.id
    session['username'] = user.username

    return jsonify({'message': 'Login successful'}), 200


@app.route('/logout', methods=['POST'])
def logout():
    # Clear the session data on logout
    session.pop('user_id', None)
    session.pop('username', None)
    return jsonify({'message': 'Logout successful'}), 200


@app.route('/users', methods=['GET'])
def get_users():
    # Check if the user is logged in before allowing access to user data
    if 'user_id' not in session:
        return jsonify({'error': 'You must be logged in to view this page'}), 401

    user_repo = UserRepository()
    users = user_repo.db_session.query(UserDataModel).all()
    return jsonify([{'id': u.id, 'username': u.username} for u in users])


@app.route('/todos', methods=['POST'])
def create_todo():
    if 'user_id' not in session:
        return jsonify({'error': 'You must be logged in to create a to-do'}), 401

    data = request.json
    title = data.get('title')
    description = data.get('description')

    if not title:
        return jsonify({'error': 'Title is required'}), 400

    todo_repo = TodoRepository()
    new_todo = TodoDataModel(title=title, description=description, user_id=session['user_id'])
    todo_repo.add(new_todo)

    return jsonify({'message': 'To-do created successfully'}), 201


@app.route('/todos', methods=['GET'])
def get_todos():
    if 'user_id' not in session:
        return jsonify({'error': 'You must be logged in to view your to-dos'}), 401

    todo_repo = TodoRepository()
    todos = todo_repo.get_by_user_id(session['user_id'])
    return jsonify([{'id': t.id, 'title': t.title, 'description': t.description} for t in todos])


if __name__ == '__main__':
    app.run(debug=True)
