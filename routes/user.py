import uuid

from fastapi import APIRouter, Query, status
from fastapi.responses import Response

from app.controllers import user_controller
from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    return await user_controller.list_users(page=page, size=size, db=db)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: uuid.UUID, db: DBSession):
    return await user_controller.get_user(user_id=user_id, db=db)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: DBSession):
    return await user_controller.create_user(payload=payload, db=db)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: uuid.UUID, payload: UserUpdate, db: DBSession):
    return await user_controller.update_user(user_id=user_id, payload=payload, db=db)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: uuid.UUID, db: DBSession) -> Response:
    return await user_controller.delete_user(user_id=user_id, db=db)
