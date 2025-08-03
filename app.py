import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, g, session, abort
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash # Using Werkzeug's hash functions for consistency
import secrets
from functools import wraps

app = Flask(__name__)
# Generate a strong, random secret key for session management and security
# IMPORTANT: Never share this key publicly.
app.secret_key = secrets.token_hex(32)

# Initialize extensions
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)

DATABASE = 'alfurqan_academy.db'

# Define a simple fee structure for demonstration purposes.
# You will need to expand this significantly for your full school's fee structure.
FEE_STRUCTURE = {
    ('Nur. 1', 'First Term'): 50000.00,
    ('Nur. 1', 'Second Term'): 45000.00,
    ('Nur. 1', 'Third Term'): 40000.00,
    ('Nur. 2', 'First Term'): 52000.00,
    ('Nur. 2', 'Second Term'): 47000.00,
    ('Nur. 2', 'Third Term'): 42000.00,
    ('Nur. 3', 'First Term'): 55000.00,
    ('Nur. 3', 'Second Term'): 50000.00,
    ('Nur. 3', 'Third Term'): 45000.00,
    ('Basic 1', 'First Term'): 60000.00,
    ('Basic 1', 'Second Term'): 55000.00,
    ('Basic 1', 'Third Term'): 50000.00,
    ('Basic 2', 'First Term'): 62000.00,
    ('Basic 2', 'Second Term'): 57000.00,
    ('Basic 2', 'Third Term'): 52000.00,
    ('Basic 3', 'First Term'): 65000.00,
    ('Basic 3', 'Second Term'): 60000.00,
    ('Basic 3', 'Third Term'): 55000.00,
    ('JSS 1', 'First Term'): 70000.00,
    ('JSS 1', 'Second Term'): 65000.00,
    ('JSS 1', 'Third Term'): 60000.00,
    ('JSS 2', 'First Term'): 72000.00,
    ('JSS 2', 'Second Term'): 67000.00,
    ('JSS 2', 'Third Term'): 62000.00,
    ('JSS 3', 'First Term'): 75000.00,
    ('JSS 3', 'Second Term'): 70000.00,
    ('JSS 3', 'Third Term'): 65000.00,
    ('SS 1', 'First Term'): 80000.00,
    ('SS 1', 'Second Term'): 75000.00,
    ('SS 1', 'Third Term'): 70000.00,
    ('SS 2', 'First Term'): 82000.00,
    ('SS 2', 'Second Term'): 77000.00,
    ('SS 2', 'Third Term'): 72000.00,
    ('SS 3', 'First Term'): 85000.00,
    ('SS 3', 'Second Term'): 80000.00,
    ('SS 3', 'Third Term'): 75000.00,
}

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', 'r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Decorators for authentication and role-based access control
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            abort(403) # Forbidden
        return f(*args, **kwargs)
    return decorated_function

# Helper function to get the current academic year and term
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

# Helper function to calculate fee status for a given student, academic year, and term
def get_fee_status(student_reg_number, academic_year_check, term_check):
    db = get_db()
    student = db.execute('SELECT class FROM students WHERE reg_number = ?', (student_reg_number,)).fetchone()
    if not student:
        return 'N/A'

    student_class = student['class']
    expected_fee = FEE_STRUCTURE.get((student_class, term_check), 0.0)

    total_paid_for_period = db.execute(
        'SELECT SUM(amount_paid) FROM payments WHERE student_reg_number = ? AND term = ? AND academic_year = ?',
        (student_reg_number, term_check, academic_year_check)
    ).fetchone()[0] or 0.0

    if expected_fee > 0:
        if total_paid_for_period >= expected_fee:
            return 'Paid'
        else:
            return 'Defaulter'
    else:
        return 'N/A'

# Custom Jinja2 filter for currency formatting
def format_currency_filter(value):
    try:
        return "{:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return value

app.jinja_env.filters['format_currency'] = format_currency_filter

