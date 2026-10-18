import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, Task, STATUS_ORDER, STATUS_EDITAVEIS, STATUS_CSS, PRIORITY_CSS, PRIORIDADES, PENDENTE
import re
from sqlalchemy import or_


BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Cria banco em team_task_manager/instance/database.db
app = Flask(__name__, instance_path=os.path.join(BASE_DIR, 'instance'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'senha1234')  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


# Direciona pro login se não estiver logado
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Faça login para acessar essa página.'
login_manager.login_message_category = 'warning'

# --------------Carrega usuários------------------
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

#============================== PERMISSOES ===============================
    
def can_edit(task):
    #Pode editar: quem criou, o responsável ou um admin.
    return (current_user.role == 'admin'
            or task.created_by == current_user.id
            or task.assigned_to == current_user.id)


def can_delete(task):
    #Pode excluir: quem criou ou um admin.
    return current_user.role == 'admin' or task.created_by == current_user.id

def can_delete_user(target):
    #Admin exclui qualquer conta; cada usuário pode excluir a própria.
    return current_user.role == 'admin' or current_user.id == target.id

@app.context_processor
def inject_globals():
    return dict(
        STATUS_ORDER=STATUS_ORDER,
        STATUS_EDITAVEIS=STATUS_EDITAVEIS,
        STATUS_CSS=STATUS_CSS,
        PRIORITY_CSS=PRIORITY_CSS,
        PRIORIDADES=PRIORIDADES,
        can_edit=can_edit,
        can_delete=can_delete,
        can_delete_user=can_delete_user
    )

#======================= ROTAS =================================

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

#---------------ver contatos------------------------
@app.route('/contatos')
@login_required
def contatos():
    return render_template('contatos.html', users=all_users())

#-----------------------login----------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))

        flash('Credenciais inválidas', 'danger')

    return render_template('login.html')

#-------------formatar telefone pra guardar no banco -----------------
def normalize_phone(raw):
    """Devolve só os dígitos (DDD + número) se for válido, senão None."""
    digits = re.sub(r'\D', '', raw or '')
    if digits.startswith('55') and len(digits) in (12, 13):  # aceita +55
        digits = digits[2:]
    if re.fullmatch(r'[1-9]{2}(9\d{8}|[2-5]\d{7})', digits):
        return digits
    return None


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = generate_password_hash(request.form['password'])
        phone = normalize_phone(request.form.get('phone'))
        role = request.form.get('role', 'member')

        if phone is None:
            flash('Telefone inválido! Informe DDD e número.', 'danger')
            return redirect(url_for('register'))

        if not username:
            flash('Informe um nome de usuário!', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe!', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, password=password, role=role, telefone=phone)
        db.session.add(new_user)
        db.session.commit()
        flash('Registrou com sucesso!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

#-------------------------formatar telefone na hora de exibir ----------------------
@app.template_filter('telefone')
def format_phone(d):
    if not d:
        return ''
    if len(d) == 11:
        return f'({d[:2]}) {d[2:7]}-{d[7:]}'
    return f'({d[:2]}) {d[2:6]}-{d[6:]}'

@app.route('/logout')
@login_required  # só quem está logado pode usar
def logout():
    logout_user()  # apaga a sessão do usuário atual
    flash('Você saiu da conta.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.order_by(Task.deadline.asc(), Task.id.asc()).all()
    users = User.query.all()

    # O próprio usuário aparece primeiro, depois os outros em ordem alfabética
    users.sort(key=lambda u: (u.id != current_user.id, u.username.lower()))

    board = []
    for user in users:
        columns = {status: [] for status in STATUS_ORDER}
        for task in tasks:  # `tasks` já está ordenada por prazo
            if task.assigned_to == user.id:
                columns[task.effective_status].append(task)

        total = sum(len(lista) for lista in columns.values())
        if total:  # só mostra quem tem tarefa
            board.append({'user': user, 'columns': columns, 'total': total})

    return render_template('dashboard.html', board=board)

#------------------------ler data----------------------
def parse_date(texto):
    try:
        return datetime.strptime(texto, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

#------------------------ler formulario----------------------
def read_task_form(form):
    """Lê e valida o formulário. Retorna (valores, prazo, mensagem_de_erro)."""
    values = {campo: form.get(campo, '').strip() for campo in
              ('title', 'description', 'deadline', 'priority', 'status', 'assigned_to')}
    deadline = parse_date(values['deadline'])

    error = None
    if not values['title']:
        error = 'O título da tarefa é obrigatório!'
    elif not values['description']:
        error = 'A descrição é obrigatória!'
    elif deadline is None:
        error = 'Informe um prazo válido!'
    elif values['priority'] not in PRIORIDADES:
        error = 'Prioridade inválida!'
    elif values['status'] not in STATUS_EDITAVEIS:
        error = 'Status inválido!'
    elif not values['assigned_to'].isdigit() or db.session.get(User, int(values['assigned_to'])) is None:
        error = 'Escolha um responsável válido!'

    return values, deadline, error

#-----------------------listar usuarios----------------------
def all_users():
    return User.query.order_by(User.username).all()

#-----------------------adicionar tarefa----------------------
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_task():
    values = {'title': '', 'description': '', 'deadline': '', 'priority': 'Média',
              'status': PENDENTE, 'assigned_to': str(current_user.id)}

    if request.method == 'POST':
        values, deadline, error = read_task_form(request.form)
        if error:
            flash(error, 'danger')
        else:
            new_task = Task(
                title=values['title'],
                description=values['description'],
                deadline=deadline,
                priority=values['priority'],
                status=values['status'],
                created_by=current_user.id,
                assigned_to=int(values['assigned_to']),
            )
            db.session.add(new_task)
            db.session.commit()
            flash('Tarefa adicionada!', 'success')
            return redirect(url_for('dashboard'))

    return render_template('add_task.html', values=values, users=all_users())

#-----------------------visualizar tarefa----------------------
@app.route('/task/<int:task_id>')
@login_required
def view_task(task_id):
    """Devolve só o conteúdo do modal (task.html), carregado via fetch no painel."""
    task = db.get_or_404(Task, task_id)
    creator = db.session.get(User, task.created_by)
    return render_template('task.html', task=task, creator=creator)

#-----------------------editar tarefa----------------------
@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = db.get_or_404(Task, task_id)

    if not can_edit(task):
        flash('Acesso negado', 'danger')
        return redirect(url_for('dashboard'))

    values = {'title': task.title, 'description': task.description,
              'deadline': task.deadline.isoformat(), 'priority': task.priority,
              'status': task.status, 'assigned_to': str(task.assigned_to)}

    if request.method == 'POST':
        values, deadline, error = read_task_form(request.form)
        if error:
            flash(error, 'danger')
        else:
            task.title = values['title']
            task.description = values['description']
            task.deadline = deadline
            task.priority = values['priority']
            task.status = values['status']
            task.assigned_to = int(values['assigned_to'])
            db.session.commit()
            flash('Tarefa atualizada!', 'success')
            return redirect(url_for('dashboard'))

    return render_template('edit_task.html', task=task, values=values, users=all_users())

#-----------------------deletar tarefa----------------------
@app.route('/delete/<int:task_id>', methods=['GET', 'POST'])
@login_required
def delete_task(task_id):
    task = db.get_or_404(Task, task_id)

    if not can_delete(task):
        flash('Acesso negado', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        db.session.delete(task)
        db.session.commit()
        flash('Tarefa deletada!', 'success')
        return redirect(url_for('dashboard'))

    # GET: mostra a tela de confirmação (delete.html)
    return render_template('delete.html', task=task)

#-----------------------deletar usuario----------------------

@app.route('/user/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
    target = db.get_or_404(User, user_id)

    if not can_delete_user(target):
        flash('Acesso negado', 'danger')
        return redirect(url_for('dashboard'))

    # nunca deixar o sistema sem nenhum administrador
    if target.role == 'admin' and User.query.filter_by(role='admin').count() <= 1:
        flash('Não é possível excluir o único administrador.', 'danger')
        return redirect(url_for('dashboard'))

    is_self = target.id == current_user.id

    if request.method == 'POST':
        username = target.username
        if is_self:
            logout_user()  # encerra a sessão antes de apagar a conta
        remove_user(target)
        if is_self:
            flash('Sua conta foi excluída.', 'success')
            return redirect(url_for('login'))
        flash(f'Usuário {username} excluído.', 'success')
        return redirect(url_for('contatos'))

    n_tasks = tasks_of(target).count()
    return render_template('delete_user.html', target=target, is_self=is_self, n_tasks=n_tasks)

#------------------- tarefas do usuário -----------------------

def tasks_of(user):
    #Tarefas criadas por ele ou atribuídas a ele.
    return Task.query.filter(or_(Task.created_by == user.id, Task.assigned_to == user.id))

def remove_user(user):
    #Apaga o usuário e todas as tarefas que ele criou ou que foram atribuídas a ele.
    tasks_of(user).delete(synchronize_session=False)
    db.session.expire_all()
    db.session.delete(user)
    db.session.commit()


#========================= RODAR APP ========================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5005)