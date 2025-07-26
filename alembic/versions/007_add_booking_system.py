"""Add booking system tables

Revision ID: 007
Revises: 006
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    booking_type_enum = postgresql.ENUM(
        'viewing', 'rental_application', 'purchase_offer', 'inspection',
        name='bookingtype'
    )
    booking_type_enum.create(op.get_bind())

    booking_status_enum = postgresql.ENUM(
        'pending', 'confirmed', 'cancelled', 'completed', 'rejected',
        name='bookingstatus'
    )
    booking_status_enum.create(op.get_bind())

    application_status_enum = postgresql.ENUM(
        'submitted', 'under_review', 'approved', 'rejected', 'withdrawn',
        name='applicationstatus'
    )
    application_status_enum.create(op.get_bind())

    offer_status_enum = postgresql.ENUM(
        'submitted', 'under_review', 'accepted', 'rejected', 'counter_offered', 'withdrawn',
        name='offerstatus'
    )
    offer_status_enum.create(op.get_bind())

    # Create property_bookings table
    op.create_table(
        'property_bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_type', booking_type_enum, nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', booking_status_enum, nullable=False, default='pending'),
        sa.Column('preferred_date', sa.DateTime(), nullable=False),
        sa.Column('preferred_time', sa.String(5), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, default=60),
        sa.Column('confirmed_date', sa.DateTime(), nullable=True),
        sa.Column('completed_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('special_requirements', sa.String(500), nullable=True),
        sa.Column('contact_name', sa.String(100), nullable=False),
        sa.Column('contact_phone', sa.String(15), nullable=False),
        sa.Column('contact_email', sa.String(255), nullable=False),
        sa.Column('cancellation_reason', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_property_bookings_id', 'property_bookings', ['id'])
    op.create_index('ix_property_bookings_property_id', 'property_bookings', ['property_id'])
    op.create_index('ix_property_bookings_user_id', 'property_bookings', ['user_id'])
    op.create_index('ix_property_bookings_status', 'property_bookings', ['status'])
    op.create_index('ix_property_bookings_preferred_date', 'property_bookings', ['preferred_date'])

    # Create rental_applications table
    op.create_table(
        'rental_applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('applicant_id', sa.Integer(), nullable=False),
        sa.Column('status', application_status_enum, nullable=False, default='submitted'),
        sa.Column('desired_move_in_date', sa.DateTime(), nullable=False),
        sa.Column('lease_duration_months', sa.Integer(), nullable=False),
        sa.Column('offered_rent', sa.Float(), nullable=False),
        sa.Column('security_deposit', sa.Float(), nullable=False),
        sa.Column('employment_status', sa.String(100), nullable=False),
        sa.Column('employer_name', sa.String(200), nullable=True),
        sa.Column('monthly_income', sa.Float(), nullable=False),
        sa.Column('previous_address', sa.String(500), nullable=True),
        sa.Column('references', sa.JSON(), nullable=True),
        sa.Column('documents', sa.JSON(), nullable=True),
        sa.Column('background_check_consent', sa.Boolean(), nullable=False, default=False),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['applicant_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_rental_applications_id', 'rental_applications', ['id'])
    op.create_index('ix_rental_applications_property_id', 'rental_applications', ['property_id'])
    op.create_index('ix_rental_applications_applicant_id', 'rental_applications', ['applicant_id'])
    op.create_index('ix_rental_applications_status', 'rental_applications', ['status'])

    # Create purchase_offers table
    op.create_table(
        'purchase_offers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('buyer_id', sa.Integer(), nullable=False),
        sa.Column('status', offer_status_enum, nullable=False, default='submitted'),
        sa.Column('offered_price', sa.Float(), nullable=False),
        sa.Column('financing_type', sa.String(20), nullable=False),
        sa.Column('down_payment', sa.Float(), nullable=False),
        sa.Column('loan_amount', sa.Float(), nullable=False, default=0),
        sa.Column('contingencies', sa.JSON(), nullable=True),
        sa.Column('closing_date', sa.DateTime(), nullable=False),
        sa.Column('inspection_period_days', sa.Integer(), nullable=False, default=7),
        sa.Column('financing_contingency_days', sa.Integer(), nullable=False, default=30),
        sa.Column('earnest_money', sa.Float(), nullable=False),
        sa.Column('additional_terms', sa.Text(), nullable=True),
        sa.Column('expiration_date', sa.DateTime(), nullable=False),
        sa.Column('counter_offer_price', sa.Float(), nullable=True),
        sa.Column('counter_offer_terms', sa.Text(), nullable=True),
        sa.Column('counter_offer_date', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_purchase_offers_id', 'purchase_offers', ['id'])
    op.create_index('ix_purchase_offers_property_id', 'purchase_offers', ['property_id'])
    op.create_index('ix_purchase_offers_buyer_id', 'purchase_offers', ['buyer_id'])
    op.create_index('ix_purchase_offers_status', 'purchase_offers', ['status'])
    op.create_index('ix_purchase_offers_expiration_date', 'purchase_offers', ['expiration_date'])


def downgrade():
    # Drop tables
    op.drop_table('purchase_offers')
    op.drop_table('rental_applications')
    op.drop_table('property_bookings')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS offerstatus')
    op.execute('DROP TYPE IF EXISTS applicationstatus')
    op.execute('DROP TYPE IF EXISTS bookingstatus')
    op.execute('DROP TYPE IF EXISTS bookingtype')