# ROUTES
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    students_data = db.execute('SELECT * FROM students ORDER BY admission_date DESC LIMIT 5').fetchall()
    current_academic_year, current_term = get_current_school_period()
    students_with_status = []
    for student in students_data:
        student_dict = dict(student)
        student_dict['fee_status'] = get_fee_status(student['reg_number'], current_academic_year, current_term)
        students_with_status.append(student_dict)

    return render_template('index.html', students=students_with_status)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
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
        db = get_db()
        existing_user = db.execute('SELECT 1 FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
        else:
            hashed_password = generate_password_hash(password)
            db.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, hashed_password, 'user'))
            db.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/register_student', methods=('GET', 'POST'))
@login_required
@admin_required
def register_student():
    if request.method == 'POST':
        reg_number = request.form['reg_number'].strip()
        name = request.form['name'].strip()
        dob = request.form['dob'].strip()
        gender = request.form['gender'].strip()
        address = request.form['address'].strip()
        phone = request.form['phone'].strip()
        email = request.form['email'].strip()
        student_class = request.form['class'].strip()
        term = request.form['term'].strip()
        academic_year = request.form['academic_year'].strip()
        admission_date = datetime.now().strftime('%Y-%m-%d')

        db = get_db()
        existing_student = db.execute('SELECT 1 FROM students WHERE reg_number = ?', (reg_number,)).fetchone()
        if existing_student:
            flash(f'Error: Student with Registration Number {reg_number} already exists.', 'error')
        else:
            try:
                db.execute(
                    'INSERT INTO students (reg_number, name, dob, gender, address, phone, email, class, term, academic_year, admission_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (reg_number, name, dob, gender, address, phone, email, student_class, term, academic_year, admission_date)
                )
                db.commit()
                flash(f'Student {name} registered successfully!', 'success')
                return redirect(url_for('student_details', reg_number=reg_number))
            except sqlite3.Error as e:
                flash(f'Database error: {e}', 'error')

    classes = sorted(list(set(item[0] for item in FEE_STRUCTURE.keys())))
    terms = sorted(list(set(item[1] for item in FEE_STRUCTURE.keys())))
    current_year_val = datetime.now().year
    academic_years = [f"{y}/{y+1}" for y in range(current_year_val - 2, current_year_val + 3)]

    return render_template('register_student.html', classes=classes, terms=terms, academic_years=academic_years)

@app.route('/students')
@login_required
def student_list():
    db = get_db()
    status_filter = request.args.get('status', 'all')
    class_filter = request.args.get('class', 'all')
    term_filter = request.args.get('term', 'all')
    search_query = request.args.get('search_query', '').strip()

    query = 'SELECT * FROM students WHERE 1=1'
    params = []

    current_academic_year, current_term_for_status = get_current_school_period()

    if search_query:
        query += ' AND (name LIKE ? OR reg_number LIKE ?)'
        params.extend([f'%{search_query}%', f'%{search_query}%'])
    if class_filter != 'all':
        query += ' AND class = ?'
        params.append(class_filter)
    if term_filter != 'all':
        query += ' AND term = ?'
        params.append(term_filter)
    
    query += ' ORDER BY name'
    students_data = db.execute(query, params).fetchall()
    
    students_with_status = []
    for student in students_data:
        student_dict = dict(student)
        student_dict['fee_status'] = get_fee_status(student['reg_number'], current_academic_year, current_term_for_status)
        students_with_status.append(student_dict)

    if status_filter != 'all':
        students_with_status = [s for s in students_with_status if s['fee_status'] == status_filter]

    all_classes = sorted(list(set(s['class'] for s in db.execute('SELECT class FROM students').fetchall())))
    all_terms = sorted(list(set(s['term'] for s in db.execute('SELECT term FROM students').fetchall())))

    return render_template(
        'student_list.html',
        students=students_with_status,
        status_filter=status_filter,
        class_filter=class_filter,
        term_filter=term_filter,
        search_query=search_query,
        classes=all_classes,
        terms=all_terms
    )

