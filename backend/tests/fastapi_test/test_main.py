import pytest
from fastapi.testclient import TestClient
from main import app, current_user_ctx, UserService
from contextvars import ContextVar

client = TestClient(app)


def test_read_users_me_with_valid_token():
    """测试有效令牌获取用户信息"""
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer valid_token_123"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == 123
    assert response.json()["username"] == "john_doe"


def test_read_users_me_with_invalid_token():
    """测试无效令牌"""
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_create_task_with_user_context():
    """测试创建任务时用户上下文是否正确"""
    response = client.post(
        "/tasks",
        json={"title": "Test task", "description": "Test description"},
        headers={"Authorization": "Bearer valid_token_123"}
    )
    assert response.status_code == 200
    # 检查响应中是否包含正确的用户ID
    assert response.json()["task"]["created_by"] == 123


def test_get_tasks_with_different_users():
    """测试不同用户获取任务"""
    # 用户1
    response1 = client.get(
        "/tasks",
        headers={"Authorization": "Bearer valid_token_123"}
    )
    assert response1.status_code == 200
    # 这里应该只返回用户1的任务

    # 用户2
    response2 = client.get(
        "/tasks",
        headers={"Authorization": "Bearer valid_token_456"}
    )
    assert response2.status_code == 200
    # 这里应该只返回用户2的任务


def test_context_outside_request():
    """测试在请求上下文外获取用户（应该失败）"""
    try:
        UserService.get_current_user()
        assert False, "Should have raised an exception"
    except RuntimeError as e:
        assert "No current user available" in str(e)


# 手动设置上下文进行测试
def test_user_service_with_manual_context():
    """测试手动设置上下文后获取用户"""
    test_user = {"id": 999, "username": "test_user"}
    token = current_user_ctx.set(test_user)

    try:
        user_id = UserService.get_current_user_id()
        assert user_id == 999

        user = UserService.get_current_user()
        assert user["username"] == "test_user"
    finally:
        current_user_ctx.reset(token)


if __name__ == "__main__":
    # pytest.main([__file__, "-v"])
    test_read_users_me_with_valid_token()
    test_read_users_me_with_invalid_token()
    test_create_task_with_user_context()
    test_get_tasks_with_different_users()
    test_context_outside_request()
    test_user_service_with_manual_context()
