import uuid

from fastapi import APIRouter

from app.controllers import role_controller
from app.core.dependencies import DBSession
from app.schemas.role import RoleResponse

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=list[RoleResponse])
async def list_roles(db: DBSession):
    return await role_controller.list_roles(db=db)


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(role_id: uuid.UUID, db: DBSession):
    return await role_controller.get_role(role_id=role_id, db=db)
