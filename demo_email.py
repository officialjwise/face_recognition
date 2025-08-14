#!/usr/bin/env python3
"""
Email Service Demo Script
This script demonstrates how to use the email service without full configuration.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from email_service import EmailService

def demo_email_service():
    """Demonstrate email service functionality"""
    
    print("📧 Email Service Demo")
    print("=" * 50)
    
    # Show current configuration status
    print("\n🔧 Configuration Status:")
    providers = ['gmail', 'outlook', 'yahoo']
    
    for provider in providers:
        username_var = f"{provider.upper()}_USERNAME"
        password_var = f"{provider.upper()}_{'APP_' if provider == 'gmail' else ''}PASSWORD"
        
        username = os.getenv(username_var)
        password = os.getenv(password_var)
        
        status = "✅ Configured" if username and password else "❌ Not configured"
        print(f"{provider.capitalize():8}: {status}")
    
    print("\n📋 Available Email Services:")
    print("1. Gmail (requires App Password)")
    print("2. Outlook/Hotmail") 
    print("3. Yahoo Mail (requires App Password)")
    print("4. Custom SMTP server")
    
    print("\n🚀 To configure email service:")
    print("1. Run: python setup_email.py")
    print("2. Or set environment variables manually")
    print("3. Or create a .env file with your settings")
    
    print("\n📖 Example usage in your application:")
    print("""
from email_service import EmailService

# Initialize service
service = EmailService(provider='gmail')

# Send OTP email
success = service.send_otp_email(
    to_email='user@example.com',
    otp='123456',
    purpose='registration'
)

# Send welcome email
success = service.send_welcome_email(
    to_email='admin@example.com',
    full_name='John Doe',
    username='john.doe'
)
    """)
    
    print("\n⚙️  Configuration Examples:")
    print("\nFor Gmail (.env file):")
    print("EMAIL_PROVIDER=gmail")
    print("GMAIL_USERNAME=your-email@gmail.com")
    print("GMAIL_APP_PASSWORD=your-16-char-app-password")
    
    print("\nFor Outlook (.env file):")
    print("EMAIL_PROVIDER=outlook")
    print("OUTLOOK_USERNAME=your-email@outlook.com")
    print("OUTLOOK_PASSWORD=your-password")
    
    print("\n📚 For detailed setup instructions, see:")
    print("- EMAIL_SETUP_GUIDE.md")
    print("- Run: python setup_email.py")

if __name__ == '__main__':
    demo_email_service()
