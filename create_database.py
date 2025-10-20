#!/usr/bin/env python3
"""
Simple MySQL database creation script for SweetBite
"""

import pymysql
import getpass

def create_database():
    print("🍰 SweetBite MySQL Database Setup")
    print("=" * 40)
    
    # Get MySQL connection details
    print("\nPlease provide your MySQL connection details:")
    host = input("MySQL Host (default: localhost): ").strip() or "localhost"
    port = int(input("MySQL Port (default: 3306): ").strip() or "3306")
    username = input("MySQL Username (default: root): ").strip() or "root"
    password = getpass.getpass("MySQL Password: ")
    database_name = input("Database Name (default: sweetbite_db): ").strip() or "sweetbite_db"
    
    try:
        # Connect to MySQL server
        connection = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
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
        
        # Update Django settings
        update_django_settings(host, port, username, password, database_name)
        
        print("\n🎉 MySQL setup completed successfully!")
        print("You can now run: python manage.py migrate")
        
    except Exception as e:
        print(f"❌ Error connecting to MySQL: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure MySQL service is running")
        print("2. Check your username and password")
        print("3. Verify MySQL is accessible on the specified host/port")

def update_django_settings(host, port, username, password, database_name):
    """
    Update Django settings.py with MySQL configuration
    """
    settings_file = "sweetbite_backend/settings.py"
    
    # Read current settings
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Update database configuration
    new_db_config = f'''DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '{database_name}',
        'USER': '{username}',
        'PASSWORD': '{password}',
        'HOST': '{host}',
        'PORT': '{port}',
        'OPTIONS': {{
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }},
    }}
}}'''
    
    # Replace the database configuration
    import re
    pattern = r"DATABASES = \{[^}]+\}"
    updated_content = re.sub(pattern, new_db_config, content, flags=re.DOTALL)
    
    # Write updated settings
    with open(settings_file, 'w') as f:
        f.write(updated_content)
    
    print(f"✅ Updated Django settings with MySQL configuration")

if __name__ == "__main__":
    create_database()



