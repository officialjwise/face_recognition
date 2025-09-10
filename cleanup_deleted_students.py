#!/usr/bin/env python3
"""
Cleanup Script for Soft-Deleted Students
This script will permanently remove students that were marked as 'deleted' but not actually removed
"""

import sqlite3
import os

def cleanup_soft_deleted_students():
    """Permanently remove students marked as 'deleted'"""
    conn = sqlite3.connect('enhanced_students.db')
    cursor = conn.cursor()
    
    try:
        # Get all soft-deleted students
        cursor.execute("SELECT id, student_id FROM students WHERE status = 'deleted'")
        deleted_students = cursor.fetchall()
        
        if not deleted_students:
            print("No soft-deleted students found.")
            return
        
        print(f"Found {len(deleted_students)} soft-deleted students to clean up:")
        
        for student_id, student_uid in deleted_students:
            print(f"- Cleaning up student: {student_uid}")
            
            # Delete related records
            cursor.execute('DELETE FROM exam_assignments WHERE student_id = ?', (student_id,))
            cursor.execute('DELETE FROM recognition_logs WHERE student_id = ?', (student_id,))
            
            # Clean up files
            try:
                # Delete face encoding file
                encoding_file = f"face_encodings/{student_uid}.npy"
                if os.path.exists(encoding_file):
                    os.remove(encoding_file)
                    print(f"  - Deleted encoding: {encoding_file}")
                
                # Delete student photos
                photos_dir = "static/student_photos"
                if os.path.exists(photos_dir):
                    for filename in os.listdir(photos_dir):
                        if filename.startswith(student_uid):
                            file_path = os.path.join(photos_dir, filename)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                print(f"  - Deleted photo: {filename}")
            except Exception as file_error:
                print(f"  - Warning: Could not delete some files for {student_uid}: {file_error}")
        
        # Now permanently delete the student records
        cursor.execute("DELETE FROM students WHERE status = 'deleted'")
        conn.commit()
        
        print(f"\nSuccessfully cleaned up {len(deleted_students)} soft-deleted students.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during cleanup: {e}")
    finally:
        conn.close()

def check_student_status():
    """Check current student status in database"""
    conn = sqlite3.connect('enhanced_students.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT status, COUNT(*) FROM students GROUP BY status")
        results = cursor.fetchall()
        
        print("Current student status summary:")
        total = 0
        for status, count in results:
            print(f"  {status}: {count}")
            total += count
        print(f"  Total: {total}")
        
    except Exception as e:
        print(f"Error checking status: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("SOFT-DELETED STUDENTS CLEANUP")
    print("=" * 60)
    
    print("Current status:")
    check_student_status()
    
    print("\nStarting cleanup...")
    cleanup_soft_deleted_students()
    
    print("\nFinal status:")
    check_student_status()
