#!/usr/bin/env python3
"""
Student Deletion Script
This script will delete all students and clean up associated files
"""

import os
import shutil
from database import delete_all_students, hard_delete_all_students

def cleanup_student_files():
    """Remove all student photos and face encodings"""
    
    # Clean up student photos
    photos_dir = "static/student_photos"
    if os.path.exists(photos_dir):
        print("Cleaning up student photos...")
        try:
            # Remove all files in the directory
            for filename in os.listdir(photos_dir):
                file_path = os.path.join(photos_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Deleted photo: {filename}")
            print("Student photos cleanup completed.")
        except Exception as e:
            print(f"Error cleaning up student photos: {e}")


    if os.path.exists(photos_dir) and not os.listdir(photos_dir):
        try:
            os.rmdir(photos_dir)
            print(f"Removed empty directory: {photos_dir}")
        except Exception as e:
            print(f"Error removing directory {photos_dir}: {e}")
    
    # Clean up face encodings
    encodings_dir = "face_encodings"
    if os.path.exists(encodings_dir):
        print("Cleaning up face encodings...")
        try:
            # Remove all .npy files in the directory
            for filename in os.listdir(encodings_dir):
                if filename.endswith('.npy'):
                    file_path = os.path.join(encodings_dir, filename)
                    os.remove(file_path)
                    print(f"Deleted encoding: {filename}")
            print("Face encodings cleanup completed.")
        except Exception as e:
            print(f"Error cleaning up face encodings: {e}")

def main():
    """Main deletion process"""
    print("=" * 60)
    print("STUDENT DELETION SCRIPT")
    print("=" * 60)
    
    print("\nThis script will:")
    print("1. Delete all student records from the database")
    print("2. Remove all student photos")
    print("3. Remove all face encoding files")
    print("4. Clean up related records (exam assignments, recognition logs)")
    
    choice = input("\nChoose deletion type:\n1. Soft delete (mark as deleted)\n2. Hard delete (permanent removal)\nEnter choice (1 or 2): ").strip()
    
    if choice not in ['1', '2']:
        print("Invalid choice. Exiting.")
        return
    
    confirm = input(f"\nAre you sure you want to {'soft' if choice == '1' else 'permanently'} delete ALL students? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Operation cancelled.")
        return
    
    print("\nStarting deletion process...")
    
    # Delete from database
    if choice == '1':
        success = delete_all_students()
    else:
        success = hard_delete_all_students()
    
    if success:
        # Clean up files
        cleanup_student_files()
        print("\n" + "=" * 60)
        print("DELETION COMPLETED SUCCESSFULLY!")
        print("All students and associated files have been removed.")
        print("=" * 60)
    else:
        print("\nDeletion failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
