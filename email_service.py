# Email Service Configuration and Implementation
# email_service.py

import smtplib
import logging
import ssl
import os
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class EmailService:
    """Email service class supporting multiple providers"""
    
    def __init__(self, provider='gmail', **kwargs):
        self.provider = provider.lower()
        self.config = self._get_config(provider, **kwargs)
        
    def _get_config(self, provider, **kwargs):
        """Get configuration for different email providers"""
        configs = {
            'gmail': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'use_tls': True,
                'username': kwargs.get('username') or os.getenv('GMAIL_USERNAME'),
                'password': kwargs.get('password') or os.getenv('GMAIL_APP_PASSWORD'),
            },
            'outlook': {
                'smtp_server': 'smtp-mail.outlook.com',
                'smtp_port': 587,
                'use_tls': True,
                'username': kwargs.get('username') or os.getenv('OUTLOOK_USERNAME'),
                'password': kwargs.get('password') or os.getenv('OUTLOOK_PASSWORD'),
            },
            'yahoo': {
                'smtp_server': 'smtp.mail.yahoo.com',
                'smtp_port': 587,
                'use_tls': True,
                'username': kwargs.get('username') or os.getenv('YAHOO_USERNAME'),
                'password': kwargs.get('password') or os.getenv('YAHOO_PASSWORD'),
            },
            'custom': {
                'smtp_server': kwargs.get('smtp_server'),
                'smtp_port': kwargs.get('smtp_port', 587),
                'use_tls': kwargs.get('use_tls', True),
                'username': kwargs.get('username'),
                'password': kwargs.get('password'),
            }
        }
        
        if provider not in configs:
            raise ValueError(f"Unsupported email provider: {provider}")
            
        config = configs[provider]
        
        # Validate required fields
        if not config['username'] or not config['password']:
            raise ValueError(f"Username and password required for {provider}")
            
        return config
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   html_body: Optional[str] = None, 
                   from_name: Optional[str] = None) -> bool:
        """Send email with optional HTML body"""
        try:
            # Create message
            from_addr = f"{from_name} <{self.config['username']}>" if from_name else self.config['username']
            
            # Create message body
            if html_body:
                message = f"""From: {from_addr}
To: {to_email}
Subject: {subject}
MIME-Version: 1.0
Content-Type: text/html; charset=utf-8

{html_body}
"""
            else:
                message = f"""From: {from_addr}
To: {to_email}
Subject: {subject}

{body}
"""
            
            # Connect to server and send email
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            
            if self.config['use_tls']:
                context = ssl.create_default_context()
                server.starttls(context=context)
            
            server.login(self.config['username'], self.config['password'])
            server.sendmail(self.config['username'], to_email, message.encode('utf-8'))
            server.quit()
            
            logging.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logging.error(f"Email sending failed: {str(e)}")
            return False
    
    def send_otp_email(self, to_email: str, otp: str, purpose: str = 'verification') -> bool:
        """Send OTP email with formatted template"""
        subject = f"Your OTP Code for {purpose.title()}"
        
        text_body = f"""
Hello,

Your OTP code for {purpose} is: {otp}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Student Face Recognition System Team
        """
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #2563eb, #1e40af); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: white; padding: 30px; border: 1px solid #e2e8f0; }}
        .otp-code {{ background: #f8fafc; border: 2px dashed #2563eb; padding: 20px; text-align: center; margin: 20px 0; border-radius: 10px; }}
        .otp-number {{ font-size: 32px; font-weight: bold; color: #2563eb; letter-spacing: 5px; }}
        .footer {{ background: #f8fafc; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; color: #6b7280; }}
        .warning {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Student Face Recognition System</h1>
            <p>OTP Verification Code</p>
        </div>
        
        <div class="content">
            <h2>Hello!</h2>
            <p>You have requested an OTP code for <strong>{purpose}</strong>.</p>
            
            <div class="otp-code">
                <p>Your verification code is:</p>
                <div class="otp-number">{otp}</div>
                <p><small>Enter this code to continue</small></p>
            </div>
            
            <div class="warning">
                <strong>⚠️ Important:</strong>
                <ul>
                    <li>This code will expire in <strong>10 minutes</strong></li>
                    <li>Do not share this code with anyone</li>
                    <li>If you didn't request this code, please ignore this email</li>
                </ul>
            </div>
            
            <p>If you're having trouble, please contact our support team.</p>
        </div>
        
        <div class="footer">
            <p>© 2025 Student Face Recognition System. All rights reserved.</p>
            <p><small>This is an automated message, please do not reply to this email.</small></p>
        </div>
    </div>
</body>
</html>
        """
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=text_body,
            html_body=html_body,
            from_name="SFRS Admin"
        )
    
    def send_welcome_email(self, to_email: str, full_name: str, username: str) -> bool:
        """Send welcome email to new admin users"""
        subject = "Welcome to Student Face Recognition System"
        
        text_body = f"""
Hello {full_name},

Welcome to the Student Face Recognition System!

Your admin account has been successfully created with the following details:
- Username: {username}
- Email: {to_email}

You can now log in to the admin dashboard and start managing students and face recognition settings.

Best regards,
SFRS Team
        """
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #059669, #047857); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: white; padding: 30px; border: 1px solid #e2e8f0; }}
        .welcome-box {{ background: #f0f9ff; border: 1px solid #0891b2; padding: 20px; border-radius: 10px; margin: 20px 0; }}
        .button {{ display: inline-block; background: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
        .footer {{ background: #f8fafc; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; color: #6b7280; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Welcome to SFRS!</h1>
            <p>Student Face Recognition System</p>
        </div>
        
        <div class="content">
            <h2>Hello {full_name}!</h2>
            <p>Welcome to the Student Face Recognition System. Your admin account has been successfully created!</p>
            
            <div class="welcome-box">
                <h3>Account Details:</h3>
                <p><strong>Username:</strong> {username}</p>
                <p><strong>Email:</strong> {to_email}</p>
                <p><strong>Role:</strong> Administrator</p>
            </div>
            
            <p>You can now:</p>
            <ul>
                <li>✅ Access the admin dashboard</li>
                <li>✅ Manage student records</li>
                <li>✅ Configure face recognition settings</li>
                <li>✅ Monitor system activity</li>
                <li>✅ Generate reports</li>
            </ul>
            
            <div style="text-align: center;">
                <a href="#" class="button">Login to Dashboard</a>
            </div>
            
            <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
        </div>
        
        <div class="footer">
            <p>© 2025 Student Face Recognition System. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=text_body,
            html_body=html_body,
            from_name="SFRS Admin"
        )

# Configuration examples for different providers
def get_email_service_examples():
    """Return configuration examples for different email providers"""
    return {
        'gmail': {
            'description': 'Gmail (requires App Password)',
            'setup_instructions': [
                '1. Enable 2-factor authentication on your Google account',
                '2. Generate an App Password: https://myaccount.google.com/apppasswords',
                '3. Use your Gmail address as username and App Password as password'
            ],
            'env_vars': {
                'GMAIL_USERNAME': 'your-email@gmail.com',
                'GMAIL_APP_PASSWORD': 'your-16-character-app-password'
            }
        },
        'outlook': {
            'description': 'Outlook/Hotmail',
            'setup_instructions': [
                '1. Use your Outlook email and password',
                '2. May require enabling "Less secure app access" for some accounts'
            ],
            'env_vars': {
                'OUTLOOK_USERNAME': 'your-email@outlook.com',
                'OUTLOOK_PASSWORD': 'your-password'
            }
        },
        'yahoo': {
            'description': 'Yahoo Mail (requires App Password)',
            'setup_instructions': [
                '1. Enable 2-factor authentication',
                '2. Generate App Password in Yahoo Account Security',
                '3. Use Yahoo email and App Password'
            ],
            'env_vars': {
                'YAHOO_USERNAME': 'your-email@yahoo.com',
                'YAHOO_PASSWORD': 'your-app-password'
            }
        },
        'custom': {
            'description': 'Custom SMTP Server',
            'setup_instructions': [
                '1. Get SMTP server details from your email provider',
                '2. Configure server, port, and authentication details'
            ],
            'env_vars': {
                'SMTP_SERVER': 'smtp.yourdomain.com',
                'SMTP_PORT': '587',
                'SMTP_USERNAME': 'your-email@yourdomain.com',
                'SMTP_PASSWORD': 'your-password'
            }
        }
    }

if __name__ == '__main__':
    # Example usage
    print("Email Service Configuration Examples:")
    examples = get_email_service_examples()
    
    for provider, config in examples.items():
        print(f"\n{provider.upper()}:")
        print(f"Description: {config['description']}")
        print("Setup Instructions:")
        for instruction in config['setup_instructions']:
            print(f"  {instruction}")
        print("Environment Variables:")
        for var, example in config['env_vars'].items():
            print(f"  {var}={example}")
