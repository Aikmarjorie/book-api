from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from sqlalchemy import Integer, String, Text, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import random

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

# Constante - API KEY (idealmente em env.var, mas aqui, ok só para fixar conceito) -> serve para a rota report-closed (DELETE)
API_KEY="TopSecretAPIKey"

# CREATE MODELS
class Book(db.Model):
    __tablename__ = "book_table"

    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    title: Mapped[str] = mapped_column(String(500),nullable=False) # essa coluna não pode receber Null, portanto, campo obrigatório
    author: Mapped[str] = mapped_column(String(250),nullable=False)
    genre: Mapped[str] = mapped_column(String(250),nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text,nullable=True)

    # owner_id:
    # rating:
    # status:

    # # tables + to_dict method ??

class User(UserMixin,db.Model):
    __tablename__ = "user_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(225), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(500),nullable=False)
    

# with app.app_context():
#     db.create_all()

# CREATE ROUTES / endpoints
# AUTHENTICATION:
# POST /auth/register
# POST /auth/login
# POST /auth/logout
#
# BOOKS:
@app.route("/books")
def all_books():
    result = db.session.execute(db.select(Book))
    books = result.scalars().all()
    
    return jsonify(books=books) # preciso converter essa lista de objetos em dict - json

# GET    /books
# GET    /books/<id>
# POST   /books
# PUT    /books/<id>
# DELETE /books/<id>
#
# Filtros
# Por exemplo:
# GET /books?genre=fantasy
# GET /books?status=read
# GET /books?author=tolkien
#
# E talvez:
# GET /books?genre=fantasy&status=read


if __name__ == '__main__':
    app.run(debug=True,port=5001)