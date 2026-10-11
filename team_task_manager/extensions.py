from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


# Ativem o ambiente virtual usando esses comandos
# primeiro comando: "python -m venv venv"(sim, é venv duas vezes)
# segundo comando: "venv\\Scripts\\activate" (se tiver no Windows), ou "source venv/bin/activate" (se tiver no Linux ou Mac)
#Depois rodem esse comando pra instalar o flask: "pip install flask-login"