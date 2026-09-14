import os # Python carrega os

import pytest
from pytest import fixture

os.environ["DB_URI"] = "sqlite:///:memory:" # Tu crias/alteras a variável de ambiente -> o banco de teste sempre começa vazio.
from main import app, db, User, generate_password_hash # preciso importar ambos os objetos: a app (preciso da aplicação) e o db (preciso do database)

with app.app_context(): # "Durante este bloco, considera que estamos trabalhando dentro desta aplicação.
    db.create_all() # "Cria as tabelas dos meus models."


client = app.test_client() # Tu criaste um cliente de teste associado à tua aplicação.

@pytest.fixture
def client_logged_in():
    client.post(
        "/auth/register", # registra Maria, Maria fica logada. No endpoint register é isso que acontece.
        json={
            "name": "Maria",
            "email": "maria@test.com",
            "password": "maria123"
        }
    )
    return client # se eu retorno response, por ex, eu digo: "Aqui está a resposta do registro." e não "Aqui está o cliente autenticado."
# Essa distinção entre quem faz a requisição (client) e o resultado da requisição (response) é fundamental em testes de APIs. Você acabou de esbarrar num conceito importante.

@pytest.fixture
def create_user(): # garante que existe a Paula no db de teste para poder fazer login.
    hash_and_salted_password = generate_password_hash(
        "paula123",  # script e o padrao, sera que isso ta certo?
        salt_length=8
    )

    new_user = User(
        email="paula@test.com",
        name="Paula",
        password=hash_and_salted_password,
    )

    db.session.add(new_user)
    db.session.commit()
    return new_user

# REGISTER WITH VALID DATA:
# def test_register_new_user():
#     response = client.post(
#         "/auth/register",
#         json={
#             "name": "Maria",
#             "email": "maria@test.com",
#             "password": "maria123"
#         }
#     )
#
#     assert response.status_code == 201
#     assert response.json["response"]["success"] == "User logged in successfully"
#
# # REGISTER WITH DUPLICATED DATA:
# def test_register_new_user_with_registered_email(client_logged_in):
#     # segundo: tenta criar a mesma Maria
#     response = client.post(
#         "/auth/register",
#         json={
#             "name": "Maria",
#             "email": "maria@test.com",
#             "password": "maria123"
#         }
#     )
#
#     assert response.status_code == 409
#     assert response.json["response"]["error"] == "You've already signed up with that email, log in instead!"

# LOGIN WITH VALID DATA:
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


# CREATE WITH VALID DATA:
# def test_create_book_with_valid_data(client_logged_in):
#     # Faço um registro (la no register eu tenho login_user(new_user) então se eu criar um registro, ele vai ficar logado, aí
#     # client.post( # não vai dar 401 - Unauthorized porque a rota exite @login_required
#     #     "/auth/register",
#     #     json={
#     #         "name": "Maria",
#     #         "email": "maria@test.com",
#     #         "password": "maria123"
#     #     }
#     # )
#
#     response = client.post(
#         "/books",
#         json={
#             "title": "Dune",
#             "author": "Frank Herbert",
#             "genre": "Science Fiction",
#             "year": 1965,
#             "description": "A science fiction novel.",
#             "rating": 5,
#             "status": "Read"
#         }
#     )
#
#     assert response.status_code == 201
#     assert response.json["response"]["success"] == "Book added successfully"

# CREATE WITH INVALID DATA:
# def test_create_book_with_invalid_data(client_logged_in):
#     response = client.post(
#         "/books",
#         json={
#             "title": "Dune",
#             "author": "Frank Herbert",
#             "genre": "Science Fiction",
#             "year": 1965,
#             "description": "A science fiction novel.",
#             "rating": 10,
#             "status": "Read"
#         }
#     )
#
#     assert response.status_code == 400 # a API rejeitou o request
#     assert response.json["response"]["error"] == "Invalid book data" # pelo motivo esperado, não por um erro qualquer.
#
# # CREATE WITHOUT AUTHENTICATION:
# def test_create_book_without_authentication():
#     pass

# GET BOOKS:



# GET UNEXISTENT BOOK:


# VALID PATCH:


# VALID DELETE:


# Campo obrigatório ausente:
# def test_create_book_with_mandatory_field_missing(client_logged_in):
#     response = client.post(
#         "/books",
#         json={
#             "title": "Dune",
#             "genre": "Science Fiction",
#             "year": 1965,
#             "description": "A science fiction novel.",
#             "rating": 2,
#             "status": "Read"
#         }
#     )
#
#     assert response.status_code == 400
#     assert response.json["response"]["error"] == "Title, author and genre are mandatory fields"

# When the users makes a request with an unauthorized field:
# def test_create_book_with_unknown_field(client_logged_in):
#     response = client.post(
#         "/books",
#         json={
#             "title": "Dune",
#             "author": "Frank Herbert",
#             "genre": "Science Fiction",
#             "year": 1965,
#             "description": "A science fiction novel.",
#             "rating": 5,
#             "status": "Read",
#             "owner_id": 999
#         }
#     )
#
#     assert response.status_code == 400
#     assert response.json["response"]["error"] == "One or more fields are not allowed"

