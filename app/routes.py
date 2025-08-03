from flask import render_template, redirect, url_for, flash, request, Blueprint
from . import db, bcrypt
from .forms import LoginForm, CreateUserForm
from .models import User
from flask_login import login_user, logout_user, login_required, current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/create_first_admin')
def create_first_admin():
    try:
        # Check if an admin user already exists to prevent misuse
        existing_user = User.query.filter_by(username='admin').first()
        if existing_user:
            flash('Admin user already exists. You can log in.', 'info')
            return redirect(url_for('main.login'))

        # Hash the password for the new admin user
        hashed_password = bcrypt.generate_password_hash('admin').decode('utf-8')
        
        # Create the new user object
        first_admin = User(username='admin', password=hashed_password, role='admin')
        
        # Add to the database
        db.session.add(first_admin)
        db.session.commit()
        
        flash('First admin user created successfully. You can now log in.', 'success')
        return redirect(url_for('main.login'))
        
    except Exception as e:
        # Catch any errors and provide a specific flash message
        db.session.rollback()
        flash(f'An error occurred while creating the admin user: {str(e)}', 'danger')
        return redirect(url_for('main.login'))

@main_bp.route('/', methods=['GET', 'POST'])
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
            
    return render_template('login.html', form=form)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('main.login'))

@main_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    return render_template('register.html')

@main_bp.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    return render_template('add_student.html')

@main_bp.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'warning')
            return render_template('create_user.html', form=form)
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(
            username=form.username.data,
            password=hashed_password,
            role=form.role.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash('New user created successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('create_user.html', form=form)
