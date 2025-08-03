from flask import render_template, redirect, url_for, flash, request, Blueprint
from . import db, bcrypt
from .forms import LoginForm
from .models import User
from flask_login import login_user, logout_user, login_required, current_user

main_bp = Blueprint('main', __name__)

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
