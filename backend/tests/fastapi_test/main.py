from contextvars import ContextVar
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
import uuid
import uvicorn

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 创建上下文变量存储当前用户和请求ID
current_user_ctx: ContextVar[dict] = ContextVar("current_user", default=None)
request_id_ctx: ContextVar[str] = ContextVar("request_id", default=None)


# 用户模型
class User(BaseModel):
    id: int
    username: str
    email: Optional[str] = None


# 模拟用户服务
class UserService:
    @staticmethod
    def get_current_user_id() -> int:
        """在service中直接获取当前用户ID"""
        user = current_user_ctx.get()
        if not user:
            raise RuntimeError("No current user available")
        return user["id"]

    @staticmethod
    def get_current_user() -> dict:
        """获取完整的当前用户信息"""
        user = current_user_ctx.get()
        if not user:
            raise RuntimeError("No current user available")
        return user


# 业务服务示例
class TaskService:
    def create_task(self, task_data: dict):
        """创建任务时自动添加当前用户ID"""
        current_user_id = UserService.get_current_user_id()

        # 这里模拟数据库操作
        task = {
            **task_data,
            "created_by": current_user_id,
            "created_at": "2023-10-01 12:00:00"
        }

        print(f"Task created by user {current_user_id}: {task}")
        return task

    def get_user_tasks(self):
        """获取当前用户的任务"""
        user = current_user_ctx.get()
        current_user_id = UserService.get_current_user_id()

        # 模拟根据用户ID查询任务
        return [{"id": 1, "title": "Sample task", "user_id": current_user_id}]


# 中间件：设置上下文
@app.middleware("http")
async def set_context_vars(request: Request, call_next):
    # 为每个请求生成唯一ID
    request_id = str(uuid.uuid4())
    request_id_token = request_id_ctx.set(request_id)

    # 尝试提取用户信息
    user_token = None
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            user = await decode_token_and_get_user(token)  # 您的认证逻辑
            user_token = current_user_ctx.set(user)

        response = await call_next(request)
        return response
    finally:
        # 清理上下文
        request_id_ctx.reset(request_id_token)
        if user_token:
            current_user_ctx.reset(user_token)


# 模拟认证函数
async def decode_token_and_get_user(token: str) -> dict:
    # 这里应该是您的实际认证逻辑，例如JWT解码或数据库查询
    # 简单模拟：根据token返回用户信息
    if token == "valid_token_123":
        return {"id": 123, "username": "john_doe", "email": "john@example.com"}
    elif token == "valid_token_456":
        return {"id": 456, "username": "jane_doe", "email": "jane@example.com"}
    else:
        return None


# 依赖项：用于路由层认证
async def get_current_user_route(token: str = Depends(oauth2_scheme)) -> dict:
    """路由层的用户认证"""
    user = await decode_token_and_get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user


# 路由处理函数
@app.post("/tasks")
async def create_task(
        task_data: dict,
        current_user: dict = Depends(get_current_user_route)
):
    """创建任务"""
    # 不需要显式传递user_id到service！
    task_service = TaskService()
    task = task_service.create_task(task_data)
    return {"task": task, "message": "Task created successfully"}


@app.get("/tasks")
async def get_tasks(current_user: dict = Depends(get_current_user_route)):
    """获取当前用户的任务"""
    task_service = TaskService()
    tasks = task_service.get_user_tasks()
    return {"tasks": tasks}


@app.get("/users/me")
async def read_users_me(current_user: dict = Depends(get_current_user_route)):
    """获取当前用户信息"""
    return current_user


# 测试端点 - 直接在路由中获取上下文用户
@app.get("/test-context")
async def test_context():
    """测试直接通过上下文获取用户（不通过依赖注入）"""
    try:
        user = UserService.get_current_user()
        return {"message": "Successfully got user from context", "user": user}
    except RuntimeError as e:
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)