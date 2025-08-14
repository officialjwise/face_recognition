# Enhanced Student Face Registration System
# Main application file: enhanced_app.py

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import cv2
import numpy as np
import os
import base64
import sqlite3
from datetime import datetime, timedelta
import face_recognition
from werkzeug.utils import secure_filename
import json
import hashlib
import secrets
import random
import string
from functools import wraps
import logging
from dotenv import load_dotenv
from database import get_db_connection, init_enhanced_db, hash_password, verify_password
from email_service import EmailService

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Secure random secret key

# Configuration
UPLOAD_FOLDER = 'static/student_photos'
ENCODINGS_FOLDER = 'face_encodings'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
RECOGNITION_THRESHOLD = 0.6

# Email Configuration
EMAIL_PROVIDER = os.getenv('EMAIL_PROVIDER', 'gmail')  # gmail, outlook, yahoo, custom
EMAIL_SERVICE = None

# Initialize email service
try:
    EMAIL_SERVICE = EmailService(provider=EMAIL_PROVIDER)
    logging.info(f"Email service initialized with provider: {EMAIL_PROVIDER}")
except Exception as e:
    logging.warning(f"Email service initialization failed: {str(e)}")
    logging.warning("Email notifications will be disabled")

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ENCODINGS_FOLDER, exist_ok=True)
os.makedirs('static/logs', exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure logging
logging.basicConfig(
    filename='static/logs/app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login'))
        
        conn = get_db_connection()
        admin = conn.execute(
            'SELECT role FROM admins WHERE id = ?', (session['admin_id'],)
        ).fetchone()
        conn.close()
        
        if not admin or admin['role'] not in ['admin', 'super_admin']:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_email(to_email, subject, body):
    """Send email using configured email service"""
    try:
        if EMAIL_SERVICE:
            return EMAIL_SERVICE.send_email(to_email, subject, body)
        else:
            # Fallback: just log the email
            logging.info(f"Email service not configured. Would send to {to_email}: {subject} - {body}")
            return True
    except Exception as e:
        logging.error(f"Email sending failed: {str(e)}")
        return False

def send_otp_email(to_email, otp, purpose='verification'):
    """Send OTP email with formatted template"""
    try:
        if EMAIL_SERVICE:
            return EMAIL_SERVICE.send_otp_email(to_email, otp, purpose)
        else:
            # Fallback: just log the OTP
            logging.info(f"EMAIL SERVICE NOT CONFIGURED - OTP for {to_email}: {otp}")
            return True
    except Exception as e:
        logging.error(f"OTP email sending failed: {str(e)}")
        return False

def log_recognition_attempt(student_id, success, confidence_score, method, notes=None):
    """Log face recognition attempts"""
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO recognition_logs 
        (student_id, recognition_type, success, confidence_score, method, 
         ip_address, user_agent, session_id, verified_by, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        student_id, 'verification', success, confidence_score, method,
        request.remote_addr, request.headers.get('User-Agent'),
        session.get('session_id'), session.get('admin_id'), notes
    ))
    conn.commit()
    conn.close()

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        admin = conn.execute(
            'SELECT * FROM admins WHERE username = ? AND is_active = 1',
            (username,)
        ).fetchone()
        conn.close()
        
        if admin and verify_password(password, admin['password_hash']):
            session['admin_id'] = admin['id']
            session['admin_name'] = admin['full_name']
            session['admin_role'] = admin['role']
            session['college_id'] = admin['college_id']
            session['session_id'] = secrets.token_hex(16)
            
            # Update last login
            conn = get_db_connection()
            conn.execute(
                'UPDATE admins SET last_login = ? WHERE id = ?',
                (datetime.now(), admin['id'])
            )
            conn.commit()
            conn.close()
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        
        # Generate OTP and send to email
        otp = generate_otp()
        email = data['email']
        
        # Store OTP in database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO otp_codes (email, otp_code, purpose, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (email, otp, 'registration', datetime.now() + timedelta(minutes=10)))
        conn.commit()
        conn.close()
        
        # Send OTP email
        send_otp_email(email, otp, 'registration')
        
        # Store registration data in session
        session['registration_data'] = dict(data)
        flash('OTP sent to your email. Please verify to complete registration.', 'info')
        return redirect(url_for('verify_otp', purpose='registration'))
    
    # Get colleges for dropdown
    conn = get_db_connection()
    colleges = conn.execute('SELECT * FROM colleges WHERE status = "active"').fetchall()
    conn.close()
    
    return render_template('auth/register.html', colleges=colleges)

