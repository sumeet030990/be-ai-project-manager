import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.repositories.role_repository import RoleRepository
from app.schemas.role import RoleResponse


class RoleService:
    def __init__(self, session: AsyncSession):
        self.repository = RoleRepository(session)

    async def list_roles(self) -> list[RoleResponse]:
        items, _ = await self.repository.get_all(skip=0, limit=1000)
        return [RoleResponse.model_validate(r) for r in items]

    async def get_role(self, role_id: uuid.UUID) -> RoleResponse:
        role = await self.repository.get_by_id(role_id)
        if not role:
            raise NotFoundException("Role", str(role_id))
        return RoleResponse.model_validate(role)
