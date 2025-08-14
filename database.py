# Enhanced Database Schema and Management
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
import json

DATABASE = 'enhanced_students.db'

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_enhanced_db():
    """Initialize comprehensive database schema"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Colleges/Universities table
    c.execute('''
        CREATE TABLE IF NOT EXISTS colleges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code TEXT NOT NULL UNIQUE,
            address TEXT,
            phone TEXT,
            email TEXT,
            established_year INTEGER,
            logo_path TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Departments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            college_id INTEGER,
            name TEXT NOT NULL,
            code TEXT NOT NULL,
            head_name TEXT,
            email TEXT,
            phone TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (college_id) REFERENCES colleges (id),
            UNIQUE(college_id, code)
        )
    ''')
    
    # Admin users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            college_id INTEGER,
            department_id INTEGER,
            phone TEXT,
            is_active BOOLEAN DEFAULT 1,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (college_id) REFERENCES colleges (id),
            FOREIGN KEY (department_id) REFERENCES departments (id)
        )
    ''')
    
    # OTP table for verification
    c.execute('''
        CREATE TABLE IF NOT EXISTS otp_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp_code TEXT NOT NULL,
            purpose TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Academic years table
    c.execute('''
        CREATE TABLE IF NOT EXISTS academic_years (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year_code TEXT UNIQUE NOT NULL,
            start_year INTEGER NOT NULL,
            end_year INTEGER NOT NULL,
            is_current BOOLEAN DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Enhanced students table
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            index_number TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            middle_name TEXT,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            date_of_birth DATE,
            gender TEXT,
            address TEXT,
            emergency_contact TEXT,
            emergency_phone TEXT,
            college_id INTEGER,
            department_id INTEGER,
            program TEXT,
            year_of_study INTEGER,
            academic_year_id INTEGER,
            admission_year INTEGER,
            photo_path TEXT,
            face_encoding TEXT,
            status TEXT DEFAULT 'active',
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (college_id) REFERENCES colleges (id),
            FOREIGN KEY (department_id) REFERENCES departments (id),
            FOREIGN KEY (academic_year_id) REFERENCES academic_years (id),
            FOREIGN KEY (created_by) REFERENCES admins (id)
        )
    ''')
    
    # Exam rooms table
    c.execute('''
        CREATE TABLE IF NOT EXISTS exam_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT NOT NULL,
            building TEXT,
            capacity INTEGER,
            college_id INTEGER,
            equipment TEXT,
            status TEXT DEFAULT 'available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (college_id) REFERENCES colleges (id)
        )
    ''')
    
    # Exam sessions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS exam_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            exam_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            room_id INTEGER,
            college_id INTEGER,
            department_id INTEGER,
            subject TEXT,
            examiner_id INTEGER,
            status TEXT DEFAULT 'scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES exam_rooms (id),
            FOREIGN KEY (college_id) REFERENCES colleges (id),
            FOREIGN KEY (department_id) REFERENCES departments (id),
            FOREIGN KEY (examiner_id) REFERENCES admins (id)
        )
    ''')
    
    # Student exam assignments
    c.execute('''
        CREATE TABLE IF NOT EXISTS exam_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_session_id INTEGER,
            student_id INTEGER,
            seat_number TEXT,
            verified BOOLEAN DEFAULT 0,
            verification_time TIMESTAMP,
            verified_by INTEGER,
            status TEXT DEFAULT 'assigned',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exam_session_id) REFERENCES exam_sessions (id),
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (verified_by) REFERENCES admins (id)
        )
    ''')
    
    # Recognition logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS recognition_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            recognition_type TEXT,
            success BOOLEAN,
            confidence_score REAL,
            method TEXT,
            ip_address TEXT,
            user_agent TEXT,
            session_id TEXT,
            exam_session_id INTEGER,
            verified_by INTEGER,
            notes TEXT,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (exam_session_id) REFERENCES exam_sessions (id),
            FOREIGN KEY (verified_by) REFERENCES admins (id)
        )
    ''')
    
    # Index number range assignments for exam rooms
    c.execute('''
        CREATE TABLE IF NOT EXISTS index_range_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_session_id INTEGER,
            room_id INTEGER,
            start_index TEXT NOT NULL,
            end_index TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exam_session_id) REFERENCES exam_sessions (id),
            FOREIGN KEY (room_id) REFERENCES exam_rooms (id)
        )
    ''')
    
    # Student attendance records for exam verification
    c.execute('''
        CREATE TABLE IF NOT EXISTS exam_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            exam_session_id INTEGER,
            verification_time TIMESTAMP,
            room_assignment TEXT,
            seat_assignment TEXT,
            verification_method TEXT DEFAULT 'face_recognition',
            confidence_score REAL,
            status TEXT DEFAULT 'present',
            verified_by_admin INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (exam_session_id) REFERENCES exam_sessions (id),
            FOREIGN KEY (verified_by_admin) REFERENCES admins (id)
        )
    ''')
    
    # System settings table
    c.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT,
            description TEXT,
            category TEXT,
            updated_by INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (updated_by) REFERENCES admins (id)
        )
    ''')
    
    # Notifications table
    c.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            target_type TEXT,
            target_id INTEGER,
            is_read BOOLEAN DEFAULT 0,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES admins (id)
        )
    ''')
    
    # Insert default data
    insert_default_data(c)
    
    conn.commit()
    conn.close()

def insert_default_data(cursor):
    """Insert default system data"""
    
    # Default college
    cursor.execute('''
        INSERT OR IGNORE INTO colleges (name, code, address, phone, email)
        VALUES (?, ?, ?, ?, ?)
    ''', ('Default University', 'DU', '123 University Ave', '+1-555-0100', 'admin@university.edu'))
    
    # Default department
    cursor.execute('''
        INSERT OR IGNORE INTO departments (college_id, name, code, head_name, email)
        VALUES (1, 'Computer Science', 'CS', 'Dr. John Doe', 'cs@university.edu')
    ''')
    
    # Default admin user (password: admin123)
    password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
    cursor.execute('''
        INSERT OR IGNORE INTO admins (username, email, password_hash, full_name, role, college_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('admin', 'admin@university.edu', password_hash, 'System Administrator', 'super_admin', 1))
    
    # Default system settings
    default_settings = [
        ('app_name', 'Student Face Recognition System', 'Application name', 'general'),
        ('theme', 'light', 'Default theme', 'appearance'),
        ('max_recognition_distance', '0.6', 'Maximum face recognition distance', 'recognition'),
        ('session_timeout', '30', 'Session timeout in minutes', 'security'),
        ('enable_notifications', 'true', 'Enable system notifications', 'general'),
        ('recognition_confidence_threshold', '0.8', 'Minimum confidence for recognition', 'recognition')
    ]
    
    for setting in default_settings:
        cursor.execute('''
            INSERT OR IGNORE INTO system_settings (setting_key, setting_value, description, category)
            VALUES (?, ?, ?, ?)
        ''', setting)
    
    # Default academic years
    academic_years = [
        ('2023/2024', 2023, 2024, False),
        ('2024/2025', 2024, 2025, False),
        ('2025/2026', 2025, 2026, True),  # Current year
        ('2026/2027', 2026, 2027, False),
    ]
    
    for year in academic_years:
        cursor.execute('''
            INSERT OR IGNORE INTO academic_years (year_code, start_year, end_year, is_current)
            VALUES (?, ?, ?, ?)
        ''', year)
    
    # Sample exam rooms
    exam_rooms = [
        ('SF26', 'Science Building', 50, 1),
        ('SF27', 'Science Building', 45, 1),
        ('LT101', 'Lecture Theatre Block', 150, 1),
        ('LT102', 'Lecture Theatre Block', 120, 1),
        ('LAB201', 'Computer Lab Block', 30, 1),
    ]
    
    for room in exam_rooms:
        cursor.execute('''
            INSERT OR IGNORE INTO exam_rooms (room_number, building, capacity, college_id)
            VALUES (?, ?, ?, ?)
        ''', room)

def hash_password(password):
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(password, hashed):
    """Verify password against hash"""
    try:
        salt, hash_part = hashed.split(':')
        return hashlib.sha256((password + salt).encode()).hexdigest() == hash_part
    except:
        # Fallback for simple hash (backward compatibility)
        return hashlib.sha256(password.encode()).hexdigest() == hashed

def migrate_database():
    """Migrate database to latest schema"""
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # Check if academic_year_id column exists in students table
        c.execute("PRAGMA table_info(students)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'academic_year_id' not in columns:
            print("Adding academic_year_id column to students table...")
            c.execute('ALTER TABLE students ADD COLUMN academic_year_id INTEGER')
            # Note: SQLite doesn't support adding foreign key constraints to existing tables
            # The constraint will be enforced through application logic
            print("Migration completed successfully!")
        else:
            print("Database is already up to date.")
            
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        conn.commit()
        conn.close()

if __name__ == '__main__':
    init_enhanced_db()
    migrate_database()
    print("Enhanced database initialized and migrated successfully!")
