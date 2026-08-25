from flask import Flask, abort, jsonify, render_template, request, redirect, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect, text
from datetime import datetime, timedelta
import os

app = Flask(__name__, static_folder=None)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nihon-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@app.route('/static/<path:filename>')
def static(filename):
    if filename not in {'style.css', 'script.js'}:
        abort(404)
    return send_from_directory(app.root_path, filename)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    category = db.Column(db.String(50))
    minutes = db.Column(db.Integer)
    title = db.Column(db.String(150), nullable=False, default='Study session')
    score = db.Column(db.Integer, nullable=False, default=0)
    notes = db.Column(db.Text, nullable=False, default='')

class StudyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    focus = db.Column(db.String(100), nullable=False)
    task = db.Column(db.String(300), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    is_done = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not email or len(password) < 6:
            return 'Enter a valid email and a password of at least 6 characters', 400
        if User.query.filter_by(email=email).first():
            return "User already exists, go to login"
        hashed = generate_password_hash(password)
        new_user = User(email=email, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, request.form.get('password', '')):
            login_user(user)
            return redirect(url_for('home'))
        return "Wrong email or password"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    todos = Todo.query.filter_by(user_id=current_user.id).order_by(Todo.created_at.desc()).all()
    return render_template('index.html', stats=build_dashboard(), todos=todos)

@app.route('/todo/add', methods=['POST'])
@login_required
def add_todo():
    title = request.form.get('title', '').strip()
    if not title:
        return 'A todo title is required', 400
    db.session.add(Todo(user_id=current_user.id, title=title))
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/todo/toggle/<int:todo_id>')
@login_required
def toggle_todo(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()
    todo.is_done = not todo.is_done
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/todo/delete/<int:todo_id>')
@login_required
def delete_todo(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/history')
@login_required
def history():
    sessions = (StudySession.query.filter_by(user_id=current_user.id)
                .order_by(StudySession.date.desc(), StudySession.id.desc()).all())
    todos = (Todo.query.filter_by(user_id=current_user.id)
             .order_by(Todo.created_at.desc()).all())
    return render_template('history.html', sessions=sessions, todos=todos)

def build_dashboard():
    today = datetime.utcnow().date()
    sessions = (StudySession.query.filter_by(user_id=current_user.id)
                .order_by(StudySession.date.desc(), StudySession.id.desc()).all())
    plans = StudyPlan.query.filter_by(user_id=current_user.id).order_by(StudyPlan.id).all()
    totals = {category: 0 for category in ('grammar', 'vocabulary', 'kanji', 'dokkai')}
    for session in sessions:
        if session.category in totals:
            totals[session.category] += session.minutes or 0

    def activity(days):
        return [
            {'date': (today - timedelta(days=offset)).isoformat(),
             'label': (today - timedelta(days=offset)).strftime('%a'),
             'minutes': sum((item.minutes or 0) for item in sessions
                            if item.date == today - timedelta(days=offset))}
            for offset in range(days - 1, -1, -1)
        ]

    weekly = activity(7)
    monthly = activity(30)
    top_category = max(totals, key=totals.get) if any(totals.values()) else 'vocabulary'
    completion = round(sum(plan.completed for plan in plans) / len(plans) * 100) if plans else 0
    return {
        'streak': len({session.date for session in sessions}),
        'category_totals': totals,
        'total_minutes': sum((session.minutes or 0) for session in sessions),
        'total_sessions': len(sessions),
        'completion_percent': completion,
        'top_category': top_category,
        'weekly_activity': weekly,
        'monthly_activity': monthly,
        'plans': plans,
        'sessions': sessions[:10],
    }

@app.route('/api/dashboard')
@login_required
def dashboard_api():
    dashboard = build_dashboard()
    dashboard.pop('plans', None)
    dashboard.pop('sessions', None)
    return jsonify(dashboard)

@app.route('/add_session', methods=['POST'])
@login_required
def add_session():
    try:
        minutes = int(request.form.get('minutes', 0))
        score = int(request.form.get('score', 0))
    except ValueError:
        return 'Minutes and score must be numbers', 400
    category = request.form.get('category', '').strip().lower()
    if category not in {'grammar', 'vocabulary', 'kanji', 'dokkai'} or minutes < 1 or not 0 <= score <= 100:
        return 'Invalid study session values', 400
    db.session.add(StudySession(user_id=current_user.id, date=datetime.utcnow().date(),
                                category=category, minutes=minutes,
                                title=request.form.get('title', '').strip() or 'Study session',
                                score=score, notes=request.form.get('notes', '').strip()))
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/save_plan', methods=['POST'])
@login_required
def save_plan():
    focus = request.form.get('focus', '').strip() or 'Japanese'
    task = request.form.get('task', '').strip()
    if not task:
        return 'A plan task is required', 400
    db.session.add(StudyPlan(user_id=current_user.id, focus=focus, task=task))
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/toggle_plan/<int:plan_id>', methods=['POST'])
@login_required
def toggle_plan(plan_id):
    plan = StudyPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    plan.completed = not plan.completed
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/reset', methods=['POST'])
@login_required
def reset_data():
    StudySession.query.filter_by(user_id=current_user.id).delete()
    StudyPlan.query.filter_by(user_id=current_user.id).delete()
    Todo.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return redirect(url_for('home'))

with app.app_context():
    db.create_all()
    session_columns = {column['name'] for column in inspect(db.engine).get_columns('study_session')}
    migrations = {
        'title': "ALTER TABLE study_session ADD COLUMN title VARCHAR(150) NOT NULL DEFAULT 'Study session'",
        'score': 'ALTER TABLE study_session ADD COLUMN score INTEGER NOT NULL DEFAULT 0',
        'notes': "ALTER TABLE study_session ADD COLUMN notes TEXT NOT NULL DEFAULT ''",
    }
    for column, statement in migrations.items():
        if column not in session_columns:
            db.session.execute(text(statement))
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)