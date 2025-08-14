# Student Face Registration System
# Main application file: app.py

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import cv2
import numpy as np
import os
import base64
import sqlite3
from datetime import datetime
import face_recognition
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key

# Configuration
UPLOAD_FOLDER = 'static/student_photos'
ENCODINGS_FOLDER = 'face_encodings'
DATABASE = 'students.db'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ENCODINGS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    """Initialize the database"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            middle_name TEXT,
            last_name TEXT NOT NULL,
            index_number TEXT UNIQUE NOT NULL,
            student_id TEXT UNIQUE NOT NULL,
            photo_path TEXT,
            face_encoding TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

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

def validate_student_data(data):
    """Validate student registration data"""
    errors = []
    
    if not data.get('first_name', '').strip():
        errors.append("First name is required")
    
    if not data.get('last_name', '').strip():
        errors.append("Last name is required")
    
    index_number = data.get('index_number', '').strip()
    if not index_number:
        errors.append("Index number is required")
    elif len(index_number) != 7 or not index_number.isdigit():
        errors.append("Index number must be exactly 7 digits")
    
    student_id = data.get('student_id', '').strip()
    if not student_id:
        errors.append("Student ID is required")
    elif len(student_id) != 8 or not student_id.isdigit():
        errors.append("Student ID must be exactly 8 digits")
    
    return errors

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Validate form data
        errors = validate_student_data(request.form)
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('register'))
        
        # Check if student already exists
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT id FROM students WHERE index_number = ? OR student_id = ?', 
                 (request.form['index_number'], request.form['student_id']))
        existing = c.fetchone()
        conn.close()
        
        if existing:
            flash('Student with this index number or student ID already exists', 'error')
            return redirect(url_for('register'))
        
        # Handle file upload or camera capture
        photo_path = None
        face_encoding_json = None
        
        # Check if image was uploaded
        if 'photo' in request.files and request.files['photo'].filename:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{request.form['student_id']}_{file.filename}")
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(photo_path)
                
                # Process face encoding
                encoding, error = save_face_encoding(photo_path, request.form['student_id'])
                if error:
                    flash(f'Face processing error: {error}', 'error')
                    os.remove(photo_path)  # Clean up
                    return redirect(url_for('register'))
                face_encoding_json = json.dumps(encoding)
        
        # Check if camera data was submitted
        elif 'camera_data' in request.form and request.form['camera_data']:
            try:
                # Decode base64 image
                image_data = request.form['camera_data'].split(',')[1]
                image_binary = base64.b64decode(image_data)
                
                # Save image
                filename = f"{request.form['student_id']}_camera.jpg"
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                with open(photo_path, 'wb') as f:
                    f.write(image_binary)
                
                # Process face encoding
                encoding, error = save_face_encoding(photo_path, request.form['student_id'])
                if error:
                    flash(f'Face processing error: {error}', 'error')
                    os.remove(photo_path)  # Clean up
                    return redirect(url_for('register'))
                face_encoding_json = json.dumps(encoding)
                
            except Exception as e:
                flash(f'Camera image processing error: {str(e)}', 'error')
                return redirect(url_for('register'))
        
        else:
            flash('Please provide a photo either by upload or camera capture', 'error')
            return redirect(url_for('register'))
        
        # Save to database
        try:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute('''
                INSERT INTO students (first_name, middle_name, last_name, index_number, 
                                    student_id, photo_path, face_encoding)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form['first_name'].strip(),
                request.form.get('middle_name', '').strip() or None,
                request.form['last_name'].strip(),
                request.form['index_number'].strip(),
                request.form['student_id'].strip(),
                photo_path,
                face_encoding_json
            ))
            conn.commit()
            conn.close()
            
            flash('Student registered successfully!', 'success')
            return redirect(url_for('students'))
            
        except Exception as e:
            flash(f'Database error: {str(e)}', 'error')
            if photo_path and os.path.exists(photo_path):
                os.remove(photo_path)  # Clean up
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/students')
def students():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM students ORDER BY created_at DESC')
    students_data = c.fetchall()
    conn.close()
    
    return render_template('students.html', students=students_data)

@app.route('/verify')
def verify():
    return render_template('verify.html')

@app.route('/verify_face', methods=['POST'])
def verify_face():
    try:
        # Get image data from request
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'No image provided'})
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No image selected'})
        
        # Save temporary image
        temp_path = os.path.join(UPLOAD_FOLDER, 'temp_verify.jpg')
        file.save(temp_path)
        
        # Load and encode the verification image
        verify_image = face_recognition.load_image_file(temp_path)
        verify_encodings = face_recognition.face_encodings(verify_image)
        
        if len(verify_encodings) == 0:
            os.remove(temp_path)
            return jsonify({'success': False, 'message': 'No face detected in image'})
        
        verify_encoding = verify_encodings[0]
        
        # Compare with all registered students
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT student_id, first_name, last_name, face_encoding FROM students WHERE face_encoding IS NOT NULL')
        students = c.fetchall()
        conn.close()
        
        best_match = None
        best_distance = float('inf')
        
        for student in students:
            student_id, first_name, last_name, encoding_json = student
            stored_encoding = np.array(json.loads(encoding_json))
            
            # Calculate face distance
            distance = face_recognition.face_distance([stored_encoding], verify_encoding)[0]
            
            if distance < best_distance and distance < 0.6:  # Threshold for match
                best_distance = distance
                best_match = {
                    'student_id': student_id,
                    'name': f"{first_name} {last_name}",
                    'confidence': round((1 - distance) * 100, 2)
                }
        
        # Clean up
        os.remove(temp_path)
        
        if best_match:
            return jsonify({
                'success': True, 
                'student': best_match,
                'message': f"Match found: {best_match['name']}"
            })
        else:
            return jsonify({'success': False, 'message': 'No matching student found'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5001)
