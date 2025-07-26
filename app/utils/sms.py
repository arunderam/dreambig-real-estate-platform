import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import BackgroundTasks
from app.config import settings

logger = logging.getLogger(__name__)

class SMSProvider:
    """Base SMS provider class"""

    def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:  # type: ignore
        raise NotImplementedError

class TwilioSMSProvider(SMSProvider):
    """Twilio SMS provider implementation"""

    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.phone_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
        self.enabled = all([self.account_sid, self.auth_token, self.phone_number])

        if self.enabled:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio SMS provider initialized successfully")
            except ImportError:
                logger.warning("Twilio library not installed. Install with: pip install twilio")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.enabled = False
        else:
            logger.warning("Twilio SMS provider not configured. Check environment variables.")

    def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS using Twilio"""
        if not self.enabled:
            return {
                "success": False,
                "error": "Twilio SMS provider not configured or available",
                "provider": "twilio"
            }

        try:
            # Format phone number (ensure it starts with +)
            if not phone_number.startswith('+'):
                phone_number = '+91' + phone_number.lstrip('0')  # Default to India

            # Send SMS
            message_obj = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=phone_number
            )

            return {
                "success": True,
                "message_sid": message_obj.sid,
                "status": message_obj.status,
                "provider": "twilio",
                "sent_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to send SMS via Twilio to {phone_number}: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "twilio"
            }

class MockSMSProvider(SMSProvider):
    """Mock SMS provider for development/testing"""

    def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Mock SMS sending"""
        logger.info(f"[MOCK SMS] To: {phone_number}, Message: {message}")
        return {
            "success": True,
            "message_sid": f"mock_{datetime.now().timestamp()}",
            "status": "sent",
            "provider": "mock",
            "sent_at": datetime.now(timezone.utc).isoformat()
        }

class SMSManager:
    """Enhanced SMS manager with multiple providers"""

    def __init__(self):
        self.providers = {
            "twilio": TwilioSMSProvider(),
            "mock": MockSMSProvider()
        }

        # Select primary provider
        if self.providers["twilio"].enabled:
            self.primary_provider = "twilio"
        else:
            self.primary_provider = "mock"

        logger.info(f"SMS Manager initialized with primary provider: {self.primary_provider}")

    def send_sms(
        self,
        phone_number: str,
        message: str,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send SMS using specified or primary provider"""

        if provider is None:
            provider = self.primary_provider

        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Unknown SMS provider: {provider}",
                "available_providers": list(self.providers.keys())
            }

        return self.providers[provider].send_sms(phone_number, message)

    def send_bulk_sms(
        self,
        phone_numbers: List[str],
        message: str,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send SMS to multiple recipients"""
        results = []
        success_count = 0

        for phone_number in phone_numbers:
            result = self.send_sms(phone_number, message, provider)
            results.append({
                "phone_number": phone_number,
                "result": result
            })
            if result["success"]:
                success_count += 1

        return {
            "total_recipients": len(phone_numbers),
            "success_count": success_count,
            "failure_count": len(phone_numbers) - success_count,
            "results": results
        }

    def send_otp(self, phone_number: str, otp: str) -> Dict[str, Any]:
        """Send OTP SMS"""
        message = f"Your DreamBig verification code is: {otp}. This code will expire in 10 minutes. Do not share this code with anyone."
        return self.send_sms(phone_number, message)

    def send_property_alert(
        self,
        phone_number: str,
        property_title: str,
        property_id: int
    ) -> Dict[str, Any]:
        """Send property alert SMS"""
        message = f"New property match: {property_title}. View details at http://localhost:8000/properties/{property_id}"
        return self.send_sms(phone_number, message)

    def send_booking_confirmation(
        self,
        phone_number: str,
        service_type: str,
        booking_id: int
    ) -> Dict[str, Any]:
        """Send booking confirmation SMS"""
        message = f"Your {service_type} booking (ID: {booking_id}) has been confirmed. You will be contacted soon."
        return self.send_sms(phone_number, message)

# Global SMS manager instance
sms_manager = SMSManager()

# Legacy function for backward compatibility
async def send_sms(
    background_tasks: BackgroundTasks,
    phone_numbers: List[str],
    message: str
):
    """Send SMS using background task (legacy function)"""
    def _send():
        for phone_number in phone_numbers:
            result = sms_manager.send_sms(phone_number, message)
            if not result["success"]:
                logger.error(f"Failed to send SMS to {phone_number}: {result.get('error')}")

    background_tasks.add_task(_send)

# New enhanced functions
def send_sms_sync(phone_number: str, message: str) -> Dict[str, Any]:
    """Send SMS synchronously"""
    return sms_manager.send_sms(phone_number, message)

def send_bulk_sms_sync(phone_numbers: List[str], message: str) -> Dict[str, Any]:
    """Send bulk SMS synchronously"""
    return sms_manager.send_bulk_sms(phone_numbers, message)

async def send_sms_async(
    background_tasks: BackgroundTasks,
    phone_number: str,
    message: str
) -> None:
    """Send SMS asynchronously"""
    def _send():
        result = sms_manager.send_sms(phone_number, message)
        if not result["success"]:
            logger.error(f"Failed to send SMS to {phone_number}: {result.get('error')}")

    background_tasks.add_task(_send)

async def send_otp_sms(
    background_tasks: BackgroundTasks,
    phone_number: str,
    otp: str
) -> None:
    """Send OTP SMS asynchronously"""
    def _send():
        result = sms_manager.send_otp(phone_number, otp)
        if not result["success"]:
            logger.error(f"Failed to send OTP SMS to {phone_number}: {result.get('error')}")

    background_tasks.add_task(_send)