@app.route('/verify-otp/<purpose>', methods=['GET', 'POST'])
def verify_otp(purpose):
    if request.method == 'POST':
        otp = request.form['otp']
        email = session.get('registration_data', {}).get('email')
        
        conn = get_db_connection()
        otp_record = conn.execute('''
            SELECT * FROM otp_codes 
            WHERE email = ? AND otp_code = ? AND purpose = ? 
            AND expires_at > ? AND used = 0
        ''', (email, otp, purpose, datetime.now())).fetchone()
        
        if otp_record:
            # Mark OTP as used
            conn.execute('UPDATE otp_codes SET used = 1 WHERE id = ?', (otp_record['id'],))
            
            if purpose == 'registration':
                # Complete registration
                reg_data = session['registration_data']
                password_hash = hash_password(reg_data['password'])
                
                conn.execute('''
                    INSERT INTO admins (username, email, password_hash, full_name, role, college_id, phone)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    reg_data['username'], reg_data['email'], password_hash,
                    reg_data['full_name'], 'admin', reg_data['college_id'], reg_data['phone']
                ))
                
                flash('Registration successful! You can now login.', 'success')
                session.pop('registration_data', None)
                conn.commit()
                conn.close()
                return redirect(url_for('login'))
        else:
            flash('Invalid or expired OTP', 'error')
        
        conn.close()
    
    return render_template('auth/verify_otp.html', purpose=purpose)

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# Dashboard and Main Routes
@app.route('/')
@login_required
def dashboard():
    conn = get_db_connection()
    
    # Get statistics
    stats = {}
    stats['total_students'] = conn.execute('SELECT COUNT(*) as count FROM students').fetchone()['count']
    stats['total_colleges'] = conn.execute('SELECT COUNT(*) as count FROM colleges').fetchone()['count']
    stats['total_departments'] = conn.execute('SELECT COUNT(*) as count FROM departments').fetchone()['count']
    stats['total_exams'] = conn.execute('SELECT COUNT(*) as count FROM exam_sessions').fetchone()['count']
    
    # Recent recognition logs
    recent_logs = conn.execute('''
        SELECT rl.*, s.first_name, s.last_name, s.student_id
        FROM recognition_logs rl
        LEFT JOIN students s ON rl.student_id = s.id
        ORDER BY rl.created_at DESC LIMIT 10
    ''').fetchall()
    
    # Recognition success rate
    success_rate = conn.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
        FROM recognition_logs
        WHERE created_at >= date('now', '-7 days')
    ''').fetchone()
    
    conn.close()
    
    return render_template('dashboard/main.html', 
                         stats=stats, 
                         recent_logs=recent_logs,
                         success_rate=success_rate)

# Student Management Routes
@app.route('/students')
@login_required
def students_list():
    search = request.args.get('search', '')
    department = request.args.get('department', '')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    conn = get_db_connection()
    
    # Build query
    query = '''
        SELECT s.*, c.name as college_name, d.name as department_name
        FROM students s
        LEFT JOIN colleges c ON s.college_id = c.id
        LEFT JOIN departments d ON s.department_id = d.id
        WHERE 1=1
    '''
    params = []
    
    if search:
        query += ' AND (s.first_name LIKE ? OR s.last_name LIKE ? OR s.student_id LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])
    
    if department:
        query += ' AND s.department_id = ?'
        params.append(department)
    
    query += ' ORDER BY s.created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, (page-1) * per_page])
    
    students = conn.execute(query, params).fetchall()
    
    # Get departments for filter
    departments = conn.execute('SELECT * FROM departments ORDER BY name').fetchall()
    
    conn.close()
    
    return render_template('students/list.html', 
                         students=students, 
                         departments=departments,
                         search=search,
                         current_page=page)

