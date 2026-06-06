import uuid

from fastapi import APIRouter, Query, status
from fastapi.responses import Response

from app.controllers import feature_controller
from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.feature import FeatureCreate, FeatureResponse, FeatureUpdate

router = APIRouter(prefix="/projects/{project_id}/features", tags=["Features"])


@router.get("", response_model=PaginatedResponse[FeatureResponse])
async def list_features(
    project_id: uuid.UUID,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    return await feature_controller.list_features(project_id=project_id, page=page, size=size, db=db)


@router.get("/{feature_id}", response_model=FeatureResponse)
async def get_feature(project_id: uuid.UUID, feature_id: uuid.UUID, db: DBSession):
    return await feature_controller.get_feature(project_id=project_id, feature_id=feature_id, db=db)


@router.post("", response_model=FeatureResponse, status_code=status.HTTP_201_CREATED)
async def create_feature(project_id: uuid.UUID, payload: FeatureCreate, db: DBSession):
    return await feature_controller.create_feature(project_id=project_id, payload=payload, db=db)


@router.patch("/{feature_id}", response_model=FeatureResponse)
async def update_feature(project_id: uuid.UUID, feature_id: uuid.UUID, payload: FeatureUpdate, db: DBSession):
    return await feature_controller.update_feature(project_id=project_id, feature_id=feature_id, payload=payload, db=db)


@router.delete("/{feature_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature(
    project_id: uuid.UUID,
    feature_id: uuid.UUID,
    db: DBSession,
    delete_remote: bool = Query(default=False),
) -> Response:
    return await feature_controller.delete_feature(project_id=project_id, feature_id=feature_id, db=db, delete_remote=delete_remote)
