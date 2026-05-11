from fastapi import APIRouter

from routes.company import router as company_router
from routes.jira import router as jira_router
from routes.module import router as module_router
from routes.project import router as project_router
from routes.project_plugin import router as project_plugin_router
from routes.project_tech_stack import router as project_tech_stack_router
from routes.role import router as role_router
from routes.story import router as story_router
from routes.test_case import router as test_case_router
from routes.user import router as user_router

api_router = APIRouter()

api_router.include_router(role_router)
api_router.include_router(user_router)
api_router.include_router(company_router)
api_router.include_router(project_router)
api_router.include_router(project_tech_stack_router)
api_router.include_router(project_plugin_router)
api_router.include_router(module_router)
api_router.include_router(story_router)
api_router.include_router(test_case_router)
api_router.include_router(jira_router)
