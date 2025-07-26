from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    properties,
    investments,
    search,
    services,
    # documents,
    chat,
    bookings,
    legal,
    i18n
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
api_router.include_router(investments.router, prefix="/investments", tags=["investments"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
# api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
api_router.include_router(legal.router, prefix="/legal", tags=["legal"])
api_router.include_router(i18n.router, prefix="/i18n", tags=["internationalization"])