"""
Enhanced email utilities for DreamBig application
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
from jinja2 import Environment, FileSystemLoader
import os
from fastapi import BackgroundTasks

from app.config import settings

logger = logging.getLogger(__name__)

class EmailManager:
    """Enhanced email manager with template support"""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAILS_FROM_EMAIL or settings.SMTP_USER

        # Setup Jinja2 for email templates
        template_dir = Path("app/templates/email")
        template_dir.mkdir(parents=True, exist_ok=True)

        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send email with optional attachments"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            if cc:
                msg['Cc'] = ', '.join(cc)

            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)

            # Add HTML content
            if html_content:
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)

            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())

                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        msg.attach(part)

            # Send email
            context = ssl.create_default_context()

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)

                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)

                server.sendmail(self.from_email, recipients, msg.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_template_email(
        self,
        to_email: str,
        template_name: str,
        subject: str,
        context: Dict[str, Any],
        attachments: List[str] = None
    ) -> bool:
        """Send email using Jinja2 template"""
        try:
            # Load and render template
            template = self.jinja_env.get_template(f"{template_name}.html")
            html_content = template.render(**context)

            # Try to load text version
            text_content = None
            try:
                text_template = self.jinja_env.get_template(f"{template_name}.txt")
                text_content = text_template.render(**context)
            except:
                # If no text template, create simple text version
                text_content = f"Please view this email in HTML format.\n\nSubject: {subject}"

            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                attachments=attachments
            )

        except Exception as e:
            logger.error(f"Failed to send template email to {to_email}: {str(e)}")
            return False

# Global email manager instance
email_manager = EmailManager()

# Legacy function for backward compatibility
async def send_email(
    background_tasks: BackgroundTasks,
    email_to: str,
    subject: str,
    body: str,
    html: Optional[str] = None
):
    """Send email using SMTP in background (legacy function)"""
    def _send():
        email_manager.send_email(
            to_email=email_to,
            subject=subject,
            text_content=body,
            html_content=html
        )

    background_tasks.add_task(_send)

# Convenience functions for common email types
def send_welcome_email(email: str, name: str) -> bool:
    """Send welcome email to new user"""
    context = {
        "name": name,
        "login_url": "http://localhost:8000/login",
        "support_email": "support@dreambig.com"
    }

    return email_manager.send_template_email(
        to_email=email,
        template_name="welcome",
        subject="Welcome to DreamBig!",
        context=context
    )

def send_verification_email(email: str, name: str, verification_token: str) -> bool:
    """Send email verification email"""
    verification_url = f"http://localhost:8000/verify-email?token={verification_token}"

    context = {
        "name": name,
        "verification_url": verification_url,
        "support_email": "support@dreambig.com"
    }

    return email_manager.send_template_email(
        to_email=email,
        template_name="email_verification",
        subject="Verify Your Email - DreamBig",
        context=context
    )

def send_password_reset_email(email: str, name: str, reset_token: str) -> bool:
    """Send password reset email"""
    reset_url = f"http://localhost:8000/reset-password?token={reset_token}"

    context = {
        "name": name,
        "reset_url": reset_url,
        "support_email": "support@dreambig.com"
    }

    return email_manager.send_template_email(
        to_email=email,
        template_name="password_reset",
        subject="Reset Your Password - DreamBig",
        context=context
    )

def send_property_inquiry_email(
    owner_email: str,
    owner_name: str,
    inquirer_name: str,
    inquirer_email: str,
    property_title: str,
    message: str
) -> bool:
    """Send property inquiry email to owner"""
    context = {
        "owner_name": owner_name,
        "inquirer_name": inquirer_name,
        "inquirer_email": inquirer_email,
        "property_title": property_title,
        "message": message,
        "dashboard_url": "http://localhost:8000/dashboard"
    }

    return email_manager.send_template_email(
        to_email=owner_email,
        template_name="property_inquiry",
        subject=f"New Inquiry for {property_title}",
        context=context
    )

def send_booking_confirmation_email(booking_id: int, user_email: str) -> bool:
    """Send booking confirmation email"""
    context = {
        "booking_id": booking_id,
        "dashboard_url": "http://localhost:8000/dashboard",
        "support_email": "support@dreambig.com"
    }

    return email_manager.send_template_email(
        to_email=user_email,
        template_name="booking_confirmation",
        subject="Booking Confirmation - DreamBig Real Estate",
        context=context
    )

def send_application_notification_email(application_id: int, property_owner_email: str) -> bool:
    """Send rental application notification to property owner"""
    context = {
        "application_id": application_id,
        "dashboard_url": "http://localhost:8000/dashboard",
        "support_email": "support@dreambig.com"
    }

    return email_manager.send_template_email(
        to_email=property_owner_email,
        template_name="application_notification",
        subject="New Rental Application - DreamBig Real Estate",
        context=context
    )

def send_offer_notification_email(offer_id: int, property_owner_email: str, offered_price: float) -> bool:
    """Send purchase offer notification to property owner"""
    context = {
        "offer_id": offer_id,
        "offered_price": f"₹{offered_price:,.2f}",
        "dashboard_url": "http://localhost:8000/dashboard",
        "support_email": "support@dreambig.com"
    }

    return email_manager.send_template_email(
        to_email=property_owner_email,
        template_name="offer_notification",
        subject="New Purchase Offer - DreamBig Real Estate",
        context=context
    )