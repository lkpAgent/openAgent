"""Initialize system management data."""

from sqlalchemy.orm import Session
from ..models.permission import Permission, Role
from ..models.department import Department
from ..models.user import User
from ..core.permissions import Permissions
from ..services.auth import AuthService
from ..utils.logger import get_logger
from .init_resource_data import init_resources

logger = get_logger(__name__)


def init_permissions(db: Session) -> None:
    """初始化系统权限."""
    permissions_data = [
        # 系统管理
        {"name": "系统管理", "code": Permissions.SYSTEM_ADMIN, "resource": "system", "action": "admin", "description": "系统管理员权限"},
        
        # 用户管理
        {"name": "创建用户", "code": Permissions.USER_CREATE, "resource": "user", "action": "create", "description": "创建新用户"},
        {"name": "查看用户", "code": Permissions.USER_READ, "resource": "user", "action": "read", "description": "查看用户信息"},
        {"name": "更新用户", "code": Permissions.USER_UPDATE, "resource": "user", "action": "update", "description": "更新用户信息"},
        {"name": "删除用户", "code": Permissions.USER_DELETE, "resource": "user", "action": "delete", "description": "删除用户"},
        {"name": "用户管理", "code": Permissions.USER_MANAGE, "resource": "user", "action": "manage", "description": "用户管理权限"},
        
        # 部门管理
        {"name": "创建部门", "code": Permissions.DEPT_CREATE, "resource": "department", "action": "create", "description": "创建新部门"},
        {"name": "查看部门", "code": Permissions.DEPT_READ, "resource": "department", "action": "read", "description": "查看部门信息"},
        {"name": "更新部门", "code": Permissions.DEPT_UPDATE, "resource": "department", "action": "update", "description": "更新部门信息"},
        {"name": "删除部门", "code": Permissions.DEPT_DELETE, "resource": "department", "action": "delete", "description": "删除部门"},
        {"name": "部门管理", "code": Permissions.DEPT_MANAGE, "resource": "department", "action": "manage", "description": "部门管理权限"},
        
        # 角色权限管理
        {"name": "创建角色", "code": Permissions.ROLE_CREATE, "resource": "role", "action": "create", "description": "创建新角色"},
        {"name": "查看角色", "code": Permissions.ROLE_READ, "resource": "role", "action": "read", "description": "查看角色信息"},
        {"name": "更新角色", "code": Permissions.ROLE_UPDATE, "resource": "role", "action": "update", "description": "更新角色信息"},
        {"name": "删除角色", "code": Permissions.ROLE_DELETE, "resource": "role", "action": "delete", "description": "删除角色"},
        {"name": "角色管理", "code": Permissions.ROLE_MANAGE, "resource": "role", "action": "manage", "description": "角色管理权限"},
        
        {"name": "查看权限", "code": Permissions.PERMISSION_READ, "resource": "permission", "action": "read", "description": "查看权限信息"},
        {"name": "创建权限", "code": Permissions.PERMISSION_CREATE, "resource": "permission", "action": "create", "description": "创建新权限"},
        {"name": "更新权限", "code": Permissions.PERMISSION_UPDATE, "resource": "permission", "action": "update", "description": "更新权限信息"},
        {"name": "删除权限", "code": Permissions.PERMISSION_DELETE, "resource": "permission", "action": "delete", "description": "删除权限"},
        {"name": "权限管理", "code": Permissions.PERMISSION_MANAGE, "resource": "permission", "action": "manage", "description": "权限管理权限"},
        {"name": "分配权限", "code": Permissions.PERMISSION_ASSIGN, "resource": "permission", "action": "assign", "description": "分配权限给角色或用户"},
        
        # 大模型管理
        {"name": "创建大模型配置", "code": Permissions.LLM_CONFIG_CREATE, "resource": "llm_config", "action": "create", "description": "创建大模型配置"},
        {"name": "查看大模型配置", "code": Permissions.LLM_CONFIG_READ, "resource": "llm_config", "action": "read", "description": "查看大模型配置"},
        {"name": "更新大模型配置", "code": Permissions.LLM_CONFIG_UPDATE, "resource": "llm_config", "action": "update", "description": "更新大模型配置"},
        {"name": "删除大模型配置", "code": Permissions.LLM_CONFIG_DELETE, "resource": "llm_config", "action": "delete", "description": "删除大模型配置"},
        {"name": "大模型管理", "code": Permissions.LLM_CONFIG_MANAGE, "resource": "llm_config", "action": "manage", "description": "大模型管理权限"},
        
        # 对话管理
        {"name": "创建对话", "code": Permissions.CHAT_CREATE, "resource": "chat", "action": "create", "description": "创建新对话"},
        {"name": "查看对话", "code": Permissions.CHAT_READ, "resource": "chat", "action": "read", "description": "查看对话记录"},
        {"name": "更新对话", "code": Permissions.CHAT_UPDATE, "resource": "chat", "action": "update", "description": "更新对话信息"},
        {"name": "删除对话", "code": Permissions.CHAT_DELETE, "resource": "chat", "action": "delete", "description": "删除对话记录"},
        
        # 知识库管理
        {"name": "创建知识库", "code": Permissions.KNOWLEDGE_CREATE, "resource": "knowledge", "action": "create", "description": "创建知识库"},
        {"name": "查看知识库", "code": Permissions.KNOWLEDGE_READ, "resource": "knowledge", "action": "read", "description": "查看知识库"},
        {"name": "更新知识库", "code": Permissions.KNOWLEDGE_UPDATE, "resource": "knowledge", "action": "update", "description": "更新知识库"},
        {"name": "删除知识库", "code": Permissions.KNOWLEDGE_DELETE, "resource": "knowledge", "action": "delete", "description": "删除知识库"},
        {"name": "知识库管理", "code": Permissions.KNOWLEDGE_MANAGE, "resource": "knowledge", "action": "manage", "description": "知识库管理权限"},
        
        # 智能查询
        {"name": "使用智能查询", "code": Permissions.SMART_QUERY_USE, "resource": "smart_query", "action": "use", "description": "使用智能查询功能"},
        {"name": "智能查询管理", "code": Permissions.SMART_QUERY_MANAGE, "resource": "smart_query", "action": "manage", "description": "智能查询管理权限"},
    ]
    
    for perm_data in permissions_data:
        # 检查权限是否已存在
        existing_perm = db.query(Permission).filter(
            Permission.code == perm_data["code"]
        ).first()
        
        if not existing_perm:
            permission = Permission(**perm_data)
            permission.set_audit_fields(1)  # 系统用户ID为1
            db.add(permission)
            logger.info(f"Created permission: {perm_data['name']} ({perm_data['code']})")
    
    db.commit()
    logger.info("Permissions initialization completed")


