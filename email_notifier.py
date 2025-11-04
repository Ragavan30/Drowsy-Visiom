"""
Email notification system for drowsiness alerts
Sends email with snapshot attachments via SMTP
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
import config

class EmailNotifier:
    def __init__(self):
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.sender_email = config.SENDER_EMAIL
        self.sender_password = config.SENDER_PASSWORD
        self.receiver_email = config.RECEIVER_EMAIL
        
    def create_message(self, snapshot_path, detection_time):
        """Create email message with snapshot attachment"""
        msg = MIMEMultipart()
        
        # Email headers
        msg['From'] = self.sender_email
        msg['To'] = self.receiver_email
        msg['Subject'] = "🚨 DROWSINESS ALERT - Immediate Attention Required"
        
        # Email body
        detection_datetime = datetime.fromtimestamp(detection_time)
        body = f"""
        ⚠️ DROWSINESS DETECTION ALERT ⚠️
        
        This is an automated alert from your Drowsiness Detection System.
        
        Detection Details:
        • Time: {detection_datetime.strftime('%Y-%m-%d %H:%M:%S')}
        • Status: DROWSY STATE DETECTED
        • Action Required: Please ensure safety immediately
        
        A snapshot has been captured and attached to this email for your review.
        
        Please take appropriate safety measures:
        • Stop driving if you are currently driving
        • Take a break and rest
        • Consider consuming caffeine or taking a nap
        • Ensure you are in a safe location
        
        This alert is generated automatically by your drowsiness detection system.
        Stay safe!
        
        --
        Drowsiness Detection System
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach snapshot if it exists
        if snapshot_path and os.path.exists(snapshot_path):
            try:
                with open(snapshot_path, 'rb') as attachment:
                    img = MIMEImage(attachment.read())
                    img.add_header('Content-Disposition', 
                                 f'attachment; filename="drowsiness_snapshot_{int(detection_time)}.jpg"')
                    msg.attach(img)
            except Exception as e:
                print(f"Error attaching image: {e}")
        
        return msg
    
    def send_alert(self, snapshot_path, detection_time):
        """Send drowsiness alert email"""
        try:
            # Skip if email is not configured
            if not all([self.sender_email, self.sender_password, self.receiver_email]):
                print("Email configuration incomplete - skipping email alert")
                return False
            
            print(f"Sending drowsiness alert email to {self.receiver_email}...")
            
            # Create message
            msg = self.create_message(snapshot_path, detection_time)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print("Drowsiness alert email sent successfully!")
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def test_email_connection(self):
        """Test email configuration and connection"""
        try:
            if not all([self.sender_email, self.sender_password, self.receiver_email]):
                return False, "Email configuration incomplete"
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
            
            return True, "Email connection successful"
            
        except Exception as e:
            return False, f"Email connection failed: {e}"
    
    def send_test_email(self):
        """Send a test email to verify configuration"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.receiver_email
            msg['Subject'] = "🧪 Drowsiness Detection System - Test Email"
            
            body = f"""
            This is a test email from your Drowsiness Detection System.
            
            If you receive this email, your email configuration is working correctly.
            
            Configuration Details:
            • SMTP Server: {self.smtp_server}:{self.smtp_port}
            • Sender: {self.sender_email}
            • Receiver: {self.receiver_email}
            
            Test sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            --
            Drowsiness Detection System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return True, "Test email sent successfully"
            
        except Exception as e:
            return False, f"Failed to send test email: {e}"
