from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, Task

app = Flask(__name__)
app.config['SECRET_KEY'] = 'senha1234'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Direciona pro login se não estiver logado
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Carrega usuários
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

