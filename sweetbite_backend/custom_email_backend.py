# Custom Email Backend for SweetBite
# Handles SSL certificate issues and provides better error handling

import ssl
import smtplib
import os
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail.message import EmailMessage
from django.conf import settings

# Disable SSL verification globally
os.environ['PYTHONHTTPSVERIFY'] = '0'


class CustomSMTPEmailBackend(EmailBackend):
    """
    Custom SMTP backend that handles SSL certificate issues
    """
    
    def open(self):
        """
        Ensure an open connection to the email server.
        Return whether or not a new connection was required (True or False).
        """
        if self.connection:
            # Nothing to do if the connection is already open.
            return False
        
        try:
            print(f"🔗 Connecting to SMTP server: {self.host}:{self.port}")
            
            # Create SSL context that doesn't verify certificates
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect to SMTP server
            self.connection = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            print(f"✅ Connected to SMTP server")
            
            # Enable debug output (optional)
            if settings.DEBUG:
                self.connection.set_debuglevel(1)
            
            # Start TLS with custom context
            if self.use_tls:
                print(f"🔒 Starting TLS connection...")
                self.connection.starttls(context=context)
                print(f"✅ TLS connection established")
            
            # Login if credentials are provided
            if self.username and self.password:
                print(f"🔑 Logging in with username: {self.username}")
                self.connection.login(self.username, self.password)
                print(f"✅ Successfully logged in")
            
            return True
            
        except Exception as e:
            print(f"❌ SMTP Connection Error: {str(e)}")
            if not self.fail_silently:
                raise
            return False
    
    def close(self):
        """Close the connection to the email server."""
        if self.connection is None:
            return
        try:
            self.connection.quit()
        except (smtplib.SMTPException, OSError):
            if self.fail_silently:
                return
            raise
        finally:
            self.connection = None
