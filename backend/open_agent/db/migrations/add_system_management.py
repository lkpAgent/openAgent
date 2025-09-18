"""Add system management tables.

Revision ID: add_system_management
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_system_management'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create system management tables."""
    
    # Create departments table
    op.create_table('departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_departments_name'), 'departments', ['name'], unique=False)
    op.create_index(op.f('ix_departments_parent_id'), 'departments', ['parent_id'], unique=False)
    
    # Create permissions table
    op.create_table('permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_permissions_category'), 'permissions', ['category'], unique=False)
    op.create_index(op.f('ix_permissions_name'), 'permissions', ['name'], unique=False)
    
    # Create roles table
    op.create_table('roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=False)
    
    # Create role_permissions table
    op.create_table('role_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission')
    )
    op.create_index(op.f('ix_role_permissions_permission_id'), 'role_permissions', ['permission_id'], unique=False)
    op.create_index(op.f('ix_role_permissions_role_id'), 'role_permissions', ['role_id'], unique=False)
    
    # Create user_roles table
    op.create_table('user_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_user_role')
    )
    op.create_index(op.f('ix_user_roles_role_id'), 'user_roles', ['role_id'], unique=False)
    op.create_index(op.f('ix_user_roles_user_id'), 'user_roles', ['user_id'], unique=False)
    
    # Create user_permissions table
    op.create_table('user_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'permission_id', name='uq_user_permission')
    )
    op.create_index(op.f('ix_user_permissions_permission_id'), 'user_permissions', ['permission_id'], unique=False)
    op.create_index(op.f('ix_user_permissions_user_id'), 'user_permissions', ['user_id'], unique=False)
    
    # Create llm_configs table
    op.create_table('llm_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('api_key', sa.Text(), nullable=True),
        sa.Column('api_base', sa.String(length=500), nullable=True),
        sa.Column('api_version', sa.String(length=20), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('top_p', sa.Float(), nullable=True),
        sa.Column('frequency_penalty', sa.Float(), nullable=True),
        sa.Column('presence_penalty', sa.Float(), nullable=True),
        sa.Column('timeout', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_llm_configs_name'), 'llm_configs', ['name'], unique=False)
    op.create_index(op.f('ix_llm_configs_provider'), 'llm_configs', ['provider'], unique=False)
    
    # Add new columns to users table
    op.add_column('users', sa.Column('department_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('is_superuser', sa.Boolean(), nullable=True, default=False))
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True, default=False))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('login_count', sa.Integer(), nullable=True, default=0))
    
    # Create foreign key constraint for department_id
    op.create_foreign_key('fk_users_department_id', 'users', 'departments', ['department_id'], ['id'])
    op.create_index(op.f('ix_users_department_id'), 'users', ['department_id'], unique=False)


def downgrade():
    """Drop system management tables."""
    
    # Drop foreign key and index for users.department_id
    op.drop_index(op.f('ix_users_department_id'), table_name='users')
    op.drop_constraint('fk_users_department_id', 'users', type_='foreignkey')
    
    # Drop new columns from users table
    op.drop_column('users', 'login_count')
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'is_admin')
    op.drop_column('users', 'is_superuser')
    op.drop_column('users', 'department_id')
    
    # Drop llm_configs table
    op.drop_index(op.f('ix_llm_configs_provider'), table_name='llm_configs')
    op.drop_index(op.f('ix_llm_configs_name'), table_name='llm_configs')
    op.drop_table('llm_configs')
    
    # Drop user_permissions table
    op.drop_index(op.f('ix_user_permissions_user_id'), table_name='user_permissions')
    op.drop_index(op.f('ix_user_permissions_permission_id'), table_name='user_permissions')
    op.drop_table('user_permissions')
    
    # Drop user_roles table
    op.drop_index(op.f('ix_user_roles_user_id'), table_name='user_roles')
    op.drop_index(op.f('ix_user_roles_role_id'), table_name='user_roles')
    op.drop_table('user_roles')
    
    # Drop role_permissions table
    op.drop_index(op.f('ix_role_permissions_role_id'), table_name='role_permissions')
    op.drop_index(op.f('ix_role_permissions_permission_id'), table_name='role_permissions')
    op.drop_table('role_permissions')
    
    # Drop roles table
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_table('roles')
    
    # Drop permissions table
    op.drop_index(op.f('ix_permissions_name'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_category'), table_name='permissions')
    op.drop_table('permissions')
    
    # Drop departments table
    op.drop_index(op.f('ix_departments_parent_id'), table_name='departments')
    op.drop_index(op.f('ix_departments_name'), table_name='departments')
    op.drop_table('departments')