@app.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        try:
            # Get form data
            data = request.form
            file = request.files.get('photo')
            
            # Validate required fields
            required_fields = ['student_id', 'index_number', 'first_name', 'last_name']
            for field in required_fields:
                if not data.get(field):
                    flash(f'{field.replace("_", " ").title()} is required', 'error')
                    return redirect(request.url)
            
            # Check for duplicates
            conn = get_db_connection()
            existing = conn.execute(
                'SELECT id FROM students WHERE student_id = ? OR index_number = ?',
                (data['student_id'], data['index_number'])
            ).fetchone()
            
            if existing:
                flash('Student ID or Index Number already exists', 'error')
                conn.close()
                return redirect(request.url)
            
            # Handle photo upload
            photo_path = None
            face_encoding_json = None
            
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{data['student_id']}_{file.filename}")
                photo_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(photo_path)
                
                # Extract face encoding
                encoding, error = save_face_encoding(photo_path, data['student_id'])
                if encoding:
                    face_encoding_json = json.dumps(encoding)
                else:
                    flash(f'Face encoding error: {error}', 'warning')
            
            # Insert student
            conn.execute('''
                INSERT INTO students 
                (student_id, index_number, first_name, middle_name, last_name,
                 email, phone, date_of_birth, gender, address, emergency_contact,
                 emergency_phone, college_id, department_id, program, year_of_study,
                 admission_year, photo_path, face_encoding, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['student_id'], data['index_number'], data['first_name'],
                data.get('middle_name'), data['last_name'], data.get('email'),
                data.get('phone'), data.get('date_of_birth'), data.get('gender'),
                data.get('address'), data.get('emergency_contact'),
                data.get('emergency_phone'), data.get('college_id'),
                data.get('department_id'), data.get('program'),
                data.get('year_of_study'), data.get('admission_year'),
                photo_path, face_encoding_json, session['admin_id']
            ))
            
            conn.commit()
            conn.close()
            
            flash('Student added successfully!', 'success')
            return redirect(url_for('students_list'))
            
        except Exception as e:
            flash(f'Error adding student: {str(e)}', 'error')
    
    # Get colleges and departments
    conn = get_db_connection()
    colleges = conn.execute('SELECT * FROM colleges WHERE status = "active"').fetchall()
    departments = conn.execute('SELECT * FROM departments ORDER BY name').fetchall()
    conn.close()
    
    return render_template('students/add.html', colleges=colleges, departments=departments)

def save_face_encoding(image_path, student_id):
    """Extract and save face encoding from image"""
    try:
        # Load image
        image = face_recognition.load_image_file(image_path)
        
        # Get face encodings
        face_encodings = face_recognition.face_encodings(image)
        
        if len(face_encodings) == 0:
            return None, "No face detected in the image"
        
        if len(face_encodings) > 1:
            return None, "Multiple faces detected. Please use an image with only one face"
        
        # Save encoding
        encoding = face_encodings[0]
        encoding_file = os.path.join(ENCODINGS_FOLDER, f"{student_id}.npy")
        np.save(encoding_file, encoding)
        
        return encoding.tolist(), None
        
    except Exception as e:
        return None, f"Error processing face: {str(e)}"

# Face Recognition Routes
@app.route('/verify')
@login_required
def verify_face():
    return render_template('recognition/verify.html')

@app.route('/api/verify-face', methods=['POST'])
@login_required
def api_verify_face():
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'success': False, 'message': 'No image provided'})
        
        # Decode base64 image
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        
        # Save temporary image
        temp_path = f"temp_verify_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        with open(temp_path, 'wb') as f:
            f.write(image_bytes)
        
        try:
            # Load and process image
            unknown_image = face_recognition.load_image_file(temp_path)
            unknown_encodings = face_recognition.face_encodings(unknown_image)
            
            if len(unknown_encodings) == 0:
                return jsonify({'success': False, 'message': 'No face detected in image'})
            
            unknown_encoding = unknown_encodings[0]
            
            # Get all student encodings
            conn = get_db_connection()
            students = conn.execute(
                'SELECT id, student_id, first_name, last_name, face_encoding FROM students WHERE face_encoding IS NOT NULL'
            ).fetchall()
            
            best_match = None
            best_distance = float('inf')
            
            for student in students:
                if student['face_encoding']:
                    stored_encoding = np.array(json.loads(student['face_encoding']))
                    distance = face_recognition.face_distance([stored_encoding], unknown_encoding)[0]
                    
                    if distance < best_distance and distance < RECOGNITION_THRESHOLD:
                        best_distance = distance
                        best_match = {
                            'id': student['id'],
                            'student_id': student['student_id'],
                            'name': f"{student['first_name']} {student['last_name']}",
                            'confidence': 1 - distance
                        }
            
            # Log recognition attempt
            if best_match:
                log_recognition_attempt(
                    best_match['id'], True, best_match['confidence'], 'camera',
                    f'Successful verification with confidence: {best_match["confidence"]:.2f}'
                )
                
                conn.close()
                return jsonify({
                    'success': True,
                    'student': best_match,
                    'message': f"Match found: {best_match['name']}"
                })
            else:
                log_recognition_attempt(
                    None, False, 0, 'camera', 'No matching student found'
                )
                
                conn.close()
                return jsonify({'success': False, 'message': 'No matching student found'})
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        logging.error(f"Face verification error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

# API Routes for AJAX
@app.route('/api/departments/<int:college_id>')
@login_required
def get_departments(college_id):
    conn = get_db_connection()
    departments = conn.execute(
        'SELECT * FROM departments WHERE college_id = ? ORDER BY name',
        (college_id,)
    ).fetchall()
    conn.close()
    
    return jsonify([{
        'id': d['id'],
        'name': d['name'],
        'code': d['code']
    } for d in departments])

if __name__ == '__main__':
    init_enhanced_db()
    app.run(debug=True, host='0.0.0.0', port=5001)
