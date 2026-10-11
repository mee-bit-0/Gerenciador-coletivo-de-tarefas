from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


# Ativem o ambiente virtual usando esses comandos
# primeiro comando: "python -m venv venv"(sim, é venv duas vezes)
# segundo comando: "venv\\Scripts\\activate" (se tiver no Windows), ou "source venv/bin/activate" (se tiver no Linux ou Mac)
# Depois, no VSCode, apertem Ctrl + Shift + P e digitem Python: Select Interpreter e selecionem o que tá escrito "venv" no caminho
# No final rodem esse comando pra instalar o flask: "pip install flask flask-login flask-sqlalchemy"