@app.route('/student/<reg_number>')
@login_required
def student_details(reg_number):
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE reg_number = ?', (reg_number,)).fetchone()
    if student is None:
        flash('Student not found!', 'error')
        return redirect(url_for('student_list'))

    payments = db.execute('SELECT * FROM payments WHERE student_reg_number = ? ORDER BY payment_date DESC, academic_year DESC, term DESC', (reg_number,)).fetchall()
    current_academic_year, current_term = get_current_school_period()
    student_fee_status = get_fee_status(reg_number, current_academic_year, current_term)
    
    fee_breakdown = {}
    all_years_terms = set()
    all_years_terms.add((student['academic_year'], student['term']))
    for p in payments:
        all_years_terms.add((p['academic_year'], p['term']))
    all_years_terms.add((current_academic_year, current_term))

    for year, term in sorted(list(all_years_terms)):
        expected_fee_key = (student['class'], term)
        expected_amount = FEE_STRUCTURE.get(expected_fee_key, 0.0)

        total_paid_for_period = db.execute(
            'SELECT SUM(amount_paid) FROM payments WHERE student_reg_number = ? AND term = ? AND academic_year = ?',
            (reg_number, term, year)
        ).fetchone()[0] or 0.0
        
        outstanding_amount = expected_amount - total_paid_for_period

        fee_breakdown[f"{term} {year}"] = {
            'expected': expected_amount,
            'paid': total_paid_for_period,
            'outstanding': outstanding_amount
        }
    
    def sort_key_for_fee_breakdown(item):
        period_str = item[0]
        parts = period_str.split(' ')
        term_name = ' '.join(parts[:-1]) if len(parts) > 1 else parts[0]
        year_part = parts[-1] if len(parts) > 1 else ""
        
        try:
            start_year = int(year_part.split('/')[0])
        except (ValueError, IndexError):
            start_year = 0
            
        term_order = ['First Term', 'Second Term', 'Third Term']
        try:
            term_index = term_order.index(term_name)
        except ValueError:
            term_index = -1
            
        return (start_year, term_index)

    sorted_fee_breakdown = sorted(fee_breakdown.items(), key=sort_key_for_fee_breakdown, reverse=True)
    sorted_fee_breakdown_dict = {k: v for k, v in sorted_fee_breakdown}

    return render_template('student_details.html',
                           student=dict(student),
                           payments=payments,
                           fee_status=student_fee_status,
                           fee_breakdown=sorted_fee_breakdown_dict,
                           current_academic_year=current_academic_year,
                           current_term=current_term
                           )

@app.route('/make_payment/<reg_number>', methods=['GET', 'POST'])
@login_required
@admin_required
def make_payment(reg_number):
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE reg_number = ?', (reg_number,)).fetchone()
    if student is None:
        flash('Student not found!', 'error')
        return redirect(url_for('student_list'))

    if request.method == 'POST':
        amount_str = request.form['amount_paid'].strip()
        term = request.form['term'].strip()
        academic_year = request.form['academic_year'].strip()
        recorded_by = session['user_id'] # Use the logged-in user's ID
        
        try:
            amount_paid = float(amount_str)
            if amount_paid <= 0:
                flash('Payment amount must be positive.', 'error')
            else:
                payment_date = datetime.now().strftime('%Y-%m-%d')
                db.execute(
                    'INSERT INTO payments (student_reg_number, term, academic_year, amount_paid, payment_date, recorded_by) VALUES (?, ?, ?, ?, ?, ?)',
                    (reg_number, term, academic_year, amount_paid, payment_date, recorded_by)
                )
                db.commit()
                flash(f'Payment of ₦{amount_paid:,.2f} recorded for {student["name"]} for {term} {academic_year}.', 'success')
                return redirect(url_for('student_details', reg_number=reg_number))
        except ValueError:
            flash('Invalid amount. Please enter a valid number.', 'error')
        except sqlite3.Error as e:
            flash(f'Database error: {e}', 'error')

    terms = sorted(list(set(item[1] for item in FEE_STRUCTURE.keys())))
    current_year_val = datetime.now().year
    academic_years = [f"{y}/{y+1}" for y in range(current_year_val - 2, current_year_val + 3)]
    
    pre_selected_academic_year, pre_selected_term = get_current_school_period()

    return render_template('make_payment.html',
                           student=dict(student),
                           terms=terms,
                           academic_years=academic_years,
                           pre_selected_term=pre_selected_term,
                           pre_selected_academic_year=pre_selected_academic_year)
                           
if __name__ == '__main__':
    # Initialize the database on local run only
    if not os.path.exists(DATABASE):
        init_db()
        
    app.run(debug=True)
