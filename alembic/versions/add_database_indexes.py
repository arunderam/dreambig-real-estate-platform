"""Add database indexes for performance optimization

Revision ID: add_indexes_001
Revises: 
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_indexes_001'
down_revision = None
depends_on = None

def upgrade():
    """Add indexes for frequently queried columns"""
    
    # User table indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_phone', 'users', ['phone'])
    op.create_index('idx_users_firebase_uid', 'users', ['firebase_uid'])
    op.create_index('idx_users_role', 'users', ['role'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    op.create_index('idx_users_kyc_verified', 'users', ['kyc_verified'])
    
    # Property table indexes
    op.create_index('idx_properties_city', 'properties', ['city'])
    op.create_index('idx_properties_state', 'properties', ['state'])
    op.create_index('idx_properties_pincode', 'properties', ['pincode'])
    op.create_index('idx_properties_property_type', 'properties', ['property_type'])
    op.create_index('idx_properties_status', 'properties', ['status'])
    op.create_index('idx_properties_price', 'properties', ['price'])
    op.create_index('idx_properties_bhk', 'properties', ['bhk'])
    op.create_index('idx_properties_area', 'properties', ['area'])
    op.create_index('idx_properties_furnishing', 'properties', ['furnishing'])
    op.create_index('idx_properties_owner_id', 'properties', ['owner_id'])
    op.create_index('idx_properties_created_at', 'properties', ['created_at'])
    op.create_index('idx_properties_is_verified', 'properties', ['is_verified'])
    
    # Composite indexes for common queries
    op.create_index('idx_properties_city_type', 'properties', ['city', 'property_type'])
    op.create_index('idx_properties_city_price', 'properties', ['city', 'price'])
    op.create_index('idx_properties_type_status', 'properties', ['property_type', 'status'])
    op.create_index('idx_properties_price_bhk', 'properties', ['price', 'bhk'])
    op.create_index('idx_properties_location', 'properties', ['latitude', 'longitude'])
    
    # Investment table indexes
    op.create_index('idx_investments_investor_id', 'investments', ['investor_id'])
    op.create_index('idx_investments_property_id', 'investments', ['property_id'])
    op.create_index('idx_investments_risk_level', 'investments', ['risk_level'])
    op.create_index('idx_investments_created_at', 'investments', ['created_at'])
    
    # Service provider indexes
    op.create_index('idx_service_providers_service_type', 'service_providers', ['service_type'])
    op.create_index('idx_service_providers_is_verified', 'service_providers', ['is_verified'])
    op.create_index('idx_service_providers_city', 'service_providers', ['city'])
    
    # Service booking indexes
    op.create_index('idx_service_bookings_user_id', 'service_bookings', ['user_id'])
    op.create_index('idx_service_bookings_provider_id', 'service_bookings', ['service_provider_id'])
    op.create_index('idx_service_bookings_status', 'service_bookings', ['status'])
    op.create_index('idx_service_bookings_created_at', 'service_bookings', ['created_at'])
    
    # Favorites indexes
    op.create_index('idx_favorites_user_id', 'favorites', ['user_id'])
    op.create_index('idx_favorites_property_id', 'favorites', ['property_id'])
    op.create_index('idx_favorites_user_property', 'favorites', ['user_id', 'property_id'], unique=True)
    
    # Recently viewed indexes
    op.create_index('idx_recently_viewed_user_id', 'recently_viewed', ['user_id'])
    op.create_index('idx_recently_viewed_property_id', 'recently_viewed', ['property_id'])
    op.create_index('idx_recently_viewed_viewed_at', 'recently_viewed', ['viewed_at'])
    
    # Notification indexes
    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('idx_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('idx_notifications_created_at', 'notifications', ['created_at'])
    
    # Property media indexes
    op.create_index('idx_property_images_property_id', 'property_images', ['property_id'])
    op.create_index('idx_property_videos_property_id', 'property_videos', ['property_id'])
    op.create_index('idx_property_features_property_id', 'property_features', ['property_id'])
    op.create_index('idx_property_features_name', 'property_features', ['name'])

def downgrade():
    """Remove indexes"""
    
    # User table indexes
    op.drop_index('idx_users_email')
    op.drop_index('idx_users_phone')
    op.drop_index('idx_users_firebase_uid')
    op.drop_index('idx_users_role')
    op.drop_index('idx_users_created_at')
    op.drop_index('idx_users_kyc_verified')
    
    # Property table indexes
    op.drop_index('idx_properties_city')
    op.drop_index('idx_properties_state')
    op.drop_index('idx_properties_pincode')
    op.drop_index('idx_properties_property_type')
    op.drop_index('idx_properties_status')
    op.drop_index('idx_properties_price')
    op.drop_index('idx_properties_bhk')
    op.drop_index('idx_properties_area')
    op.drop_index('idx_properties_furnishing')
    op.drop_index('idx_properties_owner_id')
    op.drop_index('idx_properties_created_at')
    op.drop_index('idx_properties_is_verified')
    
    # Composite indexes
    op.drop_index('idx_properties_city_type')
    op.drop_index('idx_properties_city_price')
    op.drop_index('idx_properties_type_status')
    op.drop_index('idx_properties_price_bhk')
    op.drop_index('idx_properties_location')
    
    # Investment table indexes
    op.drop_index('idx_investments_investor_id')
    op.drop_index('idx_investments_property_id')
    op.drop_index('idx_investments_risk_level')
    op.drop_index('idx_investments_created_at')
    
    # Service provider indexes
    op.drop_index('idx_service_providers_service_type')
    op.drop_index('idx_service_providers_is_verified')
    op.drop_index('idx_service_providers_city')
    
    # Service booking indexes
    op.drop_index('idx_service_bookings_user_id')
    op.drop_index('idx_service_bookings_provider_id')
    op.drop_index('idx_service_bookings_status')
    op.drop_index('idx_service_bookings_created_at')
    
    # Favorites indexes
    op.drop_index('idx_favorites_user_id')
    op.drop_index('idx_favorites_property_id')
    op.drop_index('idx_favorites_user_property')
    
    # Recently viewed indexes
    op.drop_index('idx_recently_viewed_user_id')
    op.drop_index('idx_recently_viewed_property_id')
    op.drop_index('idx_recently_viewed_viewed_at')
    
    # Notification indexes
    op.drop_index('idx_notifications_user_id')
    op.drop_index('idx_notifications_is_read')
    op.drop_index('idx_notifications_created_at')
    
    # Property media indexes
    op.drop_index('idx_property_images_property_id')
    op.drop_index('idx_property_videos_property_id')
    op.drop_index('idx_property_features_property_id')
    op.drop_index('idx_property_features_name')
