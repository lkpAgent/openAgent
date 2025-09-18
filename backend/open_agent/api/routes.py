"""Main API router."""

from fastapi import APIRouter
from .endpoints import chat


# TODO: Add other routers when implemented
from .endpoints import auth
from .endpoints import knowledge_base
from .endpoints import smart_query
from .endpoints import smart_chat

from .endpoints import database_config
from .endpoints import table_metadata

# System management endpoints
from .endpoints import departments
from .endpoints import roles
from .endpoints import resources
from .endpoints import llm_configs
from .endpoints import users
from .v1 import user_departments

# Create main API router
router = APIRouter()

router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

# Include sub-routers
router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"]
)



router.include_router(
    knowledge_base.router,
    prefix="/knowledge-bases",
    tags=["knowledge-bases"]
)

router.include_router(
    smart_query.router,
    tags=["smart-query"]
)

router.include_router(
    smart_chat.router,
    tags=["smart-chat"]
)





router.include_router(
    database_config.router,
    tags=["database-config"]
)

router.include_router(
    table_metadata.router,
    tags=["table-metadata"]
)

# System management routers
router.include_router(
    departments.router,
    prefix="/admin",
    tags=["admin-departments"]
)

router.include_router(
    roles.router,
    prefix="/admin",
    tags=["admin-roles"]
)

# 添加权限管理路由
router.include_router(
    roles.permission_router,
    prefix="/admin",
    tags=["admin-permissions"]
)

router.include_router(
    resources.router,
    prefix="/admin",
    tags=["admin-resources"]
)

router.include_router(
    llm_configs.router,
    prefix="/admin",
    tags=["admin-llm-configs"]
)

router.include_router(
    user_departments.router,
    prefix="/admin",
    tags=["admin-user-departments"]
)

router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

# Basic test endpoint
@router.get("/test")
async def test_endpoint():
    return {"message": "API test is working"}