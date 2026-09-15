import os # Python carrega os

import pytest
from pytest import fixture

os.environ["DB_URI"] = "sqlite:///:memory:" # Tu crias/alteras a variável de ambiente -> o banco de teste sempre começa vazio.
from main import app, db, User, generate_password_hash # preciso importar ambos os objetos: a app (preciso da aplicação) e o db (preciso do database)

with app.app_context(): # "Durante este bloco, considera que estamos trabalhando dentro desta aplicação.
    db.create_all() # "Crie, nesse banco de teste, todas as tabelas correspondentes aos meus Models."
    # Aqui, no início da página, significa: "Antes dos testes começarem, quero que as tabelas existam."


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
def create_user(): # garante que existe a Paula no db de teste para poder fazer login. db.create_all() lá em cima permite que as tabelas existam, ambos são necessários.
    with app.app_context():
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
# Já a sua create_user precisa do contexto quando ela própria executa:

# AUTHENTICATION TESTING
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
#     assert response.status_code == 201 # ou 200? checar isso aqui e na main!
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
# def test_login_with_valid_data(create_user): # "Antes de rodar este teste, garanta que existe uma Paula no banco, através da fixture create_user."
#     response = client.post(
#         "/auth/login",
#         json={
#             "name": "Paula",
#             "email": "paula@test.com",
#             "password": "paula123"
#         }
#     )
#     assert response.status_code == 200
#     assert response.json["response"]["success"] == "User logged in successfully"

# LOGIN WITH INVALID DATA: voltar aqui -> limpeza de banco, conceito chato.
# def test_login_with_invalid_data(create_user):
#     response = client.post(
#         "/auth/login",
#         json={
#             "name": "Carlos",
#             "email": "carlos@test.com",
#             "password": "carlos456"
#         }
#     )
#     assert response.status_code == 401
#     assert response.json["response"]["error"] == "Unauthorized: wrong email or password"

# BOOKS TESTING
# CREATE BOOK WITH VALID DATA:
def test_create_book_with_valid_data(client_logged_in):
    response = client.post(
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

# CREATE BOOK WITH INVALID DATA:
def test_create_book_with_invalid_data(client_logged_in):
    response = client.post(
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

    assert response.status_code == 400 # a API rejeitou o request
    assert response.json["response"]["error"] == "Invalid book data" # pelo motivo esperado, não por um erro qualquer.
#

# GET BOOKS:
# SHOW ALL BOOKS WITHOUT FILTER:
def test_search_books(client_logged_in):
    response = client.get(
        "/books",
    )
    assert response.status_code == 200

# SHOW BOOKS WITH ONE FILTER:
def test_search_books_with_filter(client_logged_in):
    response = client.get(
        "/books",
        query_string={
            "genre": "Fantasy"
        }
    )

    assert response.status_code == 200

# GET UNEXISTENT BOOK:
# BUSCAR INEXISTENTE
def test_one_book(client_logged_in):
    response = client.get(
        "/books/1",
    )
    assert response.status_code == 200

def test_one_book_not_found(client_logged_in):
    response = client.get(
        "/books/999",
    )
    assert response.status_code == 404
    assert response.json["response"]["error"] == "Book not found"

# Na sua rota GET /books/<book_id>, você não precisa colocar json, porque a informação que a rota precisa (book_id) já está na própria URL
# Quando usar json no teste? Quando você está enviando dados no corpo da requisição, principalmente em POST e PATCH.

# VALID PATCH:
# UPDATE BOOK:
def test_partially_update_book(client_logged_in):
    response = client.patch(
        "/books/1",
        json={
            "title": "Dunne"
        }
    )
    assert response.status_code == 200
    assert response.json["response"]["success"] == "Book edited successfully"

    response = client.get( # para verificar se ele realmente foi modificado
        "/books/1"
    )
    assert response.status_code == 200
    assert response.json["book"]["title"] == "Dunne"

def test_partially_update_book_invalid_data(client_logged_in):
    response = client.patch(
        "/books/1",
        json={
            "rating": "20"
        }
    )
    assert response.status_code == 400
    assert response.json["response"]["error"] == "Invalid book data"

# DELETE BOOK:
def test_delete_book(client_logged_in):
    response = client.delete(
        "/books/1",
    )
    assert response.status_code == 200
    assert response.json["response"]["success"] == "Book successfully deleted"

    response = client.get(
        "/books/1"
    )
    assert response.status_code == 404
    assert response.json["response"]["error"] == "Book not found"

def test_delete_unexistent_book(client_logged_in):
    response = client.delete(
        "/books/40"
    )
    assert response.status_code == 404
    assert response.json["response"]["error"] == "Book not found"

# CREATE BOOK WITHOUT AUTHENTICATION:
def test_create_book_without_authentication():
    pass

# Usuário A não acessa livro do usuário B → 404
def test_user1_access_book_user2():
    pass

# Funções de validação separadas -> os endpoints já as exercitam indiretamente, e ela não são tão complexas assim para eu
# fazer testes separados para elas.