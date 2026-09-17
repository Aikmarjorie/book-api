# CONSTANTS:
ALLOWED_STATUS = {
    "Reading",
    "Read",
    "Unread"
}

ALLOWED_GENRES = {
    "Fantasy",
    "Science Fiction",
    "Mystery",
    "Thriller",
    "Romance",
    "Horror",
    "Historical Fiction",
    "Biography",
    "Non-fiction",
}

ALLOWED_BOOK_FIELDS = {
    "title",
    "author",
    "genre",
    "year",
    "description",
    "rating",
    "status"
}

# Validate the user data sent by the client.
def validate_user_data(user):
    for field in ["name","email","password"]:
        if not isinstance(user[field], str) or not user[field].strip():
            return False

    if len(user["name"]) > 50:
        return False

    if user["email"].count("@") != 1:
        return False

    if user["email"].find("@") == 0:
        return False

    if user["email"].find("@") > user["email"].find("."):
        return False

    if user["email"].find(".") >= len(user["email"]) -1:
        return False

    if len(user["password"]) < 8:
        return False

    return True

# Validate the book data sent by the client.
def validate_book_data(data):
    # Validate basic text fields when provided.
    for field in ["title", "author", "genre"]:
        if field in data:
            if not isinstance(data[field], str) or not data[field].strip():
                return False
    # Check that the genre is allowed.
    if "genre" in data:
        if data["genre"] not in ALLOWED_GENRES:
            return False

    # Validate the publication year when provided.
    if "year" in data:
        if not isinstance(data["year"], int) or data["year"] < 0:
            return False

    # Validate the description when provided.
    if "description" in data:
        if not isinstance(data["description"], str) or not data["description"].strip():
            return False

    # Validate the rating when provided.
    if "rating" in data:
        if not isinstance(data["rating"], int):
            return False
        if not 0 <= data["rating"] <= 5:
            return False

    # Validate the reading status when provided.
    if "status" in data:
        if not isinstance(data["status"], str):
            return False
        if data["status"] not in ALLOWED_STATUS:
            return False

    return True
