import uuid

from fastapi import status
from fastapi.responses import Response

from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.feature import FeatureCreate, FeatureResponse, FeatureUpdate
from app.services.feature_service import FeatureService


async def list_features(epic_id: uuid.UUID, page: int, size: int, db: DBSession) -> PaginatedResponse[FeatureResponse]:
    return await FeatureService(db).list_features(epic_id=epic_id, page=page, size=size)


async def get_feature(epic_id: uuid.UUID, feature_id: uuid.UUID, db: DBSession) -> FeatureResponse:
    return await FeatureService(db).get_feature(epic_id=epic_id, feature_id=feature_id)


async def create_feature(epic_id: uuid.UUID, payload: FeatureCreate, db: DBSession) -> FeatureResponse:
    return await FeatureService(db).create_feature(epic_id=epic_id, payload=payload)


async def update_feature(epic_id: uuid.UUID, feature_id: uuid.UUID, payload: FeatureUpdate, db: DBSession) -> FeatureResponse:
    return await FeatureService(db).update_feature(epic_id=epic_id, feature_id=feature_id, payload=payload)


async def delete_feature(epic_id: uuid.UUID, feature_id: uuid.UUID, db: DBSession, delete_remote: bool = False) -> Response:
    await FeatureService(db).delete_feature(epic_id=epic_id, feature_id=feature_id, delete_remote=delete_remote)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
