#!/usr/bin/env python3
"""
Quick Test Runner for Room Assignment & Attendance Features
This script runs automated tests to verify core functionality
"""

import sqlite3
import sys
from datetime import datetime, date
import json

def test_database_setup():
    """Test that database is properly configured"""
    print("🔍 Testing Database Setup...")
    
    conn = sqlite3.connect('enhanced_students.db')
    cursor = conn.cursor()
    
    # Check required tables exist
    required_tables = ['exam_sessions', 'index_range_assignments', 'exam_attendance', 'students']
    for table in required_tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if cursor.fetchone():
            print(f"  ✓ Table '{table}' exists")
        else:
            print(f"  ❌ Table '{table}' missing")
            return False
    
    conn.close()
    return True

def test_room_assignment_logic():
    """Test room assignment based on index numbers"""
    print("🎯 Testing Room Assignment Logic...")
    
    try:
        from exam_attendance_app import find_exam_room_for_student
        
        # Test cases
        test_cases = [
            ('8552721', True, 'Student within range should get assignment'),
            ('8555000', True, 'Student at upper bound should get assignment'),
            ('8541000', True, 'Student at lower bound should get assignment'),
            ('8540999', False, 'Student below range should not get assignment'),
            ('8555822', False, 'Student above range should not get assignment'),
            ('1234567', False, 'Random student should not get assignment'),
        ]
        
        for index_num, should_assign, description in test_cases:
            room = find_exam_room_for_student(index_num)
            has_assignment = room is not None
            
            if has_assignment == should_assign:
                print(f"  ✓ {description} - PASS")
            else:
                print(f"  ❌ {description} - FAIL")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing room assignment: {e}")
        return False

def test_attendance_creation():
    """Test attendance record creation"""
    print("📝 Testing Attendance Creation...")
    
    conn = sqlite3.connect('enhanced_students.db')
    cursor = conn.cursor()
    
    try:
        # Get test student
        cursor.execute("SELECT id FROM students WHERE index_number = '8552999' LIMIT 1")
        student = cursor.fetchone()
        
        if not student:
            print("  ⚠ No test student found, creating one...")
            cursor.execute('''
                INSERT INTO students (student_id, index_number, first_name, last_name, 
                                    email, college_id, department_id, academic_year_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('TEST_AUTO_999', '8552999', 'Test', 'Auto', 'test@auto.com', 1, 1, 1, 'active'))
            student_id = cursor.lastrowid
        else:
            student_id = student[0]
        
        # Get active exam session
        cursor.execute('''
            SELECT id FROM exam_sessions 
            WHERE status = 'active' AND exam_date = ?
        ''', (str(date.today()),))
        session = cursor.fetchone()
        
        if not session:
            print("  ❌ No active exam session found")
            return False
        
        session_id = session[0]
        
        # Test attendance creation (simulate what happens in verification)
        initial_count = cursor.execute(
            'SELECT COUNT(*) FROM exam_attendance WHERE student_id = ? AND exam_session_id = ?',
            (student_id, session_id)
        ).fetchone()[0]
        
        # Create attendance record
        cursor.execute('''
            INSERT OR REPLACE INTO exam_attendance (
                student_id, exam_session_id, verification_time, room_assignment,
                verification_method, confidence_score, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student_id, session_id, datetime.now(), 'SF26 - Science Building',
              'face_recognition_auto', 0.95, 'present'))
        
        final_count = cursor.execute(
            'SELECT COUNT(*) FROM exam_attendance WHERE student_id = ? AND exam_session_id = ?',
            (student_id, session_id)
        ).fetchone()[0]
        
        if final_count > 0:
            print("  ✓ Attendance record created successfully")
            conn.commit()
            return True
        else:
            print("  ❌ Failed to create attendance record")
            return False
            
    except Exception as e:
        print(f"  ❌ Error testing attendance creation: {e}")
        return False
    finally:
        conn.close()

def test_hard_delete_simulation():
    """Test hard delete functionality (simulation)"""
    print("🗑️ Testing Hard Delete Logic...")
    
    conn = sqlite3.connect('enhanced_students.db')
    cursor = conn.cursor()
    
    try:
        # Create a test assignment to delete
        cursor.execute('''
            INSERT INTO index_range_assignments (
                exam_session_id, room_id, start_index, end_index, created_at
            ) VALUES (?, ?, ?, ?, ?)
        ''', (1, 1, '9000000', '9000999', datetime.now()))
        
        test_assignment_id = cursor.lastrowid
        print(f"  ✓ Created test assignment {test_assignment_id}")
        
        # Verify it exists
        cursor.execute('SELECT * FROM index_range_assignments WHERE id = ?', (test_assignment_id,))
        if not cursor.fetchone():
            print("  ❌ Test assignment not found")
            return False
        
        # Simulate hard delete
        cursor.execute('DELETE FROM index_range_assignments WHERE id = ?', (test_assignment_id,))
        deleted_count = cursor.rowcount
        
        # Verify deletion
        cursor.execute('SELECT * FROM index_range_assignments WHERE id = ?', (test_assignment_id,))
        still_exists = cursor.fetchone()
        
        if deleted_count == 1 and not still_exists:
            print("  ✓ Hard delete simulation successful")
            conn.commit()
            return True
        else:
            print("  ❌ Hard delete simulation failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error testing hard delete: {e}")
        return False
    finally:
        conn.close()

def run_all_tests():
    """Run all automated tests"""
    print("🚀 Starting Automated Testing Suite")
    print("=" * 50)
    
    tests = [
        test_database_setup,
        test_room_assignment_logic,
        test_attendance_creation,
        test_hard_delete_simulation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"  ❌ Test failed with error: {e}")
            results.append(False)
            print()
    
    print("=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System ready for manual testing.")
        print("\nNext Steps:")
        print("1. Start the application: python3 exam_attendance_app.py")
        print("2. Follow the Complete Testing Guide for manual verification")
        print("3. Test the UI components and user workflows")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        failed_tests = [i for i, result in enumerate(results) if not result]
        print(f"Failed test indices: {failed_tests}")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
