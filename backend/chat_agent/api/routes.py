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
from . import knowledge_base

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

# router.include_router(
#     users.router,
#     prefix="/users",
#     tags=["users"]
# )

# Basic test endpoint
@router.get("/test")
async def test_endpoint():
    return {"message": "API test is working"}