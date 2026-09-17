from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from sqlalchemy import Integer, String, Text, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from validators import ALLOWED_STATUS, ALLOWED_GENRES, ALLOWED_BOOK_FIELDS, validate_book_data, validate_user_data

load_dotenv()

app = Flask(__name__)

# CREATE DB
class Base(DeclarativeBase):
    pass

# CONNECT TO DATABASE
# Use DB_URI if available; otherwise, use the local SQLite database.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI","sqlite:///books.db")
app.config['SECRET_KEY'] = os.environ["FLASK_KEY"]

# CREATE DB OBJECT
db = SQLAlchemy(model_class=Base)

# CONNECT FLASK + SQLALCHEMY
db.init_app(app)

# CONFIGURE APP FLASK-LOGIN
login_manager = LoginManager()
login_manager.init_app(app)

# FLASK-LOGIN USER LOADER CALLBACK
# Flask-Login uses this function to reload the logged-in user from the database.
@login_manager.user_loader
def load_user(user_id):
    return  db.session.get(User, user_id)

# CREATE MODELS
class Book(db.Model):
    __tablename__ = "book_table"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    title: Mapped[str] = mapped_column(String(500),nullable=False)
    author: Mapped[str] = mapped_column(String(250),nullable=False)
    genre: Mapped[str] = mapped_column(String(250),nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text,nullable=True)
    rating: Mapped[int] = mapped_column(Integer,nullable=True)
    status: Mapped[str] = mapped_column(String(250),nullable=True)

    owner_id: Mapped[int] = mapped_column(ForeignKey("user_table.id"),nullable=False)
    owner: Mapped["User"] = relationship(back_populates="books")

    # Convert the Book object into a Python dictionary so Flask can return it as JSON.
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class User(UserMixin,db.Model):
    __tablename__ = "user_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(225), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(500),nullable=False)

    books: Mapped[list["Book"]] = relationship(back_populates="owner")

with app.app_context():
    db.create_all()

# CREATE ROUTES / endpoints
# AUTHENTICATION:
# POST /auth/register
@app.route("/auth/register",methods=["POST"])
def register():
    # Get the JSON data sent by the client.
    user_data = request.json

    # Check if mandatory fields exist.
    if not "name" in user_data or not "email" in user_data or not "password" in user_data:
        return jsonify(response={"error": "Name, email and password are mandatory fields"}), 400

    # Check if they are valid.
    if not validate_user_data(user_data):
        return jsonify(response={"error": "Invalid user data"}), 400

    result = db.session.execute(db.select(User).where(User.email == user_data["email"]))
    user = result.scalar()

    if user:
        return jsonify(response={"error": "You've already signed up with that email, log in instead!"}), 409

    hash_and_salted_password = generate_password_hash(
        user_data["password"]
    )

    new_user = User(
        email=user_data["email"],
        name=user_data["name"],
        password=hash_and_salted_password,
    )

    db.session.add(new_user)
    db.session.commit()

    # This line will authenticate the user with Flask-Login and keep him logged in.
    login_user(new_user)

    return jsonify(response={"success": "User logged in successfully"}), 201


# POST /auth/login
@app.route("/auth/login",methods=["POST"])
def login():
    # Get the JSON data sent by the client.
    user_data = request.json

    # Check if mandatory fields exist.
    if not "email" in user_data or not "password" in user_data:
        return jsonify(response={"error": "Email and password are mandatory fields"}), 400

    result = db.session.execute(db.select(User).where(User.email == user_data["email"]))
    user = result.scalar()

    if not user:
        return jsonify(response={"error": "Unauthorized: wrong email or password"}), 401

    if not check_password_hash(user.password,user_data["password"]):
        return jsonify(response={"error": "Password incorrect, try again"}), 401

    login_user(user)
    return jsonify(response={"success": "User logged in successfully"}), 200

# POST /auth/logout
@app.route("/auth/logout",methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"success": "You've been logged out"}),200

