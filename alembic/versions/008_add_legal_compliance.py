"""Add legal compliance models

Revision ID: 008_add_legal_compliance
Revises: 007_add_booking_system
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_add_legal_compliance'
down_revision = '007_add_booking_system'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_consents table
    op.create_table('user_consents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('consent_type', sa.String(length=50), nullable=True),
        sa.Column('consent_given', sa.Boolean(), nullable=True),
        sa.Column('consent_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('consent_version', sa.String(length=20), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('consent_text', sa.Text(), nullable=True),
        sa.Column('withdrawn_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_consents_id'), 'user_consents', ['id'], unique=False)

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=True),
        sa.Column('event_timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('archived', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)

    # Create legal_documents table
    op.create_table('legal_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('effective_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_legal_documents_id'), 'legal_documents', ['id'], unique=False)

    # Create indexes for better performance
    op.create_index('ix_user_consents_user_id', 'user_consents', ['user_id'], unique=False)
    op.create_index('ix_user_consents_consent_type', 'user_consents', ['consent_type'], unique=False)
    op.create_index('ix_user_consents_consent_date', 'user_consents', ['consent_date'], unique=False)
    
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'], unique=False)
    op.create_index('ix_audit_logs_event_type', 'audit_logs', ['event_type'], unique=False)
    op.create_index('ix_audit_logs_event_timestamp', 'audit_logs', ['event_timestamp'], unique=False)
    op.create_index('ix_audit_logs_archived', 'audit_logs', ['archived'], unique=False)
    
    op.create_index('ix_legal_documents_document_type', 'legal_documents', ['document_type'], unique=False)
    op.create_index('ix_legal_documents_is_active', 'legal_documents', ['is_active'], unique=False)
    op.create_index('ix_legal_documents_effective_date', 'legal_documents', ['effective_date'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('ix_legal_documents_effective_date', table_name='legal_documents')
    op.drop_index('ix_legal_documents_is_active', table_name='legal_documents')
    op.drop_index('ix_legal_documents_document_type', table_name='legal_documents')
    
    op.drop_index('ix_audit_logs_archived', table_name='audit_logs')
    op.drop_index('ix_audit_logs_event_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_event_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    
    op.drop_index('ix_user_consents_consent_date', table_name='user_consents')
    op.drop_index('ix_user_consents_consent_type', table_name='user_consents')
    op.drop_index('ix_user_consents_user_id', table_name='user_consents')

    # Drop tables
    op.drop_index(op.f('ix_legal_documents_id'), table_name='legal_documents')
    op.drop_table('legal_documents')
    
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index(op.f('ix_user_consents_id'), table_name='user_consents')
    op.drop_table('user_consents')
