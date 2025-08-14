# Student Exam Attendance System with Face Verification
# exam_attendance_app.py

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
app.secret_key = secrets.token_hex(32)

# Configuration
UPLOAD_FOLDER = 'static/student_photos'
ENCODINGS_FOLDER = 'face_encodings'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
RECOGNITION_THRESHOLD = 0.6

# Email Configuration
EMAIL_PROVIDER = os.getenv('EMAIL_PROVIDER', 'gmail')
EMAIL_SERVICE = None

# Initialize email service
try:
    EMAIL_SERVICE = EmailService(provider=EMAIL_PROVIDER)
    logging.info(f"Email service initialized with provider: {EMAIL_PROVIDER}")
except Exception as e:
    logging.warning(f"Email service initialization failed: {str(e)}")

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
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_student_id():
    """Generate unique student ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"STU{timestamp}{random.randint(100, 999)}"

def save_face_encoding(image_data, student_id):
    """Save face encoding from base64 image data"""
    try:
        # Decode base64 image
        image_data = image_data.split(',')[1] if ',' in image_data else image_data
        image_bytes = base64.b64decode(image_data)
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Get face encodings
        face_encodings = face_recognition.face_encodings(rgb_image)
        
        if face_encodings:
            # Save image file
            image_filename = f"{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)
            cv2.imwrite(image_path, image)
            
            # Save encoding
            encoding_filename = f"{student_id}.npy"
            encoding_path = os.path.join(ENCODINGS_FOLDER, encoding_filename)
            np.save(encoding_path, face_encodings[0])
            
            return {
                'success': True,
                'image_path': image_path,
                'encoding': face_encodings[0].tolist(),
                'message': 'Face data saved successfully'
            }
        else:
            return {
                'success': False,
                'message': 'No face detected in the image'
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error processing face data: {str(e)}'
        }

def find_exam_room_for_student(index_number, exam_session_id=None):
    """Find exam room assignment for student based on index number"""
    conn = get_db_connection()
    
    # If specific exam session provided, use it; otherwise use current active session
    if exam_session_id:
        session_filter = "AND ira.exam_session_id = ?"
        params = [index_number, exam_session_id]
    else:
        # Get current active exam session
        session_filter = "AND es.status = 'active' AND es.exam_date = date('now')"
        params = [index_number]
    
    query = f'''
        SELECT ira.*, er.room_number, er.building, es.title as exam_title, es.subject,
               es.exam_date, es.start_time, es.end_time
        FROM index_range_assignments ira
        JOIN exam_rooms er ON ira.room_id = er.id
        JOIN exam_sessions es ON ira.exam_session_id = es.id
        WHERE ? BETWEEN ira.start_index AND ira.end_index
        {session_filter}
        ORDER BY es.exam_date DESC, es.start_time DESC
        LIMIT 1
    '''
    
    result = conn.execute(query, params).fetchone()
    conn.close()
    
    return dict(result) if result else None

# ===============================
# PUBLIC ENDPOINTS
# ===============================

@app.route('/')
def index():
    """Public home page"""
    return render_template('public/index.html')

@app.route('/student/register')
def student_register():
    """Public student registration page"""
    conn = get_db_connection()
    colleges = conn.execute(
        'SELECT * FROM colleges WHERE status = "active" ORDER BY name'
    ).fetchall()
    academic_years = conn.execute(
        'SELECT * FROM academic_years WHERE status = "active" ORDER BY start_year DESC'
    ).fetchall()
    conn.close()
    
    return render_template('public/student_register.html', 
                         colleges=colleges, 
                         academic_years=academic_years)

@app.route('/api/departments/<int:college_id>')
def get_departments_by_college(college_id):
    """API endpoint to get departments by college ID"""
    conn = get_db_connection()
    departments = conn.execute(
        'SELECT * FROM departments WHERE college_id = ? AND status = "active" ORDER BY name',
        (college_id,)
    ).fetchall()
    conn.close()
    
    return jsonify([dict(dept) for dept in departments])

@app.route('/student/register', methods=['POST'])
def student_register_submit():
    """Handle student registration form submission"""
    try:
        data = request.json
        
        # Generate student ID and validate required fields
        student_id = generate_student_id()
        
        required_fields = ['first_name', 'last_name', 'index_number', 'email', 
                          'college_id', 'department_id', 'year_of_study', 
                          'academic_year_id', 'face_image']
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'})
        
        # Check if index number or email already exists
        conn = get_db_connection()
        existing = conn.execute(
            'SELECT id FROM students WHERE index_number = ? OR email = ?',
            (data['index_number'], data['email'])
        ).fetchone()
        
        if existing:
            conn.close()
            return jsonify({'success': False, 'message': 'Student with this index number or email already exists'})
        
        # Process face image
        face_result = save_face_encoding(data['face_image'], student_id)
        if not face_result['success']:
            conn.close()
            return jsonify({'success': False, 'message': face_result['message']})
        
        # Insert student record
        conn.execute('''
            INSERT INTO students (
                student_id, index_number, first_name, middle_name, last_name,
                email, phone, date_of_birth, gender, address, emergency_contact,
                emergency_phone, college_id, department_id, program, year_of_study,
                academic_year_id, photo_path, face_encoding, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            student_id, data['index_number'], data['first_name'],
            data.get('middle_name', ''), data['last_name'], data['email'],
            data.get('phone', ''), data.get('date_of_birth', ''),
            data.get('gender', ''), data.get('address', ''),
            data.get('emergency_contact', ''), data.get('emergency_phone', ''),
            data['college_id'], data['department_id'], data.get('program', ''),
            data['year_of_study'], data['academic_year_id'],
            face_result['image_path'], json.dumps(face_result['encoding']), 'active'
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Student registered successfully!',
            'student_id': student_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Registration failed: {str(e)}'})

@app.route('/student/verify')
def student_verify():
    """Public face verification page"""
    return render_template('public/student_verify.html')

@app.route('/student/verify', methods=['POST'])
def student_verify_submit():
    """Handle face verification submission"""
    try:
        data = request.json
        face_image = data.get('face_image')
        
        if not face_image:
            return jsonify({'success': False, 'message': 'Face image is required'})
        
        # Decode and process face image
        image_data = face_image.split(',')[1] if ',' in face_image else face_image
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Get face encodings from submitted image
        face_encodings = face_recognition.face_encodings(rgb_image)
        
        if not face_encodings:
            return jsonify({'success': False, 'message': 'No face detected in the image'})
        
        submitted_encoding = face_encodings[0]
        
        # Compare with all stored student encodings
        conn = get_db_connection()
        students = conn.execute('''
            SELECT s.*, c.name as college_name, d.name as department_name,
                   ay.year_code as academic_year
            FROM students s
            JOIN colleges c ON s.college_id = c.id
            JOIN departments d ON s.department_id = d.id
            JOIN academic_years ay ON s.academic_year_id = ay.id
            WHERE s.status = "active" AND s.face_encoding IS NOT NULL
        ''').fetchall()
        
        best_match = None
        best_distance = float('inf')
        
        for student in students:
            try:
                stored_encoding = np.array(json.loads(student['face_encoding']))
                distance = face_recognition.face_distance([stored_encoding], submitted_encoding)[0]
                
                if distance < RECOGNITION_THRESHOLD and distance < best_distance:
                    best_distance = distance
                    best_match = student
            except:
                continue
        
        if best_match:
            # Get exam room assignment
            room_assignment = find_exam_room_for_student(best_match['index_number'])
            
            # Log the verification
            conn.execute('''
                INSERT INTO recognition_logs (
                    student_id, recognition_type, success, confidence_score,
                    method, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                best_match['id'], 'exam_verification', True, 1.0 - best_distance,
                'face_recognition', request.remote_addr, request.headers.get('User-Agent')
            ))
            
            # Record attendance if exam room found
            if room_assignment:
                conn.execute('''
                    INSERT OR REPLACE INTO exam_attendance (
                        student_id, exam_session_id, verification_time, room_assignment,
                        verification_method, confidence_score, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    best_match['id'], room_assignment['exam_session_id'], datetime.now(),
                    f"{room_assignment['room_number']} - {room_assignment['building']}",
                    'face_recognition', 1.0 - best_distance, 'present'
                ))
            
            conn.commit()
            conn.close()
            
            student_info = {
                'name': f"{best_match['first_name']} {best_match['middle_name']} {best_match['last_name']}".strip(),
                'index_number': best_match['index_number'],
                'student_id': best_match['student_id'],
                'email': best_match['email'],
                'college': best_match['college_name'],
                'department': best_match['department_name'],
                'year_of_study': best_match['year_of_study'],
                'academic_year': best_match['academic_year'],
                'confidence': round((1.0 - best_distance) * 100, 2),
                'exam_room': room_assignment['room_number'] if room_assignment else 'Not Assigned',
                'building': room_assignment['building'] if room_assignment else '',
                'exam_title': room_assignment.get('exam_title', '') if room_assignment else '',
                'exam_date': room_assignment.get('exam_date', '') if room_assignment else '',
                'exam_time': f"{room_assignment.get('start_time', '')} - {room_assignment.get('end_time', '')}" if room_assignment else ''
            }
            
            return jsonify({
                'success': True,
                'message': 'Student verified successfully!',
                'student': student_info,
                'attendance_marked': bool(room_assignment)
            })
        else:
            # Log failed verification
            conn.execute('''
                INSERT INTO recognition_logs (
                    recognition_type, success, confidence_score,
                    method, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                'exam_verification', False, 0.0,
                'face_recognition', request.remote_addr, request.headers.get('User-Agent')
            ))
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': False,
                'message': 'Student not recognized. Please ensure good lighting and face the camera directly.'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Verification failed: {str(e)}'})

# ===============================
# ADMIN PANEL ROUTES
# ===============================

@app.route('/admin')
def admin_index():
    """Redirect to admin login"""
    return redirect(url_for('admin_login'))

@app.route('/admin/login')
def admin_login():
    """Admin login page"""
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_submit():
    """Handle admin login"""
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db_connection()
    admin = conn.execute(
        'SELECT * FROM admins WHERE username = ? AND is_active = 1',
        (username,)
    ).fetchone()
    
    if admin and verify_password(password, admin['password_hash']):
        session['admin_id'] = admin['id']
        session['admin_name'] = admin['full_name']
        session['admin_role'] = admin['role']
        session['college_id'] = admin['college_id']
        
        # Update last login
        conn.execute(
            'UPDATE admins SET last_login = ? WHERE id = ?',
            (datetime.now(), admin['id'])
        )
        conn.commit()
        conn.close()
        
        flash('Login successful!', 'success')
        return redirect(url_for('admin_dashboard'))
    else:
        conn.close()
        flash('Invalid username or password', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    conn = get_db_connection()
    
    # Get statistics
    stats = {
        'total_students': conn.execute('SELECT COUNT(*) as count FROM students WHERE status = "active"').fetchone()['count'],
        'total_colleges': conn.execute('SELECT COUNT(*) as count FROM colleges WHERE status = "active"').fetchone()['count'],
        'total_departments': conn.execute('SELECT COUNT(*) as count FROM departments WHERE status = "active"').fetchone()['count'],
        'today_verifications': conn.execute('SELECT COUNT(*) as count FROM recognition_logs WHERE date(created_at) = date("now")').fetchone()['count'],
    }
    
    # Recent verifications
    recent_verifications = conn.execute('''
        SELECT rl.*, s.first_name, s.last_name, s.index_number
        FROM recognition_logs rl
        LEFT JOIN students s ON rl.student_id = s.id
        ORDER BY rl.created_at DESC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         recent_verifications=recent_verifications)

@app.route('/admin/colleges')
@login_required
def admin_colleges():
    """Colleges management page"""
    conn = get_db_connection()
    colleges = conn.execute('SELECT * FROM colleges ORDER BY name').fetchall()
    conn.close()
    
    return render_template('admin/colleges.html', colleges=colleges)

@app.route('/admin/colleges', methods=['POST'])
@login_required
def admin_colleges_create():
    """Create new college"""
    data = request.form
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO colleges (name, code, address, phone, email, established_year)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['name'], data['code'], data.get('address', ''),
            data.get('phone', ''), data.get('email', ''),
            data.get('established_year', None)
        ))
        conn.commit()
        flash('College created successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('College name or code already exists!', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_colleges'))

@app.route('/admin/departments')
@login_required
def admin_departments():
    """Departments management page"""
    conn = get_db_connection()
    departments = conn.execute('''
        SELECT d.*, c.name as college_name
        FROM departments d
        JOIN colleges c ON d.college_id = c.id
        ORDER BY c.name, d.name
    ''').fetchall()
    colleges = conn.execute('SELECT * FROM colleges WHERE status = "active" ORDER BY name').fetchall()
    conn.close()
    
    return render_template('admin/departments.html', 
                         departments=departments, 
                         colleges=colleges)

@app.route('/admin/departments', methods=['POST'])
@login_required
def admin_departments_create():
    """Create new department"""
    data = request.form
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO departments (college_id, name, code, head_name, email, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['college_id'], data['name'], data['code'],
            data.get('head_name', ''), data.get('email', ''),
            data.get('phone', '')
        ))
        conn.commit()
        flash('Department created successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Department code already exists in this college!', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_departments'))

@app.route('/admin/students')
@login_required
def admin_students():
    """Students management page"""
    conn = get_db_connection()
    students = conn.execute('''
        SELECT s.*, c.name as college_name, d.name as department_name,
               ay.year_code as academic_year
        FROM students s
        JOIN colleges c ON s.college_id = c.id
        JOIN departments d ON s.department_id = d.id
        JOIN academic_years ay ON s.academic_year_id = ay.id
        ORDER BY s.created_at DESC
    ''').fetchall()
    conn.close()
    
    return render_template('admin/students.html', students=students)

@app.route('/admin/exam-sessions')
@login_required
def admin_exam_sessions():
    """Exam sessions management page"""
    conn = get_db_connection()
    exam_sessions = conn.execute('''
        SELECT es.*, er.room_number, er.building, c.name as college_name, d.name as department_name
        FROM exam_sessions es
        LEFT JOIN exam_rooms er ON es.room_id = er.id
        LEFT JOIN colleges c ON es.college_id = c.id
        LEFT JOIN departments d ON es.department_id = d.id
        ORDER BY es.exam_date DESC, es.start_time DESC
    ''').fetchall()
    
    rooms = conn.execute('SELECT * FROM exam_rooms ORDER BY room_number').fetchall()
    colleges = conn.execute('SELECT * FROM colleges WHERE status = "active" ORDER BY name').fetchall()
    conn.close()
    
    return render_template('admin/exam_sessions.html', 
                         exam_sessions=exam_sessions, 
                         rooms=rooms, 
                         colleges=colleges)

@app.route('/admin/exam-sessions', methods=['POST'])
@login_required
def admin_exam_sessions_create():
    """Create new exam session"""
    data = request.form
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO exam_sessions (
                title, description, exam_date, start_time, end_time,
                room_id, college_id, department_id, subject, examiner_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['title'], data.get('description', ''), data['exam_date'],
            data['start_time'], data['end_time'], data.get('room_id', None),
            data.get('college_id', None), data.get('department_id', None),
            data.get('subject', ''), session['admin_id']
        ))
        conn.commit()
        flash('Exam session created successfully!', 'success')
    except Exception as e:
        flash(f'Error creating exam session: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_exam_sessions'))

@app.route('/admin/index-assignments')
@login_required
def admin_index_assignments():
    """Index number range assignments page"""
    conn = get_db_connection()
    
    assignments = conn.execute('''
        SELECT ira.*, er.room_number, er.building, es.title as exam_title,
               c.name as college_name, d.name as department_name
        FROM index_range_assignments ira
        JOIN exam_rooms er ON ira.room_id = er.id
        JOIN exam_sessions es ON ira.exam_session_id = es.id
        LEFT JOIN colleges c ON ira.college_id = c.id
        LEFT JOIN departments d ON ira.department_id = d.id
        ORDER BY ira.created_at DESC
    ''').fetchall()
    
    exam_sessions = conn.execute('''
        SELECT es.*, er.room_number
        FROM exam_sessions es
        LEFT JOIN exam_rooms er ON es.room_id = er.id
        WHERE es.status = "scheduled"
        ORDER BY es.exam_date DESC
    ''').fetchall()
    
    rooms = conn.execute('SELECT * FROM exam_rooms ORDER BY room_number').fetchall()
    conn.close()
    
    return render_template('admin/index_assignments.html', 
                         assignments=assignments, 
                         exam_sessions=exam_sessions, 
                         rooms=rooms)

@app.route('/admin/index-assignments', methods=['POST'])
@login_required
def admin_index_assignments_create():
    """Create new index number range assignment"""
    data = request.form
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO index_range_assignments (
                exam_session_id, room_id, start_index, end_index,
                college_id, department_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['exam_session_id'], data['room_id'], data['start_index'],
            data['end_index'], data.get('college_id', None),
            data.get('department_id', None), session['admin_id']
        ))
        conn.commit()
        flash('Index range assignment created successfully!', 'success')
    except Exception as e:
        flash(f'Error creating assignment: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_index_assignments'))

@app.route('/admin/attendance-reports')
@login_required
def admin_attendance_reports():
    """Attendance reports page"""
    conn = get_db_connection()
    
    attendance = conn.execute('''
        SELECT ea.*, s.first_name, s.last_name, s.index_number,
               es.title as exam_title, es.exam_date, es.start_time,
               c.name as college_name, d.name as department_name
        FROM exam_attendance ea
        JOIN students s ON ea.student_id = s.id
        JOIN exam_sessions es ON ea.exam_session_id = es.id
        JOIN colleges c ON s.college_id = c.id
        JOIN departments d ON s.department_id = d.id
        ORDER BY ea.verification_time DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin/attendance_reports.html', attendance=attendance)

# ===============================
# ADMIN API ENDPOINTS
# ===============================

@app.route('/admin/api/students/<int:student_id>')
@login_required
def admin_student_details(student_id):
    """Get detailed student information via AJAX"""
    conn = get_db_connection()
    student = conn.execute('''
        SELECT s.*, c.name as college_name, d.name as department_name,
               ay.year_code as academic_year,
               COUNT(rl.id) as total_recognitions,
               COUNT(ea.id) as total_attendance
        FROM students s
        JOIN colleges c ON s.college_id = c.id
        JOIN departments d ON s.department_id = d.id
        JOIN academic_years ay ON s.academic_year_id = ay.id
        LEFT JOIN recognition_logs rl ON s.id = rl.student_id
        LEFT JOIN exam_attendance ea ON s.id = ea.student_id
        WHERE s.id = ?
        GROUP BY s.id
    ''', (student_id,)).fetchone()
    
    if not student:
        conn.close()
        return jsonify({'success': False, 'message': 'Student not found'})
    
    # Get recent recognition logs
    recent_logs = conn.execute('''
        SELECT * FROM recognition_logs 
        WHERE student_id = ? 
        ORDER BY created_at DESC 
        LIMIT 10
    ''', (student_id,)).fetchall()
    
    # Get exam attendance
    attendance = conn.execute('''
        SELECT ea.*, es.title as exam_title, es.exam_date
        FROM exam_attendance ea
        JOIN exam_sessions es ON ea.exam_session_id = es.id
        WHERE ea.student_id = ?
        ORDER BY ea.verification_time DESC
    ''', (student_id,)).fetchall()
    
    conn.close()
    
    return jsonify({
        'success': True,
        'student': dict(student),
        'recent_logs': [dict(log) for log in recent_logs],
        'attendance': [dict(att) for att in attendance]
    })

@app.route('/admin/api/students/<int:student_id>/toggle-status', methods=['POST'])
@login_required
def admin_toggle_student_status(student_id):
    """Toggle student active/inactive status"""
    data = request.json
    new_status = data.get('status')
    
    if new_status not in ['active', 'inactive']:
        return jsonify({'success': False, 'message': 'Invalid status'})
    
    conn = get_db_connection()
    try:
        conn.execute(
            'UPDATE students SET status = ?, updated_at = ? WHERE id = ?',
            (new_status, datetime.now(), student_id)
        )
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'Student status updated to {new_status}',
            'new_status': new_status
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating status: {str(e)}'})
    finally:
        conn.close()

@app.route('/admin/api/students/<int:student_id>', methods=['PUT'])
@login_required
def admin_edit_student(student_id):
    """Edit student information"""
    data = request.json
    
    conn = get_db_connection()
    try:
        # Update student information
        conn.execute('''
            UPDATE students SET
                first_name = ?, middle_name = ?, last_name = ?,
                email = ?, phone = ?, year_of_study = ?,
                updated_at = ?
            WHERE id = ?
        ''', (
            data.get('first_name'), data.get('middle_name', ''), data.get('last_name'),
            data.get('email'), data.get('phone', ''), data.get('year_of_study'),
            datetime.now(), student_id
        ))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Student updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating student: {str(e)}'})
    finally:
        conn.close()

@app.route('/admin/api/students/<int:student_id>', methods=['DELETE'])
@login_required
def admin_delete_student(student_id):
    """Delete student (soft delete)"""
    conn = get_db_connection()
    try:
        # Soft delete by setting status to 'deleted'
        conn.execute(
            'UPDATE students SET status = ?, updated_at = ? WHERE id = ?',
            ('deleted', datetime.now(), student_id)
        )
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Student deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deleting student: {str(e)}'})
    finally:
        conn.close()

@app.route('/admin/api/colleges/<int:college_id>/toggle-status', methods=['POST'])
@login_required
def admin_toggle_college_status(college_id):
    """Toggle college active/inactive status"""
    data = request.json
    new_status = data.get('status')
    
    if new_status not in ['active', 'inactive']:
        return jsonify({'success': False, 'message': 'Invalid status'})
    
    conn = get_db_connection()
    try:
        conn.execute(
            'UPDATE colleges SET status = ? WHERE id = ?',
            (new_status, college_id)
        )
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'College status updated to {new_status}',
            'new_status': new_status
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating status: {str(e)}'})
    finally:
        conn.close()

@app.route('/admin/api/departments/<int:department_id>/toggle-status', methods=['POST'])
@login_required
def admin_toggle_department_status(department_id):
    """Toggle department active/inactive status"""
    data = request.json
    new_status = data.get('status')
    
    if new_status not in ['active', 'inactive']:
        return jsonify({'success': False, 'message': 'Invalid status'})
    
    conn = get_db_connection()
    try:
        conn.execute(
            'UPDATE departments SET status = ? WHERE id = ?',
            (new_status, department_id)
        )
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'Department status updated to {new_status}',
            'new_status': new_status
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating status: {str(e)}'})
    finally:
        conn.close()

@app.route('/admin/api/exam-sessions/<int:session_id>/activate', methods=['POST'])
@login_required
def admin_activate_exam_session(session_id):
    """Activate an exam session"""
    conn = get_db_connection()
    try:
        # First, deactivate all other sessions for the same date
        session_info = conn.execute(
            'SELECT exam_date FROM exam_sessions WHERE id = ?', (session_id,)
        ).fetchone()
        
        if not session_info:
            return jsonify({'success': False, 'message': 'Exam session not found'})
        
        # Deactivate other sessions on the same date
        conn.execute(
            'UPDATE exam_sessions SET status = "scheduled" WHERE exam_date = ? AND status = "active"',
            (session_info['exam_date'],)
        )
        
        # Activate the target session
        conn.execute(
            'UPDATE exam_sessions SET status = "active" WHERE id = ?',
            (session_id,)
        )
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Exam session activated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error activating session: {str(e)}'})
    finally:
        conn.close()

if __name__ == '__main__':
    # Initialize database
    init_enhanced_db()
    
    # Run the application
    app.run(host='0.0.0.0', port=5002, debug=True)
