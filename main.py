from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from sqlalchemy import Integer, String, Text, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

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

app = Flask(__name__)

# CREATE DB
class Base(DeclarativeBase):
    pass

# CONNECT TO DATABASE
# DB_URI can be changed through an environment variable for deployment.
# SQLite is used locally by default.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI","sqlite:///books.db")
app.config['SECRET_KEY'] = os.environ["FLASK_KEY"] # Uma chave que fica dentro do servidor e que o Flask usa para proteger informações de segurança.
                                                   # SECRET_KEY = segredo interno usado pelo Flask para proteger mecanismos como sessões.

# CREATE DB OBJECT:
db = SQLAlchemy(model_class=Base)

# CONNECT FLASK + SQLALCHEMY:
db.init_app(app)

# CONFIGURE APP FLASK-LOGIN:
# login_manager = LoginManager()
# login_manager.login_view = "login"
# login_manager.login_message = "Please log in to continue."
# login_manager.init_app(app)

# FLASK-LOGIN USER LOADER CALLBACK:
# Flask-Login uses this function to reload the logged-in user from the database.
# @login_manager.user_loader
# def load_user(user_id):
#     return  db.session.get(User, user_id)

# CREATE MODELS
class Book(db.Model):
    __tablename__ = "book_table"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    title: Mapped[str] = mapped_column(String(500),nullable=False) # essa coluna não pode receber Null, portanto, campo obrigatório
    author: Mapped[str] = mapped_column(String(250),nullable=False)
    genre: Mapped[str] = mapped_column(String(250),nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text,nullable=True)
    rating: Mapped[int] = mapped_column(Integer,nullable=True)
    status: Mapped[str] = mapped_column(String(250),nullable=True)

    owner_id: Mapped[int] = mapped_column(ForeignKey("user_table.id"),nullable=False) # porque eu colocaria nullable=False aqui?
    owner: Mapped["User"] = relationship(back_populates="books") # book.owner => User -> qual o owner desse book?

    # Transformar o objeto Book num dicionário Python, porque o Flask precisa devolver uma resposta que possa ser representada como JSON.
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class User(UserMixin,db.Model): # parent one user can have several books
    __tablename__ = "user_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(225), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(500),nullable=False)

    books: Mapped[list["Book"]] = relationship(back_populates="owner") # user.books => [Book, Book, Book...] -> quais os books pertencem a esse user
    # back_populates conecta os 2 lados: Singular → quem é o meu dono? book.owner; Plural -> Quais são meus books? user.books

with app.app_context():
    db.create_all()

# VALIDADE USER FUNCTION:
def validate_user(user):
    pass # regras para validação dos campos do user model

# CREATE ROUTES / endpoints
# AUTHENTICATION:
# POST /auth/register
@app.route("/auth/register",methods=["POST"])
def register():
    pass


# POST /auth/login
@app.route("/auth/login",methods=["POST"])
def login():
    pass


# POST /auth/logout
@app.route("/auth/logout",methods=["POST"])
def logout():
    pass

# BOOKS - CRUD SIMPLES:
# GET    /books
@app.route("/books")
def all_books():
    result = db.session.execute(db.select(Book)).scalars().all()
    books = [book.to_dict() for book in result]

    return jsonify(books=books)

# GET    /books/<id>
@app.route("/books/<int:book_id>")
def one_book(book_id):
    result = db.get_or_404(Book, book_id) # procuro pela primary key e o get_or_404 já trata o None
    book = result.to_dict()

    return jsonify(book=book)

# FUNCTION TO VALIDATE BOOK DATA:
# Regras de validação para os campos do Book:
def validate_book_data(data):
    # Validação dos campos básicos, caso tenham sido enviados:
    for field in ["title", "author", "genre"]:
        if field in data:
            if not isinstance(data[field], str) or not data[field].strip():
                return False
    if "genre" in data:
        if data["genre"] not in ALLOWED_GENRES:
            return False

    # Demais campos, verificação: foram enviados? Se sim -> São válidos?
    if "year" in data:
        if not isinstance(data["year"], int):
            return False

    if "description" in data:
        if not isinstance(data["description"], str):
            return False

    if "rating" in data:
        if not isinstance(data["rating"], int):
            return False
        if not 0 <= data["rating"] <= 5:
            return False

    if "status" in data:
        if not isinstance(data["status"], str):
            return False
        if data["status"] not in ALLOWED_STATUS:
            return False

    return True

# POST  /books -> criar
@app.route("/books",methods=["POST"])
def create_book():
    data = request.json # pegar o JSON que chegou do Bruno, já como dict python
    # return jsonify(dados)

    # Se qualquer um dos campos obrigatórios estiver faltando -> rejeitar.
    if not "title" in data or not "author" in data or not "genre" in data:
        return jsonify(response={"error": "Title, author and genre are mandatory fields"}), 400

    # Campo existe, porém, inválido:
    if not validate_book_data(data):
        return jsonify(response={"error": "Invalid book data"}), 400

    # Se tudo ok, cria book:
    new_book = Book( # lado esquerdo: é o atributo/parâmetro da classe Cafe; lado direito é o dado que veio do Bruno.
        # Dados fornecidos pelo cliente:
        # Esses campos devem existir (depois da validação acima):
        title=data["title"], # acesso as chaves via .get() x ["chave"] -> com .get() se chave não existir => None, não KeyError.
        author=data["author"], # mas, nesse caso, depois da validação, a chave deveria existir, portanto ["title"] é mais coerente.
        genre=data["genre"],

        # .get() esses campos podem não existir
        year=data.get("year"),
        description=data.get("description"),
        rating=data.get("rating"),
        status=data.get("status"),

        # Dados determinados pelo servidor:
        # owner_id=dados.get("owner_id")
        )

    db.session.add(new_book)
    db.session.commit()

    return jsonify(response={"success": "Book added successfully"}), 201

# PATCH /books/<id> -> editar parcialmente
@app.route("/books/<int:book_id>",methods=["PATCH"])
def partially_update_book(book_id): # JSON → verificar se existe → validar → procurar Book → alterar → commit
    # Pego JSON que chegou do Bruno, já como dict python
    data = request.json

    # Verifico se foram enviados campos para atualização:
    if not data:
        return jsonify(response={"error": "No fields provided for update"}), 400

    # Verifico os dados antes de alterar qualquer campo do livro:
    if not validate_book_data(data):
        return jsonify(response={"error": "Invalid book data"}), 400

    # Encontro no banco o Book que tem esse id:
    book = db.get_or_404(Book, book_id)

    # Atualizo somente os campos enviados pelo cliente:
    for field in ALLOWED_BOOK_FIELDS:
        if field in data:
            setattr(book,field,data[field])

    db.session.commit()

    return jsonify(response={"success": "Book edited successfully"}), 200

# DELETE /books/<id> -> apagar
@app.route("/books/<int:book_id>",methods=["DELETE"])
def delete_book(book_id):
    # Encontro o livro a ser deletado usando o book_id (primary key):
    book = db.get_or_404(Book,book_id) # o get_or_404 já trata se não existir o book.

    # Digo ao banco: "quero que esse objeto seja removido da sessão":
    db.session.delete(book)
    db.session.commit()

    return jsonify(response={"success": "Book successfully deleted"}), 200


# FILTROS:
# GET /books?genre=fantasy -> "Que tipo de livro?"
# GET /books?status=read -> "Qual é o estado da leitura?"


if __name__ == '__main__':
    app.run(debug=True,port=5001)