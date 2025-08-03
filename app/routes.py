from flask import render_template, request, redirect, url_for, Blueprint, flash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from . import db, bcrypt
from .models import User, Student, Fee

# Define the blueprint for the main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Your dashboard logic here
    return render_template('dashboard.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# Add a route to create a new user for testing
@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'warning')
            return redirect(url_for('main.register'))

        # Create a new user with a hashed password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password_hash=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('main.login'))
        
    return render_template('register.html')

# Add a placeholder for a route that uses the database
@main_bp.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        new_student = Student(name=name)
        db.session.add(new_student)
        db.session.commit()
        flash('Student added successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('add_student.html')

@main_bp.route('/fees')
@login_required
def fees_records():
    # You must update this route's logic to use the new models
    # This is a placeholder to show how to retrieve data
    fees = Fee.query.order_by(Fee.date.desc()).all()
    return render_template('fees_records.html', fees=fees)
