# 📧 Email Service Configuration Guide

## Overview

The Student Face Recognition System supports multiple email providers for sending OTP codes and notifications. This guide will help you configure email services for your application.

## Supported Email Providers

### 1. Gmail (Recommended)
- **Provider Code**: `gmail`
- **SMTP Server**: smtp.gmail.com
- **Port**: 587 (TLS)
- **Security**: App Password required

#### Setup Instructions:
1. **Enable 2-Factor Authentication**
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable 2-factor authentication if not already enabled

2. **Generate App Password**
   - Visit [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and generate a password
   - Copy the 16-character password (remove spaces)

3. **Configure Environment Variables**:
   ```bash
   EMAIL_PROVIDER=gmail
   GMAIL_USERNAME=your-email@gmail.com
   GMAIL_APP_PASSWORD=abcdefghijklmnop
   ```

### 2. Outlook/Hotmail
- **Provider Code**: `outlook`
- **SMTP Server**: smtp-mail.outlook.com
- **Port**: 587 (TLS)
- **Security**: Regular password

#### Setup Instructions:
1. Use your regular Outlook/Hotmail credentials
2. May require enabling "Less secure app access" for some accounts

3. **Configure Environment Variables**:
   ```bash
   EMAIL_PROVIDER=outlook
   OUTLOOK_USERNAME=your-email@outlook.com
   OUTLOOK_PASSWORD=your-password
   ```

### 3. Yahoo Mail
- **Provider Code**: `yahoo`
- **SMTP Server**: smtp.mail.yahoo.com
- **Port**: 587 (TLS)
- **Security**: App Password required

#### Setup Instructions:
1. **Enable 2-Factor Authentication**
2. **Generate App Password**:
   - Go to Yahoo Account Security
   - Generate an app-specific password

3. **Configure Environment Variables**:
   ```bash
   EMAIL_PROVIDER=yahoo
   YAHOO_USERNAME=your-email@yahoo.com
   YAHOO_PASSWORD=your-app-password
   ```

### 4. Custom SMTP Server
- **Provider Code**: `custom`
- **Configurable**: Server, port, TLS settings
- **Security**: As per your provider

#### Setup Instructions:
1. Get SMTP details from your email provider
2. **Configure Environment Variables**:
   ```bash
   EMAIL_PROVIDER=custom
   SMTP_SERVER=smtp.yourdomain.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@yourdomain.com
   SMTP_PASSWORD=your-password
   SMTP_USE_TLS=true
   ```

## Quick Setup Methods

### Method 1: Interactive Setup Script
Run the interactive setup script:
```bash
python setup_email.py
```

This script will:
- Guide you through provider selection
- Help configure credentials
- Test the email service
- Save configuration to `.env` file

### Method 2: Manual Configuration
1. Copy the template file:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` and configure your chosen provider
3. Restart the application

### Method 3: Environment Variables
Set environment variables directly:
```bash
export EMAIL_PROVIDER=gmail
export GMAIL_USERNAME=your-email@gmail.com
export GMAIL_APP_PASSWORD=your-app-password
```

## Email Templates

The system includes professionally designed email templates:

### OTP Email Features:
- 📱 Mobile-responsive design
- 🔒 Security warnings and expiry information
- 🎨 Branded styling with your application colors
- ⏰ Clear expiry time (10 minutes)
- 🚫 Anti-phishing warnings

### Welcome Email Features:
- 🎉 Welcome message for new admin users
- 📋 Account details summary
- 🔗 Quick access links
- 📞 Support contact information

## Testing Email Configuration

### Test via Setup Script:
```bash
python setup_email.py
```

### Test via Python Console:
```python
from email_service import EmailService

# Test your configuration
service = EmailService(provider='gmail')  # or your provider
success = service.send_otp_email('test@example.com', '123456', 'testing')
print(f"Test result: {success}")
```

### Check Application Logs:
```bash
tail -f static/logs/app.log
```

## Troubleshooting

### Common Issues:

#### 1. Authentication Failed
- **Gmail**: Ensure you're using App Password, not regular password
- **Yahoo**: Verify 2FA is enabled and using App Password
- **Outlook**: Try enabling "Less secure app access"

#### 2. Connection Timeout
- Check firewall settings
- Verify SMTP server and port
- Ensure internet connectivity

#### 3. SSL/TLS Errors
- Update to latest Python version
- Check certificate validity
- Try disabling TLS temporarily for testing

#### 4. App Password Issues (Gmail/Yahoo)
- Regenerate the App Password
- Ensure no spaces in the password
- Check if 2FA is properly enabled

### Debug Steps:

1. **Check Environment Variables**:
   ```python
   import os
   print(f"Provider: {os.getenv('EMAIL_PROVIDER')}")
   print(f"Username: {os.getenv('GMAIL_USERNAME')}")  # or your provider
   ```

2. **Test SMTP Connection**:
   ```python
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login('your-email@gmail.com', 'your-app-password')
   print("Connection successful!")
   server.quit()
   ```

3. **Check Application Logs**:
   - Email sending attempts are logged
   - Look for specific error messages
   - Check for network connectivity issues

## Security Best Practices

### 1. Environment Variables
- Never commit `.env` files to version control
- Use strong, unique passwords
- Rotate App Passwords periodically

### 2. Email Security
- Use App Passwords instead of regular passwords
- Enable 2-factor authentication
- Monitor for suspicious login attempts

### 3. Application Security
- Use HTTPS in production
- Implement rate limiting for OTP requests
- Log all email sending attempts

## Production Deployment

### 1. Environment Setup
```bash
# Production environment variables
EMAIL_PROVIDER=gmail
GMAIL_USERNAME=noreply@yourdomain.com
GMAIL_APP_PASSWORD=production-app-password
APP_DOMAIN=https://yourdomain.com
ENVIRONMENT=production
```

### 2. Professional Email Setup
- Use a dedicated email address (e.g., noreply@yourdomain.com)
- Configure SPF and DKIM records for better deliverability
- Consider using a dedicated email service for high volume

### 3. Monitoring
- Set up email delivery monitoring
- Track bounce rates and delivery failures
- Implement alerting for email service failures

## API Usage

### Send OTP Email:
```python
from email_service import EmailService

service = EmailService(provider='gmail')
success = service.send_otp_email(
    to_email='user@example.com',
    otp='123456',
    purpose='registration'
)
```

### Send Welcome Email:
```python
success = service.send_welcome_email(
    to_email='admin@example.com',
    full_name='John Doe',
    username='john.doe'
)
```

### Send Custom Email:
```python
success = service.send_email(
    to_email='user@example.com',
    subject='Custom Subject',
    body='Plain text body',
    html_body='<h1>HTML Body</h1>',
    from_name='SFRS Admin'
)
```

## Support

If you encounter issues:

1. Check this documentation first
2. Review application logs
3. Test with the setup script
4. Verify your email provider's requirements
5. Check for recent changes in email provider policies

For additional support, refer to the main application documentation or contact the system administrator.
