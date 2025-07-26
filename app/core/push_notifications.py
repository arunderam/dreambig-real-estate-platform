"""
Enhanced push notification system for DreamBig platform
"""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from app.db import crud, models
from app.core.chat_manager import chat_manager
from app.utils.email import email_manager
from app.utils.sms import send_sms
import asyncio

logger = logging.getLogger(__name__)

class NotificationChannel:
    """Enum for notification channels"""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBSOCKET = "websocket"

class NotificationPriority:
    """Enum for notification priorities"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationTemplate:
    """Notification templates for different types"""
    
    TEMPLATES = {
        "property_inquiry": {
            "title": "New Property Inquiry",
            "message": "You have received a new inquiry for your property: {property_title}",
            "email_subject": "New Inquiry for Your Property",
            "sms_message": "New inquiry for {property_title}. Check your DreamBig account for details."
        },
        "chat_message": {
            "title": "New Message",
            "message": "{sender_name} sent you a message",
            "email_subject": "New Message from {sender_name}",
            "sms_message": "New message from {sender_name} on DreamBig"
        },
        "property_match": {
            "title": "Property Match Found",
            "message": "We found a property that matches your criteria: {property_title}",
            "email_subject": "New Property Match - {property_title}",
            "sms_message": "New property match: {property_title}. View details on DreamBig."
        },
        "investment_update": {
            "title": "Investment Update",
            "message": "Your investment in {property_title} has been updated",
            "email_subject": "Investment Update - {property_title}",
            "sms_message": "Investment update for {property_title}. Check your portfolio."
        },
        "service_booking": {
            "title": "Service Booking",
            "message": "New service booking: {service_type}",
            "email_subject": "New Service Booking - {service_type}",
            "sms_message": "New booking for {service_type}. Check your DreamBig account."
        },
        "kyc_verification": {
            "title": "KYC Verification",
            "message": "Your KYC verification status has been updated",
            "email_subject": "KYC Verification Update",
            "sms_message": "KYC verification update. Check your DreamBig profile."
        },
        "property_approved": {
            "title": "Property Approved",
            "message": "Your property listing has been approved: {property_title}",
            "email_subject": "Property Listing Approved",
            "sms_message": "Property {property_title} approved and live on DreamBig!"
        },
        "payment_received": {
            "title": "Payment Received",
            "message": "Payment of ₹{amount} received for {description}",
            "email_subject": "Payment Confirmation - ₹{amount}",
            "sms_message": "Payment of ₹{amount} received. Thank you!"
        }
    }

class PushNotificationManager:
    """Enhanced push notification manager"""
    
    def __init__(self):
        self.notification_queue = []
        self.user_preferences = {}  # Cache for user notification preferences
    
    async def send_notification(
        self,
        db: Session,
        user_id: int,
        notification_type: str,
        data: Dict[str, Any],
        channels: List[str] = None,
        priority: str = NotificationPriority.NORMAL,
        background_tasks: BackgroundTasks = None
    ) -> Dict[str, Any]:
        """Send notification through multiple channels"""
        
        try:
            # Get user
            user = crud.get_user(db, user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return {"success": False, "error": "User not found"}
            
            # Get notification template
            template = self.TEMPLATES.get(notification_type)
            if not template:
                logger.error(f"Unknown notification type: {notification_type}")
                return {"success": False, "error": "Unknown notification type"}
            
            # Get user preferences (default to all channels if not set)
            if channels is None:
                channels = await self.get_user_notification_preferences(db, user_id)
            
            # Format notification content
            formatted_content = self.format_notification_content(template, data)
            
            # Send through each channel
            results = {}
            
            # In-app notification (always send)
            if NotificationChannel.IN_APP in channels:
                results[NotificationChannel.IN_APP] = await self.send_in_app_notification(
                    db, user_id, notification_type, formatted_content, data
                )
            
            # WebSocket notification (real-time)
            if NotificationChannel.WEBSOCKET in channels:
                results[NotificationChannel.WEBSOCKET] = await self.send_websocket_notification(
                    user_id, notification_type, formatted_content, data
                )
            
            # Email notification
            if NotificationChannel.EMAIL in channels and user.email:
                if background_tasks:
                    background_tasks.add_task(
                        self.send_email_notification,
                        user.email, user.name, formatted_content, data
                    )
                    results[NotificationChannel.EMAIL] = {"queued": True}
                else:
                    results[NotificationChannel.EMAIL] = await self.send_email_notification(
                        user.email, user.name, formatted_content, data
                    )
            
            # SMS notification
            if NotificationChannel.SMS in channels and user.phone:
                if background_tasks:
                    background_tasks.add_task(
                        self.send_sms_notification,
                        user.phone, formatted_content
                    )
                    results[NotificationChannel.SMS] = {"queued": True}
                else:
                    results[NotificationChannel.SMS] = await self.send_sms_notification(
                        user.phone, formatted_content
                    )
            
            # Push notification (mobile/web push)
            if NotificationChannel.PUSH in channels:
                results[NotificationChannel.PUSH] = await self.send_push_notification(
                    user_id, formatted_content, data
                )
            
            return {
                "success": True,
                "notification_id": results.get(NotificationChannel.IN_APP, {}).get("id"),
                "channels": results
            }
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {"success": False, "error": str(e)}
    
    def format_notification_content(self, template: Dict, data: Dict) -> Dict[str, str]:
        """Format notification content with data"""
        return {
            "title": template["title"].format(**data),
            "message": template["message"].format(**data),
            "email_subject": template["email_subject"].format(**data),
            "sms_message": template["sms_message"].format(**data)
        }
    
    async def send_in_app_notification(
        self, 
        db: Session, 
        user_id: int, 
        notification_type: str, 
        content: Dict, 
        data: Dict
    ) -> Dict[str, Any]:
        """Send in-app notification"""
        try:
            notification = crud.create_notification(db, {
                "user_id": user_id,
                "title": content["title"],
                "message": content["message"],
                "type": notification_type,
                "reference_id": data.get("reference_id")
            })
            
            return {
                "success": True,
                "id": notification.id,
                "created_at": notification.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending in-app notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_websocket_notification(
        self, 
        user_id: int, 
        notification_type: str, 
        content: Dict, 
        data: Dict
    ) -> Dict[str, Any]:
        """Send real-time WebSocket notification"""
        try:
            notification_message = {
                "type": "notification",
                "notification_type": notification_type,
                "title": content["title"],
                "message": content["message"],
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            success = await chat_manager.connection_manager.send_personal_message(
                json.dumps(notification_message), user_id
            )
            
            return {"success": success}
            
        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_email_notification(
        self, 
        email: str, 
        name: str, 
        content: Dict, 
        data: Dict
    ) -> Dict[str, Any]:
        """Send email notification"""
        try:
            # Create email context
            email_context = {
                "name": name,
                "title": content["title"],
                "message": content["message"],
                "data": data,
                "dashboard_url": "http://localhost:8000/dashboard",
                "support_email": "support@dreambig.com"
            }
            
            # Send email using template
            success = email_manager.send_template_email(
                to_email=email,
                template_name="notification",
                subject=content["email_subject"],
                context=email_context
            )
            
            return {"success": success}
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_sms_notification(self, phone: str, content: Dict) -> Dict[str, Any]:
        """Send SMS notification"""
        try:
            # For now, this is a mock implementation
            # In production, integrate with SMS gateway like Twilio
            logger.info(f"Sending SMS to {phone}: {content['sms_message']}")
            
            # Mock success response
            return {"success": True, "message": "SMS sent successfully"}
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_push_notification(
        self, 
        user_id: int, 
        content: Dict, 
        data: Dict
    ) -> Dict[str, Any]:
        """Send push notification (web/mobile)"""
        try:
            # This would integrate with services like Firebase Cloud Messaging
            # or Apple Push Notification Service in production
            logger.info(f"Sending push notification to user {user_id}: {content['title']}")
            
            # Mock success response
            return {"success": True, "message": "Push notification sent"}
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_notification_preferences(self, db: Session, user_id: int) -> List[str]:
        """Get user's notification preferences"""
        # For now, return default preferences
        # In production, this would query user preferences from database
        return [
            NotificationChannel.IN_APP,
            NotificationChannel.WEBSOCKET,
            NotificationChannel.EMAIL
        ]
    
    async def send_bulk_notification(
        self,
        db: Session,
        user_ids: List[int],
        notification_type: str,
        data: Dict[str, Any],
        background_tasks: BackgroundTasks = None
    ) -> Dict[str, Any]:
        """Send notification to multiple users"""
        results = []
        
        for user_id in user_ids:
            result = await self.send_notification(
                db, user_id, notification_type, data, 
                background_tasks=background_tasks
            )
            results.append({"user_id": user_id, "result": result})
        
        return {
            "total_users": len(user_ids),
            "results": results,
            "success_count": sum(1 for r in results if r["result"]["success"]),
            "failure_count": sum(1 for r in results if not r["result"]["success"])
        }

