import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.core.security import hash_password
from database.models.user import User
from app.repositories.company_repository import CompanyRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)
        self.role_repository = RoleRepository(session)
        self.company_repository = CompanyRepository(session)

    async def get_user(self, user_id: uuid.UUID) -> UserResponse:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundException("User", user_id)
        return UserResponse.model_validate(user)

    async def list_users(self, page: int, size: int) -> PaginatedResponse[UserResponse]:
        skip = (page - 1) * size
        items, total = await self.repository.get_all(skip=skip, limit=size)
        return PaginatedResponse(
            items=[UserResponse.model_validate(u) for u in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def create_user(self, payload: UserCreate) -> UserResponse:
        if await self.repository.get_by_email(payload.email):
            raise ConflictException(f"Email '{payload.email}' is already registered.")
        if await self.repository.get_by_contact_no(payload.contact_no):
            raise ConflictException(f"Contact number '{payload.contact_no}' is already registered.")
        if not await self.role_repository.get_by_id(payload.role_id):
            raise BadRequestException(f"Role '{payload.role_id}' does not exist.")
        if payload.company_id and not await self.company_repository.get_by_id(payload.company_id):
            raise BadRequestException(f"Company '{payload.company_id}' does not exist.")

        user = User(
            email=payload.email,
            contact_no=payload.contact_no,
            first_name=payload.first_name,
            middle_name=payload.middle_name,
            last_name=payload.last_name,
            dob=payload.dob,
            hashed_password=hash_password(payload.password),
            address_line_1=payload.address_line_1,
            address_line_2=payload.address_line_2,
            city=payload.city,
            state=payload.state,
            country=payload.country,
            pincode=payload.pincode,
            role_id=payload.role_id,
            company_id=payload.company_id,
        )
        user = await self.repository.create(user)
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: uuid.UUID, payload: UserUpdate) -> UserResponse:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundException("User", user_id)

        update_data = payload.model_dump(exclude_unset=True)

        if "role_id" in update_data and not await self.role_repository.get_by_id(update_data["role_id"]):
            raise BadRequestException(f"Role '{update_data['role_id']}' does not exist.")
        if "company_id" in update_data and update_data["company_id"] and \
                not await self.company_repository.get_by_id(update_data["company_id"]):
            raise BadRequestException(f"Company '{update_data['company_id']}' does not exist.")

        for field, value in update_data.items():
            setattr(user, field, value)

        user = await self.repository.update(user)
        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: uuid.UUID) -> None:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundException("User", user_id)
        await self.repository.delete(user)
