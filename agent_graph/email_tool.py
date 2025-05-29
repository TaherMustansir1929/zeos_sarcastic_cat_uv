import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

from langchain_core.tools import tool

load_dotenv()


@tool
def send_email(to_email: str, message: str, subject:str = "No Subject"):
    """
    Send an email to a specified email address.
    
    Args:
        to_email (str): Recipient's email address.
        message (str): Email's message content
        subject (str): Email's subject
    """
    
    # Email configuration - you'll need to set these
    smtp_server = "smtp.gmail.com"  # Gmail SMTP server
    smtp_port = 587
    sender_email = os.getenv("SENDER_EMAIL")  # Your email
    sender_password = os.getenv("EMAIL_PASSWORD")  # Your app password
    
    # Validate inputs
    if not sender_email or not sender_password:
        print("Error: Email credentials not found in environment variables")
        return "Error: Email credentials not found in environment variables"
    
    if not to_email or not message:
        print("Error: Recipient email and message are required")
        return "Error: Recipient email and message are required"
    
    message += "\n\n`Note: This email was sent by an AI Agent. Thank You`"
    to_email = to_email.lower().strip()
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS encryption
        server.login(sender_email, sender_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
        return f"Email sent successfully to {to_email}"
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return f"Error sending email: {str(e)}"

# Example usage
import time

if __name__ == "__main__":
    # Example function call
    recipient = "abbashuzaifa54@gmail.com"
    email_message = "Hello! This is a test email sent from Python."
    email_subject = "Get A Job"
    
    for _ in range(10):
        send_email.invoke(input={
            "to_email": recipient,
            "message": email_message,
            "subject": email_subject
        })
        time.sleep(0.2)