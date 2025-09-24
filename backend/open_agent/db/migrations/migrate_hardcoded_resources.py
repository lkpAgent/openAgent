#!/usr/bin/env python3
"""Migration script to move hardcoded resources to database."""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from open_agent.core.config import settings
from open_agent.db.database import Base, get_db_session
from open_agent.models import *  # Import all models to ensure they're registered
from open_agent.utils.logger import get_logger
from open_agent.models.resource import Resource
from open_agent.models.permission import Role
from open_agent.models.resource import RoleResource

logger = get_logger(__name__)

def migrate_hardcoded_resources():
    """Migrate hardcoded resources from init_resource_data.py to database."""
    db = None
    try:
        # Get database session
        db = get_db_session()
        
        if db is None:
            logger.error("Failed to create database session")
            return False
        
        # Create all tables if they don't exist
        from open_agent.db.database import engine as global_engine
        if global_engine:
            Base.metadata.create_all(bind=global_engine)
        
        logger.info("Starting hardcoded resources migration...")
        
        # Check if resources already exist
        existing_count = db.query(Resource).count()
        if existing_count > 0:
            logger.info(f"Found {existing_count} existing resources. Checking role assignments.")
            # 即使资源已存在，也要检查并分配角色资源关联
            admin_role = db.query(Role).filter(Role.name == "系统管理员").first()
            if admin_role:
                # 获取所有资源
                all_resources = db.query(Resource).all()
                assigned_count = 0
                
                for resource in all_resources:
                    # 检查关联是否已存在
                    existing = db.query(RoleResource).filter(
                        RoleResource.role_id == admin_role.id,
                        RoleResource.resource_id == resource.id
                    ).first()
                    
                    if not existing:
                        role_resource = RoleResource(
                            role_id=admin_role.id,
                            resource_id=resource.id
                        )
                        db.add(role_resource)
                        assigned_count += 1
                
                if assigned_count > 0:
                    db.commit()
                    logger.info(f"已为系统管理员角色分配 {assigned_count} 个新资源")
                else:
                    logger.info("系统管理员角色已拥有所有资源")
            else:
                logger.warning("未找到系统管理员角色")
            
            return True
        
        # Define hardcoded resource data
        main_menu_data = [
            {
                "name": "智能问答",
                "code": "CHAT",
                "type": "menu",
                "path": "/chat",
                "component": "views/Chat.vue",
                "icon": "ChatDotRound",
                "description": "智能问答功能",
                "sort_order": 1,
                "requires_auth": True,
                "requires_admin": False
            },
            {
                "name": "智能问数",
                "code": "SMART_QUERY",
                "type": "menu",
                "path": "/smart-query",
                "component": "views/SmartQuery.vue",
                "icon": "DataAnalysis",
                "description": "智能问数功能",
                "sort_order": 2,
                "requires_auth": True,
                "requires_admin": False
            },
            {
                "name": "知识库",
                "code": "KNOWLEDGE",
                "type": "menu",
                "path": "/knowledge",
                "component": "views/KnowledgeBase.vue",
                "icon": "Collection",
                "description": "知识库管理",
                "sort_order": 3,
                "requires_auth": True,
                "requires_admin": False
            },
            {
                "name": "工作流编排",
                "code": "WORKFLOW",
                "type": "menu",
                "path": "/workflow",
                "component": "views/Workflow.vue",
                "icon": "Connection",
                "description": "工作流编排功能",
                "sort_order": 4,
                "requires_auth": True,
                "requires_admin": False
            },
            {
                "name": "智能体管理",
                "code": "AGENT",
                "type": "menu",
                "path": "/agent",
                "component": "views/Agent.vue",
                "icon": "User",
                "description": "智能体管理功能",
                "sort_order": 5,
                "requires_auth": True,
                "requires_admin": False
            },
            {
                "name": "系统管理",
                "code": "SYSTEM",
                "type": "menu",
                "path": "/system",
                "component": "views/SystemManagement.vue",
                "icon": "Setting",
                "description": "系统管理功能",
                "sort_order": 6,
                "requires_auth": True,
                "requires_admin": True
            }
        ]
        
        # Create main menu resources
        created_resources = {}
        for menu_data in main_menu_data:
            resource = Resource(**menu_data)
            db.add(resource)
            db.flush()
            created_resources[menu_data["code"]] = resource
            logger.info(f"Created main menu resource: {menu_data['name']}")
        
        # System management submenu data
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
                "icon": "Avatar",
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
                "name": "资源管理",
                "code": "SYSTEM_RESOURCES",
                "type": "menu",
                "path": "/system/resources",
                "component": "components/system/ResourceManagement.vue",
                "icon": "Grid",
                "description": "资源管理功能",
                "parent_id": created_resources["SYSTEM"].id,
                "sort_order": 5,
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
                "sort_order": 6,
                "requires_auth": True,
                "requires_admin": True
            }
        ]
        
        # Create system management submenu
        for submenu_data in system_submenu_data:
            submenu = Resource(**submenu_data)
            db.add(submenu)
            db.flush()
            created_resources[submenu_data["code"]] = submenu
            logger.info(f"Created system submenu resource: {submenu_data['name']}")
        
        # Button resources data
        button_resources_data = [
            # User management buttons
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
            # Role management buttons
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
            # Permission management buttons
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
            }
        ]
        
        # Create button resources
        for button_data in button_resources_data:
            button = Resource(**button_data)
            db.add(button)
            db.flush()
            created_resources[button_data["code"]] = button
            logger.info(f"Created button resource: {button_data['name']}")
        
        # API resources data
        api_resources_data = [
            # User management APIs
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
            # Role management APIs
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
            # Resource management APIs
            {
                "name": "资源列表API",
                "code": "RESOURCE_LIST_API",
                "type": "api",
                "path": "/api/admin/resources",
                "description": "获取资源列表API",
                "sort_order": 10,
                "requires_auth": True,
                "requires_admin": True
            },
            {
                "name": "创建资源API",
                "code": "RESOURCE_CREATE_API",
                "type": "api",
                "path": "/api/admin/resources",
                "description": "创建资源API",
                "sort_order": 11,
                "requires_auth": True,
                "requires_admin": True
            }
        ]
        
        # Create API resources
        for api_data in api_resources_data:
            api_resource = Resource(**api_data)
            db.add(api_resource)
            db.flush()
            created_resources[api_data["code"]] = api_resource
            logger.info(f"Created API resource: {api_data['name']}")
        
        # 分配资源给系统管理员角色
        admin_role = db.query(Role).filter(Role.name == "系统管理员").first()
        if admin_role:
            all_resources = list(created_resources.values())
            for resource in all_resources:
                # 检查关联是否已存在
                existing = db.query(RoleResource).filter(
                    RoleResource.role_id == admin_role.id,
                    RoleResource.resource_id == resource.id
                ).first()
                
                if not existing:
                    role_resource = RoleResource(
                        role_id=admin_role.id,
                        resource_id=resource.id
                    )
                    db.add(role_resource)
            
            logger.info(f"已为系统管理员角色分配 {len(all_resources)} 个资源")
        else:
            logger.warning("未找到系统管理员角色")
        
        db.commit()
        
        total_resources = db.query(Resource).count()
        logger.info(f"Migration completed successfully. Total resources: {total_resources}")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        if db:
            db.rollback()
        return False
    finally:
        if db:
            db.close()

def main():
    """Main function to run the migration."""
    print("=== 硬编码资源数据迁移 ===")
    success = migrate_hardcoded_resources()
    if success:
        print("\n🎉 资源数据迁移完成！")
    else:
        print("\n❌ 资源数据迁移失败！")

if __name__ == "__main__":
    main()