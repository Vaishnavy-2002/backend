#!/usr/bin/env python3
"""
Simple MySQL setup for SweetBite
"""

import pymysql
import sys

def setup_mysql():
    print("🍰 SweetBite MySQL Database Setup")
    print("=" * 40)
    
    # Try different common MySQL configurations
    configs = [
        {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': ''},
        {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': 'root'},
        {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': 'password'},
        {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': '123456'},
    ]
    
    database_name = 'sweetbite_db'
    
    for i, config in enumerate(configs):
        try:
            print(f"\nTrying configuration {i+1}: {config['user']}@{config['host']}:{config['port']}")
            
            connection = pymysql.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                charset='utf8mb4'
            )
            
            with connection.cursor() as cursor:
                # Create database
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"✅ Database '{database_name}' created successfully!")
                
                # Test database connection
                cursor.execute(f"USE {database_name}")
                print(f"✅ Successfully connected to database '{database_name}'!")
            
            connection.close()
            
            # Update Django settings with working configuration
            update_django_settings(config)
            
            print(f"\n🎉 MySQL setup completed successfully!")
            print(f"Using configuration: {config['user']}@{config['host']}:{config['port']}")
            print("You can now run: python manage.py migrate")
            return True
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            continue
    
    print("\n❌ Could not connect to MySQL with any common configuration.")
    print("\nPlease manually configure MySQL:")
    print("1. Make sure MySQL service is running")
    print("2. Check your MySQL root password")
    print("3. Update the PASSWORD field in settings.py")
    return False

def update_django_settings(config):
    """Update Django settings with working MySQL configuration"""
    settings_file = "sweetbite_backend/settings.py"
    
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Update the password in settings
    import re
    pattern = r"('PASSWORD': ')[^']*(')"
    replacement = f"\\g<1>{config['password']}\\g<2>"
    updated_content = re.sub(pattern, replacement, content)
    
    with open(settings_file, 'w') as f:
        f.write(updated_content)
    
    print(f"✅ Updated Django settings with MySQL configuration")

if __name__ == "__main__":
    setup_mysql()



