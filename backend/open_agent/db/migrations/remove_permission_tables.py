"""删除权限相关表的迁移脚本

Revision ID: remove_permission_tables
Revises: add_system_management
Create Date: 2024-01-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'remove_permission_tables'
down_revision = 'add_system_management'
branch_labels = None
depends_on = None


def upgrade():
    """删除权限相关表."""
    
    # 获取数据库连接
    connection = op.get_bind()
    
    # 删除外键约束和表（按依赖关系顺序）
    tables_to_drop = [
        'user_permissions',      # 用户权限关联表
        'role_permissions',      # 角色权限关联表
        'permission_resources',  # 权限资源关联表
        'permissions',           # 权限表
        'role_resources',        # 角色资源关联表
        'resources',             # 资源表
        'user_departments',      # 用户部门关联表
        'departments'            # 部门表
    ]
    
    for table_name in tables_to_drop:
        try:
            # 检查表是否存在
            result = connection.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                );
            """))
            table_exists = result.scalar()
            
            if table_exists:
                print(f"删除表: {table_name}")
                op.drop_table(table_name)
            else:
                print(f"表 {table_name} 不存在，跳过")
                
        except Exception as e:
            print(f"删除表 {table_name} 时出错: {e}")
            # 继续删除其他表
            continue
    
    # 删除用户表中的部门相关字段
    try:
        # 检查字段是否存在
        result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'department_id';
        """))
        column_exists = result.fetchone()
        
        if column_exists:
            print("删除用户表中的 department_id 字段")
            op.drop_column('users', 'department_id')
        else:
            print("用户表中的 department_id 字段不存在，跳过")
            
    except Exception as e:
        print(f"删除 department_id 字段时出错: {e}")
    
    # 简化 user_roles 表结构（如果需要的话）
    try:
        # 检查 user_roles 表是否有多余的字段
        result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_roles' AND column_name IN ('id', 'created_at', 'updated_at', 'created_by', 'updated_by');
        """))
        extra_columns = [row[0] for row in result.fetchall()]
        
        if extra_columns:
            print("简化 user_roles 表结构")
            # 创建新的简化表
            op.execute(text("""
                CREATE TABLE user_roles_new (
                    user_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, role_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
                );
            """))
            
            # 迁移数据
            op.execute(text("""
                INSERT INTO user_roles_new (user_id, role_id)
                SELECT DISTINCT user_id, role_id FROM user_roles;
            """))
            
            # 删除旧表，重命名新表
            op.drop_table('user_roles')
            op.execute(text("ALTER TABLE user_roles_new RENAME TO user_roles;"))
            
    except Exception as e:
        print(f"简化 user_roles 表时出错: {e}")


def downgrade():
    """回滚操作 - 重新创建权限相关表."""
    
    # 注意：这是一个破坏性操作，回滚会丢失数据
    # 在生产环境中应该谨慎使用
    
    print("警告：回滚操作会重新创建权限相关表，但不会恢复数据")
    
    # 重新创建基本的权限表结构（简化版）
    op.create_table('permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    
    op.create_table('role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    
    # 添加用户表的 department_id 字段
    op.add_column('users', sa.Column('department_id', sa.Integer(), nullable=True))