"""
Custom email backend to handle SSL certificate issues on macOS
"""
import ssl
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings


class CustomSMTPEmailBackend(EmailBackend):
    """
    Custom SMTP email backend that handles SSL certificate verification issues
    """
    
    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, fail_silently=False, use_ssl=None, timeout=None,
                 ssl_keyfile=None, ssl_certfile=None, **kwargs):
        super().__init__(host, port, username, password, use_tls, fail_silently, 
                        use_ssl, timeout, ssl_keyfile, ssl_certfile, **kwargs)
        self.local_hostname = None
    
    def open(self):
        """
        Ensure an open connection to the email server. Return whether or not a new
        connection was required (True or False) or None if an exception occurred.
        """
        if self.connection:
            # Nothing to do if the connection is already open.
            return False
        
        try:
            # If local_hostname is not specified, socket.getfqdn() gets used.
            # For performance, we use the cached FQDN for local_hostname.
            if not self.local_hostname:
                self.local_hostname = self.get_fqdn()
            
            # Create SSL context that doesn't verify certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # If authentication is required, log in and send the HELO command.
            if self.username and self.password:
                self.connection = self.connection_class(
                    self.host, self.port, 
                    local_hostname=self.local_hostname,
                    timeout=self.timeout,
                    source_address=getattr(self, 'source_address', None)
                )
                
                # Start TLS if needed
                if self.use_tls:
                    self.connection.starttls(context=ssl_context)
                
                self.connection.login(self.username, self.password)
            else:
                self.connection = self.connection_class(
                    self.host, self.port,
                    local_hostname=self.local_hostname,
                    timeout=self.timeout,
                    source_address=getattr(self, 'source_address', None)
                )
                
                # Start TLS if needed
                if self.use_tls:
                    self.connection.starttls(context=ssl_context)
            
            return True
            
        except Exception as e:
            if not self.fail_silently:
                raise e
            return None