# Global notification manager instance
push_notification_manager = PushNotificationManager()

# Convenience functions for common notification types
async def notify_property_inquiry(
    db: Session,
    property_owner_id: int,
    inquirer_name: str,
    property_title: str,
    property_id: int,
    background_tasks: BackgroundTasks = None
):
    """Send property inquiry notification"""
    return await push_notification_manager.send_notification(
        db=db,
        user_id=property_owner_id,
        notification_type="property_inquiry",
        data={
            "inquirer_name": inquirer_name,
            "property_title": property_title,
            "reference_id": property_id
        },
        priority=NotificationPriority.HIGH,
        background_tasks=background_tasks
    )

async def notify_chat_message(
    db: Session,
    recipient_id: int,
    sender_name: str,
    room_id: str,
    background_tasks: BackgroundTasks = None
):
    """Send chat message notification"""
    return await push_notification_manager.send_notification(
        db=db,
        user_id=recipient_id,
        notification_type="chat_message",
        data={
            "sender_name": sender_name,
            "room_id": room_id
        },
        channels=[NotificationChannel.WEBSOCKET, NotificationChannel.PUSH],
        priority=NotificationPriority.NORMAL,
        background_tasks=background_tasks
    )

async def notify_property_match(
    db: Session,
    user_id: int,
    property_title: str,
    property_id: int,
    background_tasks: BackgroundTasks = None
):
    """Send property match notification"""
    return await push_notification_manager.send_notification(
        db=db,
        user_id=user_id,
        notification_type="property_match",
        data={
            "property_title": property_title,
            "reference_id": property_id
        },
        priority=NotificationPriority.HIGH,
        background_tasks=background_tasks
    )
