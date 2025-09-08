"""Main API router."""

from fastapi import APIRouter
from .endpoints import chat

# Create main API router
router = APIRouter()

# Include sub-routers
router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"]
)

# TODO: Add other routers when implemented
from .endpoints import auth
from .endpoints import knowledge_base
from .endpoints import smart_query
from .endpoints import smart_chat

from .endpoints import database_config
from .endpoints import table_metadata

router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
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

# router.include_router(
#     users.router,
#     prefix="/users",
#     tags=["users"]
# )

# Basic test endpoint
@router.get("/test")
async def test_endpoint():
    return {"message": "API test is working"}