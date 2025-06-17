# ===== FIXED API/SERVICES/RESEND_SERVICE.PY =====
import resend
import os
import random
import string
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ResendService:
    def __init__(self):
        self.api_key = os.getenv('REACT_APP_RESEND_API_KEY')
        self.from_email = os.getenv('REACT_APP_RESEND_FROM_EMAIL', 'noreply@hpique.nl')
        self.from_name = os.getenv('REACT_APP_RESEND_FROM_NAME', 'Cold Calling Coach')
        
        if not self.api_key:
            raise ValueError("Resend API key must be provided")
        
        # Set the API key
        resend.api_key = self.api_key
        
        # Log configuration for debugging
        logger.info(f"Resend service initialized:")
        logger.info(f"- API Key present: {'Yes' if self.api_key else 'No'}")
        logger.info(f"- From email: {self.from_email}")
        logger.info(f"- From name: {self.from_name}")
    
    def generate_verification_code(self) -> str:
        """Generate 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=6))
    
    def send_verification_email(self, email: str, code: str, first_name: str = "") -> bool:
        """Send verification email with proper response handling"""
        try:
            # Log the attempt
            logger.info(f"Attempting to send verification email to {email}")
            
            # Format the from field with both name and email
            from_field = f"{self.from_name} <{self.from_email}>"
            
            params = {
                "from": from_field,
                "to": [email],
                "subject": "Verify your email - Cold Calling Coach",
                "html": self._get_verification_email_html(code, first_name)
            }
            
            # Log the parameters (without sensitive data)
            logger.info(f"Email parameters: from={from_field}, to={email}, subject={params['subject']}")
            
            # Send the email
            response = resend.Emails.send(params)
            
            # Log the full response for debugging
            logger.info(f"Resend API response: {response}")
            
            # Fixed: Check if response is a dict with 'id' key OR an object with 'id' attribute
            if self._is_successful_response(response):
                email_id = response.get('id') if isinstance(response, dict) else getattr(response, 'id', None)
                logger.info(f"Email sent successfully with ID: {email_id}")
                return True
            else:
                logger.error(f"Email send failed - unexpected response: {response}")
                return False
            
        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
            logger.error(f"Exception type: {type(e)}")
            return False
    
    def send_password_reset_email(self, email: str, reset_link: str, first_name: str = "") -> bool:
        """Send password reset email"""
        try:
            from_field = f"{self.from_name} <{self.from_email}>"
            
            params = {
                "from": from_field,
                "to": [email],
                "subject": "Reset your password - Cold Calling Coach",
                "html": self._get_password_reset_email_html(reset_link, first_name)
            }
            
            response = resend.Emails.send(params)
            logger.info(f"Password reset email sent to {email}: {response}")
            
            return self._is_successful_response(response)
            
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
            return False
    
    def send_welcome_email(self, email: str, first_name: str) -> bool:
        """Send welcome email after successful registration"""
        try:
            from_field = f"{self.from_name} <{self.from_email}>"
            
            params = {
                "from": from_field,
                "to": [email],
                "subject": "Welcome to Cold Calling Coach!",
                "html": self._get_welcome_email_html(first_name)
            }
            
            response = resend.Emails.send(params)
            logger.info(f"Welcome email sent to {email}: {response}")
            
            return self._is_successful_response(response)
            
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
            return False
    
    def _is_successful_response(self, response) -> bool:
        """Check if the Resend response indicates success"""
        if not response:
            return False
        
        # Handle dictionary response (most common)
        if isinstance(response, dict):
            return 'id' in response and response['id']
        
        # Handle object response (alternative format)
        if hasattr(response, 'id'):
            return bool(response.id)
        
        # If we can't determine success, log and assume failure
        logger.warning(f"Unknown response format: {type(response)} - {response}")
        return False
    
    def send_test_email(self, to_email: str) -> dict:
        """Send a test email for debugging purposes"""
        try:
            from_field = f"{self.from_name} <{self.from_email}>"
            
            params = {
                "from": from_field,
                "to": [to_email],
                "subject": "Test Email - Cold Calling Coach",
                "html": "<h1>Test Email</h1><p>If you receive this, Resend is working correctly!</p>"
            }
            
            response = resend.Emails.send(params)
            
            if self._is_successful_response(response):
                return {
                    "success": True,
                    "response": response,
                    "message": "Test email sent successfully"
                }
            else:
                return {
                    "success": False,
                    "response": response,
                    "message": "Test email failed - unexpected response"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Test email failed with exception"
            }
    
    def _get_verification_email_html(self, code: str, first_name: str) -> str:
        """Get HTML template for verification email"""
        name_greeting = f"Hi {first_name}," if first_name else "Hello,"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                <h1 style="color: #007bff; text-align: center; margin-bottom: 30px;">
                    <span style="font-size: 24px;">📞</span> Cold Calling Coach
                </h1>
                
                <p style="font-size: 16px; color: #333;">{name_greeting}</p>
                
                <p style="font-size: 16px; color: #333;">
                    Welcome to Cold Calling Coach! Please verify your email address to complete your registration.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <div style="font-size: 32px; font-weight: bold; color: #007bff; letter-spacing: 3px; padding: 20px; background-color: #f8f9fa; border-radius: 8px; display: inline-block;">
                        {code}
                    </div>
                </div>
                
                <p style="font-size: 14px; color: #666;">
                    This code will expire in 10 minutes. If you didn't request this verification, please ignore this email.
                </p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #999; text-align: center;">
                    Cold Calling Coach - Practice makes perfect!<br>
                    <a href="https://hpique.nl" style="color: #007bff;">Visit our website</a>
                </p>
            </div>
        </body>
        </html>
        """
    
    def _get_password_reset_email_html(self, reset_link: str, first_name: str) -> str:
        """Get HTML template for password reset email"""
        name_greeting = f"Hi {first_name}," if first_name else "Hello,"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                <h1 style="color: #007bff; text-align: center; margin-bottom: 30px;">
                    <span style="font-size: 24px;">📞</span> Cold Calling Coach
                </h1>
                
                <p style="font-size: 16px; color: #333;">{name_greeting}</p>
                
                <p style="font-size: 16px; color: #333;">
                    We received a request to reset your password. Click the button below to create a new password:
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="display: inline-block; background-color: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Reset Password
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666;">
                    This link will expire in 1 hour. If you didn't request a password reset, please ignore this email.
                </p>
                
                <p style="font-size: 12px; color: #999;">
                    If the button doesn't work, copy and paste this link into your browser:<br>
                    <a href="{reset_link}" style="color: #007bff; word-break: break-all;">{reset_link}</a>
                </p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #999; text-align: center;">
                    Cold Calling Coach - Practice makes perfect!<br>
                    <a href="https://hpique.nl" style="color: #007bff;">Visit our website</a>
                </p>
            </div>
        </body>
        </html>
        """
    
    def _get_welcome_email_html(self, first_name: str) -> str:
        """Get HTML template for welcome email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to Cold Calling Coach!</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                <h1 style="color: #007bff; text-align: center; margin-bottom: 30px;">
                    <span style="font-size: 24px;">📞</span> Cold Calling Coach
                </h1>
                
                <p style="font-size: 18px; color: #333;">Hi {first_name},</p>
                
                <p style="font-size: 16px; color: #333;">
                    Welcome to Cold Calling Coach! 🎉 You're now ready to start improving your English cold calling skills.
                </p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0;">
                    <h3 style="color: #007bff; margin-top: 0;">What's Next?</h3>
                    <ul style="margin-bottom: 0;">
                        <li>Complete your first roleplay: "Opener + Early Objections"</li>
                        <li>Practice with different modes: Practice, Marathon, and Legend</li>
                        <li>Unlock advanced modules as you improve</li>
                        <li>Get personalized coaching feedback after each session</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://hpique.nl/dashboard" style="display: inline-block; background-color: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Start Training Now
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666;">
                    Need help? Reply to this email or visit our support page.
                </p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #999; text-align: center;">
                    Cold Calling Coach - Practice makes perfect!<br>
                    <a href="https://hpique.nl" style="color: #007bff;">Visit our website</a>
                </p>
            </div>
        </body>
        </html>
        """