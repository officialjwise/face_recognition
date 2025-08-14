"""
Student Face Registration System - Run Script
Execute this script to start the application
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'flask', 'opencv-python', 'face-recognition', 
        'numpy', 'pillow', 'werkzeug'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing packages: {', '.join(missing_packages)}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    return True

def main():
    print("=" * 50)
    print("Student Face Registration System")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print("Error: app.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    print("Starting the application...")
    print("Access the application at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Run the Flask application
    try:
        subprocess.run([sys.executable, 'app.py'])
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    main()