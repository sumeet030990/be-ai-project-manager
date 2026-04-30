import uuid

from app.core.dependencies import DBSession
from app.schemas.role import RoleResponse
from app.services.role_service import RoleService


async def list_roles(db: DBSession) -> list[RoleResponse]:
    return await RoleService(db).list_roles()


async def get_role(role_id: uuid.UUID, db: DBSession) -> RoleResponse:
    return await RoleService(db).get_role(role_id)
