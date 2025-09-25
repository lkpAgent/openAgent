"""Initialize system management data."""

from sqlalchemy.orm import Session
from ..models.permission import Role
from ..models.user import User
from ..services.auth import AuthService
from ..utils.logger import get_logger

logger = get_logger(__name__)





def init_roles(db: Session) -> None:
    """初始化系统角色."""
    roles_data = [
        {
            "name": "超级管理员",
            "code": "SUPER_ADMIN",
            "description": "系统超级管理员，拥有所有权限"
        },
        {
            "name": "普通用户",
            "code": "USER",
            "description": "普通用户，基础功能权限"
        }
    ]
    
    for role_data in roles_data:
        # 检查角色是否已存在
        existing_role = db.query(Role).filter(
            Role.code == role_data["code"]
        ).first()
        
        if not existing_role:
            # 创建角色
            role = Role(
                name=role_data["name"],
                code=role_data["code"],
                description=role_data["description"]
            )
            role.set_audit_fields(1)  # 系统用户ID为1
            db.add(role)
            logger.info(f"Created role: {role_data['name']} ({role_data['code']})")
    
    db.commit()
    logger.info("Roles initialization completed")





def init_admin_user(db: Session) -> None:
    """初始化默认管理员用户."""
    logger.info("Starting admin user initialization...")
    
    # 检查是否已存在管理员用户
    existing_admin = db.query(User).filter(
        User.username == "admin"
    ).first()
    
    if existing_admin:
        logger.info("Admin user already exists")
        return
    
    # 创建管理员用户
    hashed_password = AuthService.get_password_hash("admin123")
    
    admin_user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=hashed_password,
        full_name="系统管理员",
        is_active=True
    )
    
    admin_user.set_audit_fields(1)
    db.add(admin_user)
    db.flush()
    
    # 分配超级管理员角色
    super_admin_role = db.query(Role).filter(
        Role.code == "SUPER_ADMIN"
    ).first()
    
    if super_admin_role:
        admin_user.roles.append(super_admin_role)
    
    db.commit()
    logger.info("Admin user created: admin / admin123")


def init_system_data(db: Session) -> None:
    """初始化所有系统数据."""
    logger.info("Starting system data initialization...")
    
    try:
        # 初始化角色
        init_roles(db)
        
        # 初始化管理员用户
        init_admin_user(db)
        
        logger.info("System data initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Error during system data initialization: {str(e)}")
        db.rollback()
        raise


if __name__ == "__main__":
    # 可以单独运行此脚本来初始化数据
    from ..db.database import SessionLocal
    
    db = SessionLocal()
    try:
        init_system_data(db)
    finally:
        db.close()