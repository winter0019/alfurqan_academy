import os
import secrets
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import UserMixin, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize extensions outside of the factory function
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# --- Application Factory Function ---
def create_app():
    app = Flask(__name__)

    # --- Configuration ---
    # The SECRET_KEY is essential for CSRF protection and session management
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    
    # Configure the database connection for Render or local development
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with the application
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register Jinja2 filter
    app.jinja_env.filters['format_currency'] = format_currency_filter

    # --- Routes ---
    # This is a temporary route to create the first admin user.
    # It must be removed after the admin user is created.
    @app.route('/create_first_admin')
    def create_first_admin():
        try:
            existing_user = User.query.filter_by(username='admin').first()
            if existing_user:
                flash('Admin user already exists. You can log in.', 'info')
                return redirect(url_for('login'))

            hashed_password = generate_password_hash('admin')
            first_admin = User(username='admin', password=hashed_password, role='admin')
            db.session.add(first_admin)
            db.session.commit()
            
            flash('First admin user created successfully. You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('login'))

    @app.route('/')
    @login_required
    def index():
        students = Student.query.order_by(Student.admission_date.desc()).limit(5).all()
        current_academic_year, current_term = get_current_school_period()
        students_with_status = []
        for student in students:
            student.fee_status = get_fee_status(student.reg_number, current_academic_year, current_term)
            students_with_status.append(student)

        return render_template('index.html', students=students_with_status)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'error')
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists. Please choose a different one.', 'error')
            else:
                hashed_password = generate_password_hash(password)
                new_user = User(username=username, password=hashed_password, role='user')
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful! You can now log in.', 'success')
                return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))
    
    # ... (other routes from your original code need to be adapted) ...

    return app

# --- Helper functions and Data ---
FEE_STRUCTURE = {
    ('Nur. 1', 'First Term'): 50000.00,
    ('Nur. 1', 'Second Term'): 45000.00,
    ('Nur. 1', 'Third Term'): 40000.00,
    # ... (rest of your FEE_STRUCTURE) ...
}

def get_current_school_period():
    current_year = datetime.now().year
    if datetime.now().month < 8:
        academic_year = f"{current_year - 1}/{current_year}"
    else:
        academic_year = f"{current_year}/{current_year + 1}"
    current_month = datetime.now().month
    if 9 <= current_month <= 12:
        current_term = "First Term"
    elif 1 <= current_month <= 4:
        current_term = "Second Term"
    else:
        current_term = "Third Term"
    return academic_year, current_term

def get_fee_status(student_reg_number, academic_year_check, term_check):
    student = Student.query.filter_by(reg_number=student_reg_number).first()
    if not student:
        return 'N/A'
    
    expected_fee = FEE_STRUCTURE.get((student.student_class, term_check), 0.0)
    total_paid = db.session.query(db.func.sum(Payment.amount_paid)).filter(
        Payment.student_reg_number == student_reg_number,
        Payment.term == term_check,
        Payment.academic_year == academic_year_check
    ).scalar() or 0.0
    
    if expected_fee > 0:
        if total_paid >= expected_fee:
            return 'Paid'
        else:
            return 'Defaulter'
    else:
        return 'N/A'

def format_currency_filter(value):
    try:
        return "{:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return value

# --- Database Models ---
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20))

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    reg_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    dob = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    student_class = db.Column(db.String(50))
    term = db.Column(db.String(50))
    academic_year = db.Column(db.String(20))
    admission_date = db.Column(db.String(20))

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    student_reg_number = db.Column(db.String(50), db.ForeignKey('students.reg_number'), nullable=False)
    term = db.Column(db.String(50))
    academic_year = db.Column(db.String(20))
    amount_paid = db.Column(db.Float)
    payment_date = db.Column(db.String(20))
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
