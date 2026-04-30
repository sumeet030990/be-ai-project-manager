from sqlalchemy.ext.asyncio import AsyncSession

from database.models.role import Role
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    model = Role

    def __init__(self, session: AsyncSession):
        super().__init__(session)
