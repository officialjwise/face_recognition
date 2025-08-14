#!/usr/bin/env python3
"""
Email Integration Test Script
Tests the complete email integration with the enhanced app.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_email_integration():
    """Test email integration with the enhanced app"""
    
    print("🧪 Email Integration Test")
    print("=" * 50)
    
    try:
        from email_service import EmailService
        
        # Test Gmail configuration
        print("\n1️⃣  Testing Gmail Configuration...")
        gmail_service = EmailService(provider='gmail')
        print("   ✅ Gmail service initialized successfully")
        
        # Test environment variables
        print("\n2️⃣  Testing Environment Variables...")
        gmail_user = os.getenv('GMAIL_USERNAME')
        gmail_pass = os.getenv('GMAIL_APP_PASSWORD')
        email_provider = os.getenv('EMAIL_PROVIDER')
        
        print(f"   📧 Email Provider: {email_provider}")
        print(f"   👤 Gmail Username: {gmail_user}")
        print(f"   🔐 Gmail Password: {'*' * len(gmail_pass) if gmail_pass else 'Not set'}")
        
        if gmail_user and gmail_pass:
            print("   ✅ All required environment variables are set")
        else:
            print("   ❌ Missing required environment variables")
            return False
            
        # Test OTP email
        print("\n3️⃣  Testing OTP Email...")
        test_email = gmail_user  # Send to the same email
        otp = "123456"
        
        result = gmail_service.send_otp_email(
            to_email=test_email,
            otp=otp,
            purpose="integration test"
        )
        
        if result:
            print(f"   ✅ OTP email sent successfully to {test_email}")
        else:
            print(f"   ❌ Failed to send OTP email to {test_email}")
            return False
            
        # Test welcome email
        print("\n4️⃣  Testing Welcome Email...")
        result = gmail_service.send_welcome_email(
            to_email=test_email,
            full_name="Test Admin",
            username="test.admin"
        )
        
        if result:
            print(f"   ✅ Welcome email sent successfully to {test_email}")
        else:
            print(f"   ❌ Failed to send welcome email to {test_email}")
            
        print("\n✅ Email integration test completed successfully!")
        print(f"📬 Check your inbox at {test_email} for test emails")
        return True
        
    except Exception as e:
        print(f"\n❌ Email integration test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_email_integration()
    sys.exit(0 if success else 1)
