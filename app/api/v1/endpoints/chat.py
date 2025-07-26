"""
Chat WebSocket endpoints for real-time communication
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import crud
from app.core.chat_manager import chat_manager
from app.core.security import get_current_active_user
from app.schemas.users import UserInDB
from app.core.firebase import verify_token
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time chat"""
    try:
        # Verify token and get user
        firebase_user = verify_token(token)
        if not firebase_user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Get user from database
        db_user = crud.get_user_by_firebase_uid(db, firebase_user.uid)
        if not db_user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Connect user to chat manager
        user_data = {
            "name": db_user.name,
            "email": db_user.email,
            "role": db_user.role.value if db_user.role else "user"
        }
        
        await chat_manager.connection_manager.connect(websocket, db_user.id, user_data)
        
        # Handle messages
        await chat_manager.handle_message(websocket, db_user.id, db)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

@router.post("/rooms")
async def create_chat_room(
    room_data: dict,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new chat room"""
    try:
        # Generate room ID if not provided
        if "id" not in room_data:
            room_data["id"] = str(uuid.uuid4())
        
        # Set creator
        room_data["created_by"] = current_user.id
        
        # Create room
        room = crud.create_chat_room(db, room_data)
        
        # Add creator as admin participant
        crud.add_chat_participant(db, room.id, current_user.id, "admin")
        
        return {
            "room_id": room.id,
            "name": room.name,
            "description": room.description,
            "room_type": room.room_type,
            "created_at": room.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating chat room: {e}")
        raise HTTPException(status_code=500, detail="Failed to create chat room")

@router.get("/rooms")
async def get_user_chat_rooms(
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all chat rooms for current user"""
    try:
        rooms = crud.get_user_chat_rooms(db, current_user.id)
        
        result = []
        for room in rooms:
            # Get participants count
            participants = crud.get_chat_participants(db, room.id)
            
            result.append({
                "room_id": room.id,
                "name": room.name,
                "description": room.description,
                "room_type": room.room_type,
                "reference_id": room.reference_id,
                "participants_count": len(participants),
                "created_at": room.created_at.isoformat(),
                "updated_at": room.updated_at.isoformat() if room.updated_at else None
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting user chat rooms: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat rooms")

@router.get("/rooms/{room_id}")
async def get_chat_room(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get chat room details"""
    try:
        room = crud.get_chat_room(db, room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Chat room not found")
        
        # Check if user is participant
        participants = crud.get_chat_participants(db, room_id)
        user_participant = next((p for p in participants if p.user_id == current_user.id), None)
        
        if not user_participant:
            raise HTTPException(status_code=403, detail="Access denied to this chat room")
        
        # Get participant details
        participant_details = []
        for participant in participants:
            user = crud.get_user(db, participant.user_id)
            if user:
                participant_details.append({
                    "user_id": user.id,
                    "name": user.name,
                    "role": participant.role,
                    "joined_at": participant.joined_at.isoformat(),
                    "last_read_at": participant.last_read_at.isoformat() if participant.last_read_at else None
                })
        
        return {
            "room_id": room.id,
            "name": room.name,
            "description": room.description,
            "room_type": room.room_type,
            "reference_id": room.reference_id,
            "participants": participant_details,
            "created_at": room.created_at.isoformat(),
            "updated_at": room.updated_at.isoformat() if room.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat room: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat room")

@router.post("/rooms/{room_id}/join")
async def join_chat_room(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Join a chat room"""
    try:
        room = crud.get_chat_room(db, room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Chat room not found")
        
        # Add user as participant
        participant = crud.add_chat_participant(db, room_id, current_user.id)
        
        return {
            "message": "Successfully joined chat room",
            "room_id": room_id,
            "joined_at": participant.joined_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error joining chat room: {e}")
        raise HTTPException(status_code=500, detail="Failed to join chat room")

@router.post("/rooms/{room_id}/leave")
async def leave_chat_room(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Leave a chat room"""
    try:
        room = crud.get_chat_room(db, room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Chat room not found")
        
        # Remove user from participants
        crud.remove_chat_participant(db, room_id, current_user.id)
        
        return {
            "message": "Successfully left chat room",
            "room_id": room_id
        }
        
    except Exception as e:
        logger.error(f"Error leaving chat room: {e}")
        raise HTTPException(status_code=500, detail="Failed to leave chat room")

@router.get("/rooms/{room_id}/messages")
async def get_chat_messages(
    room_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get chat messages for a room"""
    try:
        # Check if user is participant
        participants = crud.get_chat_participants(db, room_id)
        user_participant = next((p for p in participants if p.user_id == current_user.id), None)
        
        if not user_participant:
            raise HTTPException(status_code=403, detail="Access denied to this chat room")
        
        # Get messages
        messages = crud.get_chat_messages(db, room_id, limit, offset)
        
        # Format messages
        formatted_messages = []
        for msg in reversed(messages):  # Reverse to get chronological order
            sender = crud.get_user(db, msg.sender_id)
            formatted_messages.append({
                "message_id": msg.id,
                "sender_id": msg.sender_id,
                "sender_name": sender.name if sender else "Unknown",
                "content": msg.content,
                "message_type": msg.message_type,
                "file_url": msg.file_url,
                "is_edited": msg.is_edited,
                "timestamp": msg.timestamp.isoformat(),
                "edited_at": msg.edited_at.isoformat() if msg.edited_at else None
            })
        
        return {
            "room_id": room_id,
            "messages": formatted_messages,
            "total_count": len(messages),
            "has_more": len(messages) == limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat messages")

@router.post("/rooms/{room_id}/read")
async def mark_room_as_read(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Mark chat room as read for current user"""
    try:
        participant = crud.update_last_read(db, room_id, current_user.id)
        if not participant:
            raise HTTPException(status_code=404, detail="Participant not found")
        
        return {
            "message": "Chat room marked as read",
            "room_id": room_id,
            "last_read_at": participant.last_read_at.isoformat() if participant.last_read_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking room as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark room as read")

@router.get("/online-users")
async def get_online_users(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get list of currently online users"""
    try:
        online_users = chat_manager.connection_manager.get_online_users()
        return {
            "online_users": online_users,
            "count": len(online_users)
        }
        
    except Exception as e:
        logger.error(f"Error getting online users: {e}")
        raise HTTPException(status_code=500, detail="Failed to get online users")

@router.post("/rooms/property/{property_id}")
async def create_property_chat_room(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create or get chat room for a property"""
    try:
        # Check if property exists
        property_obj = crud.get_property(db, property_id)
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Check if room already exists
        room_id = f"property_{property_id}"
        existing_room = crud.get_chat_room(db, room_id)
        
        if existing_room:
            # Add user as participant if not already
            crud.add_chat_participant(db, room_id, current_user.id)
            return {
                "room_id": room_id,
                "name": existing_room.name,
                "message": "Joined existing property chat room"
            }
        
        # Create new room
        room_data = {
            "id": room_id,
            "name": f"Property: {property_obj.title}",
            "description": f"Chat room for property {property_obj.title}",
            "room_type": "property",
            "reference_id": property_id,
            "created_by": current_user.id
        }
        
        room = crud.create_chat_room(db, room_data)
        
        # Add creator and property owner as participants
        crud.add_chat_participant(db, room_id, current_user.id, "participant")
        if property_obj.owner_id != current_user.id:
            crud.add_chat_participant(db, room_id, property_obj.owner_id, "admin")
        
        return {
            "room_id": room_id,
            "name": room.name,
            "message": "Property chat room created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating property chat room: {e}")
        raise HTTPException(status_code=500, detail="Failed to create property chat room")
