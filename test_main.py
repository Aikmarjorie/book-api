import os
import pytest
from pytest import fixture
from main import app, db, User, generate_password_hash

# Use an in-memory SQLite database for testing.
os.environ["DB_URI"] = "sqlite:///:memory:"

# Create the database tables before running the tests.
with app.app_context():
    db.create_all()

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
    with app.app_context():
        hash_and_salted_password = generate_password_hash(
            "paula123",
        )

        new_user = User(
            email="paula@test.com",
            name="Paula",
            password=hash_and_salted_password,
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
    assert response.json["response"]["success"] == "User logged in successfully"

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
            "name": "Paula",
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
            "name": "Carlos",
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
def test_search_books_with_filter(client_logged_in):
    response = client_logged_in.get(
        "/books",
        query_string={
            "genre": "Fantasy"
        }
    )

    assert response.status_code == 200

# Get an existing book
def test_one_book(create_book): # o usuário precisa estar logado E o book precisa existir (a fixture create_book ja trata os 2 casos)
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
def test_delete_unexistent_book(client_logged_in):
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

