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
login_manager = LoginManager()
# login_manager.login_view = "login"
# login_manager.login_message = "Please log in to continue."
login_manager.init_app(app)

# FLASK-LOGIN USER LOADER CALLBACK:
# Flask-Login uses this function to reload the logged-in user from the database.
@login_manager.user_loader
def load_user(user_id):
    return  db.session.get(User, user_id)

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

    owner_id: Mapped[int] = mapped_column(ForeignKey("user_table.id"),nullable=False) # owner_id diz: "Esse Book pertence ao User cujo id é esse valor."
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
    user_data = request.json # recebe os dados do usuário

    # Verifica se os campos obrigatórios existem:
    if not "name" in user_data or not "email" in user_data or not "password" in user_data:
        return jsonify(response={"error": "Name, email and password are mandatory fields"}), 400

    # Verifica se eles são válidos:
    if not validate_user_data(user_data):
        return jsonify(response={"error": "Invalid user data"}), 400

    result = db.session.execute(db.select(User).where(User.email == user_data["email"]))
    user = result.scalar()

    if user:
        return jsonify(response={"error": "You've already signed up with that email, log in instead!"}), 409

    hash_and_salted_password = generate_password_hash(
        user_data["password"], # script e o padrao, sera que isso ta certo?
        salt_length=8
    )

    new_user = User(
        email=user_data["email"], # user_data["email"] não .get() porque ja verifico se os campos existem acima...
        name=user_data["name"],
        password=hash_and_salted_password,
    )

    db.session.add(new_user)
    db.session.commit()

    # This line will authenticate the user with Flask-Login
    login_user(new_user) # usa a sessão/cookie do Flask-Login. Isso funciona, mas quando chegares à parte de autenticação da API, vamos precisar decidir como queres que o cliente mantenha a autenticação.

    # Ao invés de enviar algo para o template, eu envio uma mensagem ao user:
    return jsonify(response={"success": "User logged in successfully"}), 201


# POST /auth/login
@app.route("/auth/login",methods=["POST"])
def login():
    user_data = request.json

    # Verifica se os campos obrigatórios existem: já os validei acima aqui não preciso.
    if not "email" in user_data or not "password" in user_data:
        return jsonify(response={"error": "Email and password are mandatory fields"}), 400

    result = db.session.execute(db.select(User).where(User.email == user_data["email"]))
    user = result.scalar()

    if not user:
        return jsonify(response={"error": "Unauthorized: wrong email or password."}), 401

    if not check_password_hash(user.password,user_data["password"]):
        return jsonify(response={"error": "Password incorrect, try again."}), 401

    login_user(user)
    return jsonify(response={"success": "User logged in successfully"}), 200

# POST /auth/logout
@app.route("/auth/logout",methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"success": "You've been logged out"}),200

# BOOKS - CRUD SIMPLES:
# GET    /books
@app.route("/books")
@login_required
def search_books(): # tentando juntar isso all books com o filtro by genre.
    books_genre = request.args.get("genre") # GET /books?genre=fantasy -> "Que tipo de livro?"
    books_status = request.args.get("status") # GET/books?status=read -> "Qual o status de leitura?"

    if not books_genre and not books_status: # se o cliente não enviar nem genre nem status: retorna todos os livros.
        result = db.session.execute(db.select(Book).where(Book.owner_id == current_user.id)).scalars().all()
        books = [book.to_dict() for book in result]
        return jsonify(books=books) # sem status explícito → Flask responde 200 OK por padrão.
    # Senão: crio uma query base que inicialmente seleciona todos os Books,
    # Os filtros serão adicionados abaixo somente quando o cliente realmente tiver enviado esses parâmetros.
    query = db.select(Book).where(Book.owner_id == current_user.id)

    if books_genre: # Só entra aqui se o cliente tiver enviado um parâmetro "genre".
        if books_genre not in ALLOWED_GENRES: # Enviou gênero mas não é um gênero válido?
            return jsonify(error={"Bad request": "Sorry, genre not allowed."}), 400 # Nesse caso, a requisição é inválida e não precisamos consultar o banco.
        else: # O gênero é válido, então adicionamos uma condição à query.
            query = query.where(Book.genre == books_genre)

    if books_status: # Só entra aqui se o cliente tiver enviado um parâmetro "status"
        if books_status not in ALLOWED_STATUS: # O cliente enviou um status, mas esse valor não é permitido
            return jsonify(error={"Bad request": "Sorry, status not allowed."}), 400 # Os if ... in ALLOWED_* realmente verificam se o valor é válido. O que eles não fazem automaticamente é retornar um erro quando é inválido.
        else: # O status é válido, então adicionamos outra condição à query.
            query = query.where(Book.status == books_status)
    # Se genre também tiver sido enviado, teremos dois filtros.
    # Só agora executamos a query que construímos acima:
    result = db.session.execute(query).scalars().all() # é aqui, na execução da query, que eu coloco scalars().all(), não antes, na query.
    books = [book.to_dict() for book in result] # Converte os objetos Book retornados pelo banco em dicionários
                                                # antes de enviá-los na resposta JSON.

    return jsonify(books=books) # Retorna os livros encontrados.
    # # Se a query não encontrar nenhum livro, "books" será uma lista vazia:
    #     # {"books": []}
    #     return jsonify(books=books)

# GET    /books/<id>
@app.route("/books/<int:book_id>")
@login_required
def one_book(book_id):
    result = db.session.execute(db.select(Book).where(Book.id == book_id, Book.owner_id == current_user.id)).scalar_one_or_none()
    if result is None:
        return jsonify({"error": "Book not found"}), 404
    # o livro não existe → None → 404;
    # o livro existe, mas é de outro usuário → a query também retorna None → 404.
    # E isso combina com a decisão que você acabou de tomar de não revelar a existência de livros de outros usuários.

    book = result.to_dict()

    return jsonify(book=book)

# POST  /books -> criar
@app.route("/books",methods=["POST"])
@login_required
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
        owner_id=current_user.id # O owner_id deste Book será o ID do usuário que está fazendo esta requisição.
        )

    db.session.add(new_book)
    db.session.commit()

    return jsonify(response={"success": "Book added successfully"}), 201

# PATCH /books/<id> -> editar parcialmente
@app.route("/books/<int:book_id>",methods=["PATCH"])
@login_required
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
    book = db.session.execute(db.select(Book).where(Book.id == book_id,Book.owner_id == current_user.id)).scalar_one_or_none()

    if book is None:
        return jsonify({"error": "Book not found"}), 404

    # Atualizo somente os campos enviados pelo cliente:
    for field in ALLOWED_BOOK_FIELDS:
        if field in data:
            setattr(book,field,data[field])

    db.session.commit()

    return jsonify(response={"success": "Book edited successfully"}), 200

# DELETE /books/<id> -> apagar
@app.route("/books/<int:book_id>",methods=["DELETE"])
@login_required
def delete_book(book_id):
    # Encontro o livro a ser deletado usando o book_id (primary key):
    book = db.session.execute(db.select(Book).where(Book.id == book_id, Book.owner_id == current_user.id)).scalar_one_or_none()

    if book is None:
        return jsonify({"error": "Book not found"}), 404

    # Digo ao banco: "quero que esse objeto seja removido da sessão":
    db.session.delete(book)
    db.session.commit()

    return jsonify(response={"success": "Book successfully deleted"}), 200


if __name__ == '__main__':
    app.run(debug=True,port=5001)