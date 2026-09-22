import os
import pytest

# Use an in-memory SQLite database for testing.
os.environ["DB_URI"] = "sqlite:///:memory:"

from main import app, db, User, generate_password_hash

# Create a test client for sending requests to the application.
client = app.test_client()

# FIXTURES
@pytest.fixture
def client_logged_in():
    client.post(
        "/auth/register",
        json={
            "name": "Maria",
            "email": "maria@test.com",
            "password": "maria123"
        }
    )
    return client

@pytest.fixture
def create_user():
    # Create a user for tests that require an existing user.
    with app.app_context():
        hashed_password = generate_password_hash(
            "paula123",
        )

        new_user = User(
            email="paula@test.com",
            name="Paula",
            password=hashed_password,
        )

        db.session.add(new_user)
        db.session.commit()

@pytest.fixture(autouse=True)
def reset_database():
    # Reset the database before each test.
    with app.app_context():
        db.drop_all()
        db.create_all()

@pytest.fixture
def create_book(client_logged_in):
    # Create a book for tests that require an existing book.
    client_logged_in.post(
        "/books",
        json={
            "title": "Dune",
            "author": "Frank Herbert",
            "genre": "Science Fiction",
            "year": 1965,
            "description": "A science fiction novel.",
            "rating": 5,
            "status": "Read"
        }
    )

# AUTHENTICATION TESTS
# Register with valid data
def test_register_new_user():
    response = client.post(
        "/auth/register",
        json={
            "name": "Maria",
            "email": "maria@test.com",
            "password": "maria123"
        }
    )

    assert response.status_code == 201
    assert response.json["response"]["success"] == "User registered and logged in successfully"

# Register with a duplicated email
def test_register_new_user_with_registered_email(client_logged_in):
    response = client_logged_in.post(
        "/auth/register",
        json={
            "name": "Maria",
            "email": "maria@test.com",
            "password": "maria123"
        }
    )

    assert response.status_code == 409
    assert response.json["response"]["error"] == "You've already signed up with that email, log in instead!"

# Login with valid data
def test_login_with_valid_data(create_user):
    response = client.post(
        "/auth/login",
        json={
            "email": "paula@test.com",
            "password": "paula123"
        }
    )
    assert response.status_code == 200
    assert response.json["response"]["success"] == "User logged in successfully"

# Login with a non-existent email
def test_login_with_nonexistent_email():
    response = client.post(
        "/auth/login",
        json={
            "email": "carlos@test.com",
            "password": "carlos456"
        }
    )
    assert response.status_code == 401
    assert response.json["response"]["error"] == "Unauthorized: wrong email or password"

# BOOK TESTS
# POST ENDPOINT
# Create book with valid data
def test_create_book_with_valid_data(client_logged_in):
    response = client_logged_in.post(
        "/books",
        json={
            "title": "Dune",
            "author": "Frank Herbert",
            "genre": "Science Fiction",
            "year": 1965,
            "description": "A science fiction novel.",
            "rating": 5,
            "status": "Read"
        }
    )

    assert response.status_code == 201
    assert response.json["response"]["success"] == "Book added successfully"

# Create book with invalid data
def test_create_book_with_invalid_data(client_logged_in):
    response = client_logged_in.post(
        "/books",
        json={
            "title": "Dune",
            "author": "Frank Herbert",
            "genre": "Science Fiction",
            "year": 1965,
            "description": "A science fiction novel.",
            "rating": 10,
            "status": "Read"
        }
    )

    assert response.status_code == 400
    assert response.json["response"]["error"] == "Invalid book data"

# GET ENDPOINTS
# Get all books without filters
def test_search_books(client_logged_in):
    response = client_logged_in.get(
        "/books",
    )
    assert response.status_code == 200

# Get books with a genre filter
def test_search_books_with_filter(create_book):
    response = client.get(
        "/books",
        query_string={
            "genre": "Science Fiction"
        }
    )

    assert response.status_code == 200
    assert len(response.json["books"]) == 1
    assert response.json["books"][0]["genre"] == "Science Fiction"

# Get an existing book
def test_one_book(create_book):
    # The user must be logged in and the book must exist.
    # The create_book fixture handles both requirements.
    response = client.get(
        "/books/1",
    )
    assert response.status_code == 200

# Get a non-existent book
def test_one_book_not_found(client_logged_in):
    response = client_logged_in.get(
        "/books/999",
    )
    assert response.status_code == 404
    assert response.json["response"]["error"] == "Book not found"

# PATCH ENDPOINT
# Update an existing book
def test_partially_update_book(create_book):
    response = client.patch(
        "/books/1",
        json={
            "title": "Dunne"
        }
    )
    assert response.status_code == 200
    assert response.json["response"]["success"] == "Book edited successfully"

    # Verify that the book was actually updated.
    response = client.get(
        "/books/1"
    )
    assert response.status_code == 200
    assert response.json["book"]["title"] == "Dunne"

# Reject invalid book data
def test_partially_update_book_invalid_data(create_book):
    response = client.patch(
        "/books/1",
        json={
            "rating": "20"
        }
    )
    assert response.status_code == 400
    assert response.json["response"]["error"] == "Invalid book data"

# DELETE ENDPOINT
# Delete an existing book
def test_delete_book(create_book):
    response = client.delete(
        "/books/1",
    )
    assert response.status_code == 200
    assert response.json["response"]["success"] == "Book successfully deleted"

    # Verify that the book was actually deleted.
    response = client.get(
        "/books/1"
    )
    assert response.status_code == 404
    assert response.json["response"]["error"] == "Book not found"

# Delete a non-existent book
def test_delete_nonexistent_book(client_logged_in):
    response = client_logged_in.delete(
        "/books/40"
    )
    assert response.status_code == 404
    assert response.json["response"]["error"] == "Book not found"

# AUTHORIZATION TESTS
# Create a book without authentication
def test_create_book_without_authentication():
    response = client.post(
        "/books",
        json={
            "title": "The Hobbit",
            "author": "J.R.R. Tolkien",
            "genre": "Fantasy",
            "year": 1937,
            "description": "A fantasy adventure novel about Bilbo Baggins.",
            "rating": 5,
            "status": "Read"
        }
    )
    assert response.status_code == 401

