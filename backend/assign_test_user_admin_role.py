#!/usr/bin/env python3
"""为测试用户分配管理员角色的脚本"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from open_agent.db.database import get_db_session
from open_agent.models.user import User
from open_agent.models.permission import Role, UserRole
from open_agent.utils.logger import get_logger

logger = get_logger(__name__)

def assign_admin_role_to_test_user():
    """为测试用户分配管理员角色"""
    db = get_db_session()
    try:
        # 查找测试用户
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            print("❌ 测试用户 test@example.com 不存在")
            return False
        
        # 查找管理员角色
        admin_role = db.query(Role).filter(Role.code == "ADMIN").first()
        if not admin_role:
            print("❌ 管理员角色 ADMIN 不存在")
            return False
        
        # 检查是否已经有该角色
        existing_user_role = db.query(UserRole).filter(
            UserRole.user_id == test_user.id,
            UserRole.role_id == admin_role.id
        ).first()
        
        if existing_user_role:
            print(f"✅ 用户 {test_user.email} 已经拥有管理员角色")
            return True
        
        # 分配管理员角色
        user_role = UserRole(
            user_id=test_user.id,
            role_id=admin_role.id
        )
        user_role.set_audit_fields(1)  # 系统用户ID
        db.add(user_role)
        db.commit()
        
        print(f"✅ 成功为用户 {test_user.email} 分配管理员角色")
        
        # 验证角色分配
        db.refresh(test_user)
        user_roles = [role.code for role in test_user.roles]
        print(f"用户当前角色: {user_roles}")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 分配角色失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=== 为测试用户分配管理员角色 ===")
    success = assign_admin_role_to_test_user()
    if success:
        print("\n🎉 角色分配完成！现在测试用户应该可以访问权限管理 API 了。")
    else:
        print("\n❌ 角色分配失败！")