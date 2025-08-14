#!/usr/bin/env python3
"""
Email Service Setup Script for Student Face Recognition System
This script helps you configure email services for OTP and notifications.
"""

import os
import sys
import getpass
from email_service import EmailService, get_email_service_examples

def print_header():
    print("=" * 60)
    print("   📧 SFRS Email Service Configuration Setup")
    print("=" * 60)
    print()

def print_provider_info():
    print("📋 Available Email Providers:")
    print()
    examples = get_email_service_examples()
    
    for i, (provider, config) in enumerate(examples.items(), 1):
        print(f"{i}. {provider.upper()}")
        print(f"   Description: {config['description']}")
        print()

def choose_provider():
    providers = list(get_email_service_examples().keys())
    
    while True:
        try:
            choice = input(f"Choose email provider (1-{len(providers)}): ").strip()
            index = int(choice) - 1
            if 0 <= index < len(providers):
                return providers[index]
            else:
                print(f"Please enter a number between 1 and {len(providers)}")
        except ValueError:
            print("Please enter a valid number")

def get_provider_config(provider):
    """Get configuration for the selected provider"""
    config = {}
    examples = get_email_service_examples()
    
    print(f"\n🔧 Configuring {provider.upper()}")
    print("-" * 40)
    
    # Show setup instructions
    print("Setup Instructions:")
    for instruction in examples[provider]['setup_instructions']:
        print(f"  {instruction}")
    print()
    
    if provider == 'gmail':
        config['username'] = input("Gmail address: ").strip()
        config['password'] = getpass.getpass("App Password (16 characters): ").strip()
        
    elif provider == 'outlook':
        config['username'] = input("Outlook email: ").strip()
        config['password'] = getpass.getpass("Password: ").strip()
        
    elif provider == 'yahoo':
        config['username'] = input("Yahoo email: ").strip()
        config['password'] = getpass.getpass("App Password: ").strip()
        
    elif provider == 'custom':
        config['smtp_server'] = input("SMTP Server: ").strip()
        config['smtp_port'] = int(input("SMTP Port (default 587): ").strip() or "587")
        config['use_tls'] = input("Use TLS? (y/n, default y): ").strip().lower() != 'n'
        config['username'] = input("Email/Username: ").strip()
        config['password'] = getpass.getpass("Password: ").strip()
    
    return config

def test_email_service(provider, config):
    """Test the email service configuration"""
    print(f"\n🧪 Testing {provider} configuration...")
    
    try:
        email_service = EmailService(provider=provider, **config)
        
        test_email = input("Enter a test email address (or press Enter to skip): ").strip()
        if test_email:
            print("Sending test email...")
            success = email_service.send_otp_email(test_email, "123456", "testing")
            
            if success:
                print("✅ Test email sent successfully!")
                return True
            else:
                print("❌ Test email failed to send")
                return False
        else:
            print("⏭️  Skipping email test")
            return True
            
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        return False

def save_configuration(provider, config):
    """Save configuration to environment file"""
    env_file = '.env'
    env_lines = []
    
    # Read existing .env file if it exists
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_lines = f.readlines()
    
    # Update or add email configuration
    new_lines = []
    email_vars_added = set()
    
    # Add provider setting
    provider_line = f"EMAIL_PROVIDER={provider}\n"
    
    for line in env_lines:
        if line.startswith('EMAIL_PROVIDER='):
            new_lines.append(provider_line)
        elif line.startswith(f'{provider.upper()}_'):
            # Skip existing provider config lines, we'll add new ones
            continue
        else:
            new_lines.append(line)
    
    # If EMAIL_PROVIDER wasn't in the file, add it
    if not any(line.startswith('EMAIL_PROVIDER=') for line in env_lines):
        new_lines.append(provider_line)
    
    # Add provider-specific configuration
    if provider == 'gmail':
        new_lines.append(f"GMAIL_USERNAME={config['username']}\n")
        new_lines.append(f"GMAIL_APP_PASSWORD={config['password']}\n")
    elif provider == 'outlook':
        new_lines.append(f"OUTLOOK_USERNAME={config['username']}\n")
        new_lines.append(f"OUTLOOK_PASSWORD={config['password']}\n")
    elif provider == 'yahoo':
        new_lines.append(f"YAHOO_USERNAME={config['username']}\n")
        new_lines.append(f"YAHOO_PASSWORD={config['password']}\n")
    elif provider == 'custom':
        new_lines.append(f"SMTP_SERVER={config['smtp_server']}\n")
        new_lines.append(f"SMTP_PORT={config['smtp_port']}\n")
        new_lines.append(f"SMTP_USERNAME={config['username']}\n")
        new_lines.append(f"SMTP_PASSWORD={config['password']}\n")
        new_lines.append(f"SMTP_USE_TLS={str(config['use_tls']).lower()}\n")
    
    # Write updated configuration
    with open(env_file, 'w') as f:
        f.writelines(new_lines)
    
    print(f"✅ Configuration saved to {env_file}")

def main():
    print_header()
    
    # Check if .env template exists
    if not os.path.exists('.env.template'):
        print("⚠️  Warning: .env.template not found")
        print("   This script works best with the template file")
        print()
    
    print_provider_info()
    
    # Choose provider
    provider = choose_provider()
    
    # Get configuration
    config = get_provider_config(provider)
    
    # Test configuration
    if test_email_service(provider, config):
        # Save configuration
        save_configuration(provider, config)
        
        print("\n🎉 Email service setup completed successfully!")
        print("\nNext steps:")
        print("1. Restart your application to load the new configuration")
        print("2. Test OTP functionality during user registration")
        print("3. Check application logs for any email-related issues")
        
    else:
        print("\n❌ Setup failed. Please check your configuration and try again.")
        
        retry = input("\nWould you like to try again? (y/n): ").strip().lower()
        if retry == 'y':
            main()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
