from fastapi import APIRouter

from routes.company import router as company_router
from routes.project import router as project_router
from routes.role import router as role_router
from routes.user import router as user_router

api_router = APIRouter()

api_router.include_router(role_router)
api_router.include_router(user_router)
api_router.include_router(company_router)
api_router.include_router(project_router)