# CRUD BOOKS:
# GET /books
@app.route("/books")
@login_required
def search_books():
    # Get optional filters from the query string.
    books_genre = request.args.get("genre")
    books_status = request.args.get("status")

    if not books_genre and not books_status:
        result = db.session.execute(db.select(Book).where(Book.owner_id == current_user.id)).scalars().all()
        books = [book.to_dict() for book in result]
        return jsonify(books=books)

    # Start with the current user's books and add filters when provided.
    query = db.select(Book).where(Book.owner_id == current_user.id)

    if books_genre:
        # Reject invalid genre values before querying the database.
        if books_genre not in ALLOWED_GENRES:
            return jsonify(error={"Bad request": "Sorry, genre not allowed"}), 400
        query = query.where(Book.genre == books_genre)

    if books_status:
        # Reject invalid status values before querying the database.
        if books_status not in ALLOWED_STATUS:
            return jsonify(error={"Bad request": "Sorry, status not allowed."}), 400
        query = query.where(Book.status == books_status)

    # Execute the query after applying the requested filters.
    result = db.session.execute(query).scalars().all()
    books = [book.to_dict() for book in result]

    return jsonify(books=books)


# GET /books/<id>
@app.route("/books/<int:book_id>")
@login_required
def one_book(book_id):
    result = db.session.execute(db.select(Book).where(Book.id == book_id, Book.owner_id == current_user.id)).scalar_one_or_none()
    if result is None:
        return jsonify(response={"error": "Book not found"}), 404
    book = result.to_dict()

    return jsonify(book=book)

# POST /books
@app.route("/books",methods=["POST"])
@login_required
def create_book():
    # Get the JSON data sent by the client.
    data = request.json

    # Reject fields that are not accepted by the API.
    if any(field not in ALLOWED_BOOK_FIELDS for field in data):
        return jsonify(
            response={"error": "One or more fields are not allowed"}
        ), 400

    # Check that all required fields are provided.
    if not "title" in data or not "author" in data or not "genre" in data:
        return jsonify(response={"error": "Title, author and genre are mandatory fields"}), 400

    # Validate the provided values.
    if not validate_book_data(data):
        return jsonify(response={"error": "Invalid book data"}), 400

    # Create the book using the validated client data.
    new_book = Book(
        title=data["title"],
        author=data["author"],
        genre=data["genre"],
        year=data.get("year"),
        description=data.get("description"),
        rating=data.get("rating"),
        status=data.get("status"),

        # The server determines the owner from the authenticated user.
        owner_id=current_user.id,
        )

    db.session.add(new_book)
    db.session.commit()

    return jsonify(response={"success": "Book added successfully"}), 201

# PATCH /books/<id>
@app.route("/books/<int:book_id>",methods=["PATCH"])
@login_required
def partially_update_book(book_id):
    # Get the JSON data sent by the client.
    data = request.json

    # Reject requests without any fields to update.
    if not data:
        return jsonify(response={"error": "No fields provided for update"}), 400

    # Reject fields that are not accepted by the API.
    if any(field not in ALLOWED_BOOK_FIELDS for field in data):
        return jsonify(
            response={"error": "One or more fields cannot be updated"}
        ), 400

    # Validate the provided values before updating the book.
    if not validate_book_data(data):
        return jsonify(response={"error": "Invalid book data"}), 400

    # Find the book only if it belongs to the authenticated user.
    book = db.session.execute(db.select(Book).where(Book.id == book_id,Book.owner_id == current_user.id)).scalar_one_or_none()

    if book is None:
        return jsonify(response={"error": "Book not found"}), 404

    # Update only the fields provided by the client.
    for field in ALLOWED_BOOK_FIELDS:
        if field in data:
            setattr(book,field,data[field])

    db.session.commit()

    return jsonify(response={"success": "Book edited successfully"}), 200

# DELETE /books/<id>
@app.route("/books/<int:book_id>",methods=["DELETE"])
@login_required
def delete_book(book_id):
    # Find the book by ID and make sure it belongs to the authenticated user.
    book = db.session.execute(db.select(Book).where(Book.id == book_id, Book.owner_id == current_user.id)).scalar_one_or_none()

    if book is None:
        return jsonify(response={"error": "Book not found"}), 404

    # Mark the book for deletion and commit the change to the database.
    db.session.delete(book)
    db.session.commit()

    return jsonify(response={"success": "Book successfully deleted"}), 200


if __name__ == '__main__':
    app.run(debug=True,port=5001)