def init_roles(db: Session) -> None:
    """初始化系统角色."""
    roles_data = [
        {
            "name": "超级管理员",
            "code": "SUPER_ADMIN",
            "description": "系统超级管理员，拥有所有权限",
            "permissions": [  # 超级管理员拥有所有权限
                Permissions.SYSTEM_ADMIN,
                Permissions.USER_MANAGE,
                Permissions.DEPT_MANAGE,
                Permissions.ROLE_MANAGE,
                Permissions.PERMISSION_READ,
                Permissions.PERMISSION_ASSIGN,
                Permissions.LLM_CONFIG_MANAGE,
                Permissions.CHAT_CREATE,
                Permissions.CHAT_READ,
                Permissions.CHAT_UPDATE,
                Permissions.CHAT_DELETE,
                Permissions.KNOWLEDGE_READ,
                Permissions.SMART_QUERY_USE,
            ]
        },
        {
            "name": "系统管理员",
            "code": "ADMIN",
            "description": "系统管理员，负责用户、部门、权限管理",
            "permissions": [
                Permissions.SYSTEM_ADMIN,
                Permissions.USER_MANAGE,
                Permissions.DEPT_MANAGE,
                Permissions.ROLE_MANAGE,
                Permissions.PERMISSION_READ,
                Permissions.PERMISSION_ASSIGN,
                Permissions.LLM_CONFIG_MANAGE,
            ]
        },
        {
            "name": "部门管理员",
            "code": "DEPT_ADMIN",
            "description": "部门管理员，负责本部门用户管理",
            "permissions": [
                Permissions.USER_READ,
                Permissions.USER_UPDATE,
                Permissions.DEPT_READ,
                Permissions.ROLE_READ,
            ]
        },
        {
            "name": "普通用户",
            "code": "USER",
            "description": "普通用户，基础功能权限",
            "permissions": [
                Permissions.CHAT_CREATE,
                Permissions.CHAT_READ,
                Permissions.CHAT_UPDATE,
                Permissions.CHAT_DELETE,
                Permissions.KNOWLEDGE_READ,
                Permissions.SMART_QUERY_USE,
            ]
        },
        {
            "name": "访客",
            "code": "GUEST",
            "description": "访客用户，只读权限",
            "permissions": [
                Permissions.CHAT_READ,
                Permissions.KNOWLEDGE_READ,
            ]
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
            db.flush()  # 获取角色ID
            
            # 分配权限
            for perm_code in role_data["permissions"]:
                permission = db.query(Permission).filter(
                    Permission.code == perm_code
                ).first()
                if permission:
                    role.permissions.append(permission)
            
            logger.info(f"Created role: {role_data['name']} ({role_data['code']})")
    
    db.commit()
    logger.info("Roles initialization completed")


def init_departments(db: Session) -> None:
    """初始化默认部门."""
    departments_data = [
        {
            "name": "总公司",
            "code": "ROOT",
            "description": "公司总部",
            "parent_id": None,
            "sort_order": 1
        },
        {
            "name": "技术部",
            "code": "TECH",
            "description": "技术开发部门",
            "parent_code": "ROOT",
            "sort_order": 1
        },
        {
            "name": "产品部",
            "code": "PRODUCT",
            "description": "产品管理部门",
            "parent_code": "ROOT",
            "sort_order": 2
        },
        {
            "name": "运营部",
            "code": "OPERATION",
            "description": "运营管理部门",
            "parent_code": "ROOT",
            "sort_order": 3
        }
    ]
    
    # 先创建所有部门
    dept_map = {}
    for dept_data in departments_data:
        existing_dept = db.query(Department).filter(
            Department.code == dept_data["code"]
        ).first()
        
        if not existing_dept:
            department = Department(
                name=dept_data["name"],
                code=dept_data["code"],
                description=dept_data["description"],
                sort_order=dept_data["sort_order"]
            )
            department.set_audit_fields(1)
            db.add(department)
            db.flush()
            dept_map[dept_data["code"]] = department
            logger.info(f"Created department: {dept_data['name']} ({dept_data['code']})")
        else:
            dept_map[dept_data["code"]] = existing_dept
    
    # 设置父子关系
    for dept_data in departments_data:
        if "parent_code" in dept_data:
            child_dept = dept_map.get(dept_data["code"])
            parent_dept = dept_map.get(dept_data["parent_code"])
            if child_dept and parent_dept:
                child_dept.parent_id = parent_dept.id
    
    db.commit()
    logger.info("Departments initialization completed")


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
        # 初始化权限
        init_permissions(db)
        
        # 初始化角色
        init_roles(db)
        
        # 初始化部门
        init_departments(db)
        
        # 初始化资源
        init_resources(db)
        
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