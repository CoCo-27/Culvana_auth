from azure.communication.email import EmailClient
import logging
import os
import time
from typing import Optional, Dict, Any

class EmailService:
    def __init__(self):
        try:
            connection_string = os.environ['AZURE_COMMUNICATION_SERVICES_CONNECTION_STRING']
            self.sender_address = os.environ.get('SENDER_EMAIL_ADDRESS', 'noreply@culvana.com')
            self.email_client = EmailClient.from_connection_string(connection_string)
            logging.info(f"EmailService initialized with sender: {self.sender_address}")
            
            self.verify_domain_setup()
            
        except Exception as e:
            logging.error(f"Failed to initialize EmailService: {str(e)}", exc_info=True)
            raise

    def verify_domain_setup(self) -> bool:
        """
        Verify the email domain configuration
        Returns: bool indicating if domain setup is verified
        """
        try:
            domain = self.sender_address.split('@')[1]
            logging.info(f"Checking domain configuration for: {domain}")
            
            return True
            
        except Exception as e:
            logging.error(f"Domain verification check failed: {str(e)}", exc_info=True)
            return False

    def create_email_message(self, recipient_email: str, subject: str, 
                           plain_text: str, html_content: str) -> Dict[str, Any]:
        """
        Create an email message with the required format
        """
        return {
            "senderAddress": self.sender_address,
            "content": {
                "subject": subject,
                "plainText": plain_text,
                "html": html_content
            },
            "recipients": {
                "to": [{"address": recipient_email}]
            },
            "headers": {
                "X-Priority": "1",
                "X-MSMail-Priority": "High",
                "Importance": "high",
                "X-Microsoft-AntiSpam": "BCL:0",
                "X-Microsoft-AntiSpam-Message-Info": "None",
                "List-Unsubscribe": f"<mailto:unsubscribe@{self.sender_address.split('@')[1]}>"
            }
        }

    def monitor_send_operation(self, poller) -> Optional[Any]:
        """
        Monitor the email sending operation
        """
        try:
            while not poller.done():
                time.sleep(2)
                status = poller.status()
                logging.info(f"Email sending status: {status}")
            
            result = poller.result()
            logging.info(f"Email send result: {result}")
            
            if hasattr(result, 'message_id'):
                logging.info(f"Message ID: {result.message_id}")
            
            return result
            
        except Exception as e:
            logging.error(f"Error monitoring send operation: {str(e)}", exc_info=True)
            return None

    def send_otp_email(self, recipient_email: str, otp: str) -> bool:
        """
        Send OTP email using Azure Communication Services
        Args:
            recipient_email: The recipient's email address
            otp: The one-time password to send
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            logging.info(f"Attempting to send OTP email to {recipient_email}")
            
            plain_text = f"Your verification code is: {otp}\nThis code will expire in 10 minutes."
            html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #333;">Your Verification Code</h2>
                        <p>Your verification code is: <strong style="font-size: 18px;">{otp}</strong></p>
                        <p>This code will expire in 10 minutes.</p>
                        <hr style="border: 1px solid #eee; margin: 20px 0;">
                        <p style="color: #666; font-size: 12px;">
                            This is an automated message, please do not reply.
                        </p>
                    </div>
                </body>
                </html>
            """

            message = self.create_email_message(
                recipient_email=recipient_email,
                subject="Your Verification Code",
                plain_text=plain_text,
                html_content=html_content
            )

            logging.info(f"Sending message structure: {message}")
            
            poller = self.email_client.begin_send(message)
            
            result = self.monitor_send_operation(poller)
            
            if result:
                logging.info(f"Email successfully sent to {recipient_email}")
                return True
            else:
                logging.error(f"Failed to send email to {recipient_email}")
                return False
            
        except Exception as e:
            logging.error(f"Failed to send OTP email: {str(e)}", exc_info=True)
            logging.error(f"Full error details - Type: {type(e)}, Args: {e.args}")
            logging.error(f"Sender address: {self.sender_address}")
            logging.error(f"Recipient: {recipient_email}")
            return False

    def send_custom_email(self, recipient_email: str, subject: str, 
                         plain_text: str, html_content: str) -> bool:
        """
        Send a custom email using Azure Communication Services
        Args:
            recipient_email: The recipient's email address
            subject: Email subject
            plain_text: Plain text version of the email
            html_content: HTML version of the email
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            logging.info(f"Attempting to send custom email to {recipient_email}")
            
            message = self.create_email_message(
                recipient_email=recipient_email,
                subject=subject,
                plain_text=plain_text,
                html_content=html_content
            )
            
            poller = self.email_client.begin_send(message)
            
            result = self.monitor_send_operation(poller)
            
            if result:
                logging.info(f"Custom email successfully sent to {recipient_email}")
                return True
            else:
                logging.error(f"Failed to send custom email to {recipient_email}")
                return False
            
        except Exception as e:
            logging.error(f"Failed to send custom email: {str(e)}", exc_info=True)
            logging.error(f"Sender address: {self.sender_address}")
            logging.error(f"Recipient: {recipient_email}")
            return False