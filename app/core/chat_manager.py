"""
Real-time chat system for DreamBig platform
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.db import crud, models
from app.core.security import verify_token
import asyncio

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time chat"""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[int, WebSocket] = {}
        # Store user sessions
        self.user_sessions: Dict[int, dict] = {}
        # Store chat rooms and their participants
        self.chat_rooms: Dict[str, Set[int]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: int, user_data: dict):
        """Accept WebSocket connection and store user info"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_sessions[user_id] = {
            "user_id": user_id,
            "name": user_data.get("name", "Unknown"),
            "email": user_data.get("email", ""),
            "role": user_data.get("role", "user"),
            "connected_at": datetime.utcnow(),
            "status": "online"
        }
        logger.info(f"User {user_id} connected to chat")
        
        # Notify other users about online status
        await self.broadcast_user_status(user_id, "online")
    
    def disconnect(self, user_id: int):
        """Remove user connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        # Remove user from all chat rooms
        for room_id in list(self.chat_rooms.keys()):
            if user_id in self.chat_rooms[room_id]:
                self.chat_rooms[room_id].discard(user_id)
                if not self.chat_rooms[room_id]:  # Remove empty rooms
                    del self.chat_rooms[room_id]
        
        logger.info(f"User {user_id} disconnected from chat")
    
    async def send_personal_message(self, message: str, user_id: int):
        """Send message to specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
                return True
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                # Remove broken connection
                self.disconnect(user_id)
                return False
        return False
    
    async def broadcast_to_room(self, room_id: str, message: str, exclude_user: Optional[int] = None):
        """Broadcast message to all users in a chat room"""
        if room_id not in self.chat_rooms:
            return
        
        disconnected_users = []
        for user_id in self.chat_rooms[room_id]:
            if exclude_user and user_id == exclude_user:
                continue
                
            if user_id in self.active_connections:
                try:
                    await self.active_connections[user_id].send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
                    disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)
    
    async def broadcast_user_status(self, user_id: int, status: str):
        """Broadcast user online/offline status to relevant users"""
        status_message = {
            "type": "user_status",
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Broadcast to all connected users (you might want to limit this to relevant users)
        message_str = json.dumps(status_message)
        for connected_user_id in list(self.active_connections.keys()):
            if connected_user_id != user_id:
                await self.send_personal_message(message_str, connected_user_id)
    
    def join_room(self, room_id: str, user_id: int):
        """Add user to chat room"""
        if room_id not in self.chat_rooms:
            self.chat_rooms[room_id] = set()
        self.chat_rooms[room_id].add(user_id)
        logger.info(f"User {user_id} joined room {room_id}")
    
    def leave_room(self, room_id: str, user_id: int):
        """Remove user from chat room"""
        if room_id in self.chat_rooms:
            self.chat_rooms[room_id].discard(user_id)
            if not self.chat_rooms[room_id]:  # Remove empty rooms
                del self.chat_rooms[room_id]
        logger.info(f"User {user_id} left room {room_id}")
    
    def get_online_users(self) -> List[dict]:
        """Get list of online users"""
        return list(self.user_sessions.values())
    
    def get_room_participants(self, room_id: str) -> List[dict]:
        """Get participants in a chat room"""
        if room_id not in self.chat_rooms:
            return []
        
        participants = []
        for user_id in self.chat_rooms[room_id]:
            if user_id in self.user_sessions:
                participants.append(self.user_sessions[user_id])
        return participants

class ChatManager:
    """Manages chat operations and message handling"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
    
    async def handle_message(self, websocket: WebSocket, user_id: int, db: Session):
        """Handle incoming WebSocket messages"""
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Process different message types
                message_type = message_data.get("type")
                
                if message_type == "chat_message":
                    await self.handle_chat_message(message_data, user_id, db)
                elif message_type == "join_room":
                    await self.handle_join_room(message_data, user_id)
                elif message_type == "leave_room":
                    await self.handle_leave_room(message_data, user_id)
                elif message_type == "typing":
                    await self.handle_typing_indicator(message_data, user_id)
                elif message_type == "get_online_users":
                    await self.handle_get_online_users(user_id)
                elif message_type == "get_chat_history":
                    await self.handle_get_chat_history(message_data, user_id, db)
                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    
        except WebSocketDisconnect:
            self.connection_manager.disconnect(user_id)
            await self.connection_manager.broadcast_user_status(user_id, "offline")
        except Exception as e:
            logger.error(f"Error handling message from user {user_id}: {e}")
            self.connection_manager.disconnect(user_id)
    
    async def handle_chat_message(self, message_data: dict, sender_id: int, db: Session):
        """Handle chat message"""
        try:
            room_id = message_data.get("room_id")
            content = message_data.get("content", "").strip()
            message_type = message_data.get("message_type", "text")
            
            if not content or not room_id:
                return
            
            # Save message to database
            chat_message = crud.create_chat_message(db, {
                "room_id": room_id,
                "sender_id": sender_id,
                "content": content,
                "message_type": message_type,
                "timestamp": datetime.utcnow()
            })
            
            # Get sender info
            sender = crud.get_user(db, sender_id)
            
            # Prepare message for broadcast
            broadcast_message = {
                "type": "chat_message",
                "message_id": chat_message.id,
                "room_id": room_id,
                "sender_id": sender_id,
                "sender_name": sender.name if sender else "Unknown",
                "content": content,
                "message_type": message_type,
                "timestamp": chat_message.timestamp.isoformat()
            }
            
            # Broadcast to room participants
            await self.connection_manager.broadcast_to_room(
                room_id, 
                json.dumps(broadcast_message),
                exclude_user=sender_id
            )
            
            # Send confirmation to sender
            confirmation = {
                "type": "message_sent",
                "message_id": chat_message.id,
                "timestamp": chat_message.timestamp.isoformat()
            }
            await self.connection_manager.send_personal_message(
                json.dumps(confirmation), 
                sender_id
            )
            
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
    
    async def handle_join_room(self, message_data: dict, user_id: int):
        """Handle user joining a chat room"""
        room_id = message_data.get("room_id")
        if room_id:
            self.connection_manager.join_room(room_id, user_id)
            
            # Notify room participants
            join_message = {
                "type": "user_joined",
                "room_id": room_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.connection_manager.broadcast_to_room(
                room_id, 
                json.dumps(join_message),
                exclude_user=user_id
            )
    
    async def handle_leave_room(self, message_data: dict, user_id: int):
        """Handle user leaving a chat room"""
        room_id = message_data.get("room_id")
        if room_id:
            self.connection_manager.leave_room(room_id, user_id)
            
            # Notify room participants
            leave_message = {
                "type": "user_left",
                "room_id": room_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.connection_manager.broadcast_to_room(
                room_id, 
                json.dumps(leave_message)
            )
    
    async def handle_typing_indicator(self, message_data: dict, user_id: int):
        """Handle typing indicator"""
        room_id = message_data.get("room_id")
        is_typing = message_data.get("is_typing", False)
        
        if room_id:
            typing_message = {
                "type": "typing",
                "room_id": room_id,
                "user_id": user_id,
                "is_typing": is_typing,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.connection_manager.broadcast_to_room(
                room_id, 
                json.dumps(typing_message),
                exclude_user=user_id
            )
    
    async def handle_get_online_users(self, user_id: int):
        """Send list of online users"""
        online_users = self.connection_manager.get_online_users()
        response = {
            "type": "online_users",
            "users": online_users,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.connection_manager.send_personal_message(
            json.dumps(response), 
            user_id
        )
    
    async def handle_get_chat_history(self, message_data: dict, user_id: int, db: Session):
        """Send chat history for a room"""
        room_id = message_data.get("room_id")
        limit = message_data.get("limit", 50)
        offset = message_data.get("offset", 0)
        
        if room_id:
            # Get chat history from database
            messages = crud.get_chat_messages(db, room_id, limit, offset)
            
            # Format messages
            formatted_messages = []
            for msg in messages:
                sender = crud.get_user(db, msg.sender_id)
                formatted_messages.append({
                    "message_id": msg.id,
                    "sender_id": msg.sender_id,
                    "sender_name": sender.name if sender else "Unknown",
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "timestamp": msg.timestamp.isoformat()
                })
            
            response = {
                "type": "chat_history",
                "room_id": room_id,
                "messages": formatted_messages,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.connection_manager.send_personal_message(
                json.dumps(response), 
                user_id
            )

# Global chat manager instance
chat_manager = ChatManager()
