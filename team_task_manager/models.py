from extensions import db
from flask_login import UserMixin
from datetime import date, datetime, timezone



PENDENTE = 'Pendente'
EM_ANDAMENTO = 'Em andamento'
CONCLUIDA = 'Concluída'
ATRASADA = 'Atrasada'

#ordem status
STATUS_ORDER = [PENDENTE, EM_ANDAMENTO, CONCLUIDA, ATRASADA]

#status selecionaveis
STATUS_EDITAVEIS = [PENDENTE, EM_ANDAMENTO, CONCLUIDA]

# classes bolinhas
STATUS_CSS = {
    PENDENTE: 'dot-pendente',
    EM_ANDAMENTO: 'dot-andamento',
    CONCLUIDA: 'dot-concluida',
    ATRASADA: 'dot-atrasada',
}


PRIORIDADES = ['Baixa', 'Média', 'Alta']

#---------------------------------Usuario----------------------------------------------

class User(db.Model, UserMixin): # Define a classe usuário
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(150), unique = True, nullable= False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(10), default = 'membro') # Administrador ou membro

#---------------------------------Tarefa----------------------------------------------

class Task(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(200), nullable = False)
    description = db.Column(db.Text, nullable = False)
    deadline = db.Column(db.Date, nullable=False)  # prazo
    status = db.Column(db.String(20), default = PENDENTE)
    priority = db.Column(db.String(20), default = 'Baixa')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_tasks')

@property
def effective_status(self):
    if self.status != CONCLUIDA and self.deadline < date.today():
       return ATRASADA
    return self.status