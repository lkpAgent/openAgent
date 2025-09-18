"""Initialize resource data for the system."""

from sqlalchemy.orm import Session
from ..models.resource import Resource
from ..utils.logger import get_logger

logger = get_logger(__name__)


def init_resources(db: Session):
    """初始化系统资源数据."""
    try:
        # 检查是否已有资源数据
        existing_count = db.query(Resource).count()
        if existing_count > 0:
            logger.info("Resources already initialized, skipping...")
            return
        
        # 定义资源数据
        resources_data = [
            # 主菜单
            {
                "name": "智能问答",
                "code": "CHAT",
                "type": "menu",
                "path": "/chat",
                "component": "views/Chat.vue",
                "icon": "ChatDotRound",
                "description": "智能对话功能",
                "sort_order": 1,
                "requires_auth": True,
                "requires_admin": False
            },
            {
                "name": "智能问数",
                "code": "SMART_QUERY",
                "type": "menu",
                "path": "/smart-query",
                "component": "components/SmartQuery.vue",
                "icon": "DataAnalysis",
                "description": "智能数据查询功能",
                "sort_order": 2,
                "requires_auth": True,
                "requires_admin": False
            },
            {
                "name": "智能创作",
                "code": "CREATION",
                "type": "menu",
                "path": "/creation",
                "component": "components/CreativeStudio.vue",
                "icon": "EditPen",
                "description": "智能内容创作功能",
                "sort_order": 3,
                "requires_auth": True,
                "requires_admin": False
            },
            {
                "name": "知识库",
                "code": "KNOWLEDGE",
                "type": "menu",
                "path": "/knowledge",
                "component": "components/KnowledgeManagement.vue",
                "icon": "Collection",
                "description": "知识库管理功能",
                "sort_order": 4,
                "requires_auth": True,
                "requires_admin": False
            },
            {
                "name": "工作流编排",
                "code": "WORKFLOW",
                "type": "menu",
                "path": "/workflow",
                "component": "components/WorkflowEditor.vue",
                "icon": "Connection",
                "description": "工作流编排功能",
                "sort_order": 5,
                "requires_auth": True,
                "requires_admin": False
            },
            {
                "name": "智能体管理",
                "code": "AGENT",
                "type": "menu",
                "path": "/agent",
                "component": "components/AgentManagement.vue",
                "icon": "User",
                "description": "智能体管理功能",
                "sort_order": 6,
                "requires_auth": True,
                "requires_admin": False
            },
            {
                "name": "个人资料",
                "code": "PROFILE",
                "type": "menu",
                "path": "/profile",
                "component": "views/Profile.vue",
                "icon": "User",
                "description": "个人资料管理",
                "sort_order": 7,
                "requires_auth": True,
                "requires_admin": False
            },
            # 系统管理主菜单
            {
                "name": "系统管理",
                "code": "SYSTEM",
                "type": "menu",
                "path": "/system",
                "component": "views/SystemManagement.vue",
                "icon": "Setting",
                "description": "系统管理功能",
                "sort_order": 8,
                "requires_auth": True,
                "requires_admin": True
            }
        ]
        
        # 创建主菜单资源
        created_resources = {}
        for resource_data in resources_data:
            resource = Resource(**resource_data)
            db.add(resource)
            db.flush()  # 获取ID
            created_resources[resource_data["code"]] = resource
        
        # 系统管理子菜单
        system_submenu_data = [
            {
                "name": "用户管理",
                "code": "SYSTEM_USERS",
                "type": "menu",
                "path": "/system/users",
                "component": "components/system/UserManagement.vue",
                "icon": "User",
                "description": "用户管理功能",
                "parent_id": created_resources["SYSTEM"].id,
                "sort_order": 1,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "部门管理",
                "code": "SYSTEM_DEPARTMENTS",
                "type": "menu",
                "path": "/system/departments",
                "component": "components/system/DepartmentManagement.vue",
                "icon": "OfficeBuilding",
                "description": "部门管理功能",
                "parent_id": created_resources["SYSTEM"].id,
                "sort_order": 2,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "角色管理",
                "code": "SYSTEM_ROLES",
                "type": "menu",
                "path": "/system/roles",
                "component": "components/system/RoleManagement.vue",
                "icon": "UserFilled",
                "description": "角色管理功能",
                "parent_id": created_resources["SYSTEM"].id,
                "sort_order": 3,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "权限管理",
                "code": "SYSTEM_PERMISSIONS",
                "type": "menu",
                "path": "/system/permissions",
                "component": "components/system/PermissionManagement.vue",
                "icon": "Lock",
                "description": "权限管理功能",
                "parent_id": created_resources["SYSTEM"].id,
                "sort_order": 4,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "大模型管理",
                "code": "SYSTEM_LLM_CONFIGS",
                "type": "menu",
                "path": "/system/llm-configs",
                "component": "components/system/LLMConfigManagement.vue",
                "icon": "Cpu",
                "description": "大模型配置管理",
                "parent_id": created_resources["SYSTEM"].id,
                "sort_order": 5,
                "requires_auth": True,
                "requires_admin": True
            }
        ]
        
        # 创建系统管理子菜单
        for submenu_data in system_submenu_data:
            submenu = Resource(**submenu_data)
            db.add(submenu)
            db.flush()
            created_resources[submenu_data["code"]] = submenu
        
        # 功能按钮资源
        button_resources_data = [
            # 用户管理按钮
            {
                "name": "新增用户",
                "code": "USER_CREATE_BTN",
                "type": "button",
                "description": "新增用户按钮",
                "parent_id": created_resources["SYSTEM_USERS"].id,
                "sort_order": 1,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "编辑用户",
                "code": "USER_EDIT_BTN",
                "type": "button",
                "description": "编辑用户按钮",
                "parent_id": created_resources["SYSTEM_USERS"].id,
                "sort_order": 2,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "删除用户",
                "code": "USER_DELETE_BTN",
                "type": "button",
                "description": "删除用户按钮",
                "parent_id": created_resources["SYSTEM_USERS"].id,
                "sort_order": 3,
                "requires_auth": True,
                "requires_admin": True
            },
            # 角色管理按钮
            {
                "name": "新增角色",
                "code": "ROLE_CREATE_BTN",
                "type": "button",
                "description": "新增角色按钮",
                "parent_id": created_resources["SYSTEM_ROLES"].id,
                "sort_order": 1,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "编辑角色",
                "code": "ROLE_EDIT_BTN",
                "type": "button",
                "description": "编辑角色按钮",
                "parent_id": created_resources["SYSTEM_ROLES"].id,
                "sort_order": 2,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "删除角色",
                "code": "ROLE_DELETE_BTN",
                "type": "button",
                "description": "删除角色按钮",
                "parent_id": created_resources["SYSTEM_ROLES"].id,
                "sort_order": 3,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "权限配置",
                "code": "ROLE_PERMISSION_BTN",
                "type": "button",
                "description": "角色权限配置按钮",
                "parent_id": created_resources["SYSTEM_ROLES"].id,
                "sort_order": 4,
                "requires_auth": True,
                "requires_admin": True
            },
            # 权限管理按钮
            {
                "name": "新增权限",
                "code": "PERMISSION_CREATE_BTN",
                "type": "button",
                "description": "新增权限按钮",
                "parent_id": created_resources["SYSTEM_PERMISSIONS"].id,
                "sort_order": 1,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "编辑权限",
                "code": "PERMISSION_EDIT_BTN",
                "type": "button",
                "description": "编辑权限按钮",
                "parent_id": created_resources["SYSTEM_PERMISSIONS"].id,
                "sort_order": 2,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "删除权限",
                "code": "PERMISSION_DELETE_BTN",
                "type": "button",
                "description": "删除权限按钮",
                "parent_id": created_resources["SYSTEM_PERMISSIONS"].id,
                "sort_order": 3,
                "requires_auth": True,
                "requires_admin": True
            }
        ]
        
        # 创建按钮资源
        for button_data in button_resources_data:
            button = Resource(**button_data)
            db.add(button)
        
        # API资源
        api_resources_data = [
            # 用户管理API
            {
                "name": "用户列表API",
                "code": "USER_LIST_API",
                "type": "api",
                "path": "/api/users",
                "description": "获取用户列表API",
                "sort_order": 1,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "创建用户API",
                "code": "USER_CREATE_API",
                "type": "api",
                "path": "/api/users",
                "description": "创建用户API",
                "sort_order": 2,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "更新用户API",
                "code": "USER_UPDATE_API",
                "type": "api",
                "path": "/api/users/{id}",
                "description": "更新用户API",
                "sort_order": 3,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "删除用户API",
                "code": "USER_DELETE_API",
                "type": "api",
                "path": "/api/users/{id}",
                "description": "删除用户API",
                "sort_order": 4,
                "requires_auth": True,
                "requires_admin": True
            },
            # 角色管理API
            {
                "name": "角色列表API",
                "code": "ROLE_LIST_API",
                "type": "api",
                "path": "/api/admin/roles",
                "description": "获取角色列表API",
                "sort_order": 5,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "创建角色API",
                "code": "ROLE_CREATE_API",
                "type": "api",
                "path": "/api/admin/roles",
                "description": "创建角色API",
                "sort_order": 6,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "更新角色API",
                "code": "ROLE_UPDATE_API",
                "type": "api",
                "path": "/api/admin/roles/{id}",
                "description": "更新角色API",
                "sort_order": 7,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "删除角色API",
                "code": "ROLE_DELETE_API",
                "type": "api",
                "path": "/api/admin/roles/{id}",
                "description": "删除角色API",
                "sort_order": 8,
                "requires_auth": True,
                "requires_admin": True
            },
            # 权限管理API
            {
                "name": "权限列表API",
                "code": "PERMISSION_LIST_API",
                "type": "api",
                "path": "/api/admin/roles/permissions",
                "description": "获取权限列表API",
                "sort_order": 9,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "创建权限API",
                "code": "PERMISSION_CREATE_API",
                "type": "api",
                "path": "/api/admin/roles/permissions",
                "description": "创建权限API",
                "sort_order": 10,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "更新权限API",
                "code": "PERMISSION_UPDATE_API",
                "type": "api",
                "path": "/api/admin/roles/permissions/{id}",
                "description": "更新权限API",
                "sort_order": 11,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "删除权限API",
                "code": "PERMISSION_DELETE_API",
                "type": "api",
                "path": "/api/admin/roles/permissions/{id}",
                "description": "删除权限API",
                "sort_order": 12,
                "requires_auth": True,
                "requires_admin": True
            }
        ]
        
        # 创建API资源
        for api_data in api_resources_data:
            api_resource = Resource(**api_data)
            db.add(api_resource)
        
        db.commit()
        logger.info("Resources initialized successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing resources: {str(e)}")
        raise