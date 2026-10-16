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

# Rota Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username = username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin_dashboard' if user.role == 'admin' else 'dashboard'))

        flash('Credenciais inválidas', 'danger')

    return render_template('login.html')

# Rota Logout

@app.route('/logout')      
@login_required # só quem está logado pode usar
def logout():
    logout_user() # apaga a sessão do usuário atual
    flash('Você saiu da conta.', 'success')  # mensagem que aparece na próxima tela
    return redirect(url_for('login')) # manda o usuário de volta pra tela de login

# Rota padrão

@app.route('/')
def home():
    return redirect(url_for('login'))

# Registro

@app.route('/register', methods= ['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form.get('role', 'member')
        if User.query.filter_by(username = username).first(): 
            flash('Nome de usuário já existe!', 'danger')
            return redirect(url_for('register'))

        new_user = User(username = username, password = password, role = role )
        db.session.add(new_user)
        db.session.commit()
        flash ('Registrou com sucesso!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Dashboards

@app.route('/dashboard') 
@login_required
def dashboard():
    my_tasks = Task.query.filter_by(created_by = current_user.id).all()
    shared_tasks = Task.query.filter_by(shared_with = current_user.id).all()
    return render_template('dashboard.html', my_tasks = my_tasks, shared_tasks = shared_tasks)

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Acesso negado', 'danger')
        return redirect(url_for('dashboard'))
        tasks = Task.query.all()
        return render_template('admin_dashboard.html', tasks = tasks)

# Rota adicionar    

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        title = request.form['title'].strip()
        description = request.form['description'].strip()
        priority = request.form.get('priority', 'Baixa')

        if not title:
            flash('O nome da tarefa é obrigatório!', 'danger')
            return redirect(url_for('add_task'))

        new_task = Task(title = title, description = description, priority = priority, created_by = current_user.id)

        db.session.add(new_task)
        db.session.commit()

        flash('Task adicionada!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_task.html')    

# Rota editar tarefa

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):

    task = Task.query.get_or_404(task_id)

    if task.created_by != current_user.id and current_user.role != 'admin':
        flash('Acesso negado', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form['title'].strip()
        
        if not title:
            flash('Preencha todos os campos!', 'danger')
            return redirect(url_for('edit_task', task_id = task.id))

        task.title = title
        task.priority = request.form.get('priority', task.priority)
        task.status = request.form.get('status', task.status)
        db.session.commit()
        flash('Tarefa atualizada!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_task.html', task = task)

# Rota deletar tarefa

@app.route('/delete/<int:task_id>', methods=['GET', 'POST'])
@login_required
def delete_task(task_id):
    
    task = Task.query.get_or_404(task_id)

    if task.created_by != current_user.id and current_user.role != 'admin':
        flash('Acesso negado', 'danger')
        return redirect(url_for('dashboard'))

    db.session.delete(task)
    db.session.commit()
    flash('Tarefa deletada!', 'success')
    return redirect(url_for('dashboard'))