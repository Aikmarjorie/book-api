from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from sqlalchemy import Integer, String, Text, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

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
    rating: Mapped[str] = mapped_column(String(250),nullable=True)
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
    result = db.session.execute(db.select(Book).where(Book.id == book_id)).scalar_one_or_none()

    if result is None:
        return {"error": "Book not found"}, 404

    book = result.to_dict()

    return jsonify(book=book)

# def validate_book_data(dados, partial=False):
#     # validações... crio uma função separada para ser reaproveitada pelas rotas onde isso é necessário.

# POST  /books -> criar
@app.route("/books",methods=["POST"])
def create_book():
    dados = request.json # pegar o JSON que chegou do Bruno, já como dict python
    # return jsonify(dados)

    # Antes de modificar o book, verifico se o cliente enviou todos os campos obrigatórios no Model:
    if "title" in dados and "author" in dados and "genre" in dados:
        new_book = Book( # lado esquerdo: é o atributo/parâmetro da classe Cafe; lado direito é o dado que veio do Bruno.
            # Dados fornecidos pelo cliente:
            title=dados.get("title"), # acesso as chaves via .get() x ["chave"] -> com .get() se chave não existir => None, não KeyError.
            author=dados.get("author"),
            genre=dados.get("genre"),
            year=dados.get("year"),
            description=dados.get("description"),
            rating=dados.get("rating"),
            status=dados.get("status"),
            # Dados determinados pelo servidor:
            # owner_id=dados.get("owner_id")
            )

        db.session.add(new_book)
        db.session.commit()

        return jsonify(response={"success": "Book added successfully"}), 201

    return jsonify(response={"error": "Title, author and genre are mandatory fields"}), 400

# PUT    /books/<id> -> substituir / editar (ver se é o caso de manter)
@app.route("/books/<int:book_id>",methods=["PUT"])
def update_book(book_id):
    # Pego JSON que chegou do Bruno, já como dict python
    dados = request.json

    # Encontro no banco o book que tem esse id:
    book = db.get_or_404(Book,book_id)

    # Antes de modificar o book, verifico se o cliente enviou todos os campos obrigatórios no Model:
    if "title" in dados and "author" in dados and "genre" in dados:
        # Efetuo a modificação -> à esquerda, são os atributos do objeto Book que veio do banco, à direita, é o valor que o cliente enviou no JSON.
        book.title = dados.get("title")
        book.author = dados.get("author")
        book.genre = dados.get("genre")
        book.year = dados.get("year")
        book.description = dados.get("description")
        book.rating = dados.get("rating")
        book.status = dados.get("status")

        db.session.commit()

        return jsonify(response={"success": "Book edited successfully"}), 200

    return jsonify(response={"error": "Title, author and genre are mandatory fields"}), 400 # bad request

# PATCH /books/<id> -> editar parcialmente
@app.route("/books/<int:book_id>",methods=["PATCH"])
def partially_update_book(book_id):
    # Pego JSON que chegou do Bruno, já como dict python
    dados = request.json

    # Encontro no banco o book que tem esse id:
    book = db.get_or_404(Book, book_id)

    # Atualizo somente os campos enviados pelo cliente:
    if not dados:
        return jsonify(response={"error": "No fields provided for update"}), 400

    if "title" in dados: # "Se a chave existe, pegue o valor dela."
        book.title = dados["title"]
    if "author" in dados:
        book.author = dados["author"]
    if "genre" in dados:
        book.genre = dados["genre"]
    if "year" in dados:
        book.year = dados["year"]
    if "description" in dados:
        book.description = dados["description"]
    if "rating" in dados:
        book.rating = dados["rating"]
    if "status" in dados:
        book.status = dados["status"]

    db.session.commit()

    return jsonify(response={"success": "Book edited successfully"}), 200

# Depois, separadamente, podemos pensar na validação dos valores (year inteiro, rating válido etc.) e nos campos
# proibidos (id, owner_id). Não precisa enfiar tudo dentro desse código agora. NAS ROTAS ADD PUT E PATCH.


# DELETE /books/<id> -> apagar
@app.route("/books/<int:book_id>",methods=["DELETE"])
def delete_book(book_id):
    pass


# FILTROS:
# GET /books?genre=fantasy
# GET /books?status=read
# GET /books?author=tolkien
# GET /books?genre=fantasy&status=read


if __name__ == '__main__':
    app.run(debug=True,port=5001)