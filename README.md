# Book API

A RESTful API built with Flask for managing a personal book collection.

Authenticated users can create, view, update, delete and filter their own books. 
The API uses JSON requests and responses, HTTP status codes, server-side validation and automated tests with pytest.

This project focuses on backend API development rather than a graphical user interface.

## Features

### Book Management

* Create books
* Retrieve books
* Retrieve a single book
* Partially update books
* Delete books
* Filter books by genre and reading status

### Authentication

* User registration and login
* Password hashing with Werkzeug
* Session-based authentication with Flask-Login
* Protected book endpoints

### Validation

Incoming data is validated on the server before being stored or updated.

### Ownership

Each book is associated with the authenticated user who created it.

Book operations check both the book ID and the authenticated user's ID, so users can only access and modify their own books.

## API Endpoints

### Authentication

| Method | Endpoint         | Description         |
| ------ | ---------------- | ------------------- |
| POST   | `/auth/register` | Register a new user |
| POST   | `/auth/login`    | Log in              |
| POST   | `/auth/logout`   | Log out             |

### Books

| Method | Endpoint           | Description                             |
| ------ | ------------------ | --------------------------------------- |
| POST   | `/books`           | Create a book                           |
| GET    | `/books`           | Retrieve the authenticated user's books |
| GET    | `/books/<book_id>` | Retrieve one book                       |
| PATCH  | `/books/<book_id>` | Partially update a book                 |
| DELETE | `/books/<book_id>` | Delete a book                           |

### Filtering

The `GET /books` endpoint supports filtering through query parameters.

Examples:

```text
GET /books?genre=Fantasy
GET /books?status=Reading
GET /books?genre=Science%20Fiction&status=Read
```

If no books match the filters, the API returns an empty list.

## Validation Rules

The API applies server-side validation to incoming data.

### User registration

* Passwords must contain at least 8 characters.
* Names are limited to 50 characters.
* Email validation is intentionally basic and is not intended to cover every possible valid email format.
* Name, email and password are required.

### Books

* `title`, `author` and `genre` are required when creating a book.
* `genre` must be one of the allowed genre values.
* `status` must be one of the allowed status values.
* `rating` must be an integer between 0 and 5.
* `year` must be a non-negative integer.
* `PATCH` requests only accept fields defined by the API.
* Empty or whitespace-only values are rejected for applicable string fields.

The API intentionally uses manual validation in the current version.

## JSON Requests

Endpoints that receive data expect a JSON request body.

Requests should use:

```text
Content-Type: application/json
```

For example, creating a book requires a JSON body:

```json
{
  "title": "Dune",
  "author": "Frank Herbert",
  "genre": "Science Fiction",
  "year": 1965,
  "description": "A science fiction novel.",
  "rating": 5,
  "status": "Read"
}
```

Query parameters are used separately for filtering:

```text
GET /books?genre=Science%20Fiction
```

## Example Response

A successful book creation returns:

```json
{
  "response": {
    "success": "Book added successfully"
  }
}
```

A request for books returns a JSON list:

```json
{
  "books": [
    {
      "id": 1,
      "title": "Dune",
      "author": "Frank Herbert",
      "genre": "Science Fiction",
      "year": 1965,
      "description": "A science fiction novel.",
      "rating": 5,
      "status": "Read",
      "owner_id": 1
    }
  ]
}
```

## HTTP Status Codes

| Status | Meaning                                         |
| ------ | ----------------------------------------------- |
| 200    | Request successful                              |
| 201    | Resource created successfully                   |
| 400    | Invalid request or data                         |
| 401    | Authentication required or invalid credentials  |
| 404    | Resource not found                              |
| 409    | Conflict, such as registering an existing email |

## Tech Stack

* Python
* Flask
* Flask-SQLAlchemy
* SQLAlchemy
* Flask-Login
* SQLite
* python-dotenv
* pytest

## Database

The application uses SQLite with SQLAlchemy.

There are two main models:

### User

Stores user and authentication information.

### Book

Stores book information and belongs to a specific user through a foreign key.

The relationship is:

```text
User → Books (one-to-many)
```

A user can own multiple books, while each book belongs to one user.

## Testing

The project includes automated tests using pytest.

The test suite covers the main API flows, including:

* User registration
* Duplicate registration
* Login
* Invalid authentication
* Book creation
* Invalid book data
* Book retrieval
* Book filtering
* Book updates
* Book deletion
* Protected endpoint access

Tests use an in-memory SQLite database so they do not modify the development database.

Run the tests with:

```bash
pytest
```

## Known Limitations & Future Improvements

This project intentionally keeps the API small and focused. The following are known limitations or possible future improvements:

* **Database:** The application currently uses SQLite. PostgreSQL could be used for a production environment.
* **Database migrations:** Database schema creation currently relies on `db.create_all()`. Flask-Migrate could be introduced for managing schema changes through migrations.
* **Validation:** Validation is implemented manually. It could be expanded or replaced with a schema validation library such as Pydantic in a future version.
* **Email validation:** The current email validation is intentionally basic and does not attempt to support every possible valid email format.
* **API documentation:** API documentation could be expanded using OpenAPI/Swagger.
* **Authentication:** The current authentication uses Flask-Login sessions. Token-based authentication could be considered for clients that need a stateless API authentication mechanism.
* **Pagination:** Pagination could be introduced if the number of books becomes large.

These are potential extensions rather than requirements for the current version.

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/Aikmarjorie/book-api.git
cd book-api
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows:**

```bash
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file:

```env
FLASK_KEY=your-secret-key
DB_URI=sqlite:///books.db
```

Do not commit your `.env` file to GitHub.

### 5. Run the application

```bash
python main.py
```

The API will be available at `http://127.0.0.1:5001`.

You can interact with the API using an HTTP client such as Bruno or Postman.

## What I Learned

This project helped me understand backend API development with Flask.

I learned how to:

* Build REST-style endpoints using different HTTP methods.
* Work with JSON requests and responses.
* Use HTTP status codes to communicate API results.
* Use query parameters for filtering.
* Validate incoming API data on the server.
* Associate database resources with authenticated users.
* Enforce ownership at the database query level.
* Write focused automated tests with pytest.
* Use an isolated in-memory database during testing.
* Separate configuration and secrets from application code using environment variables.
