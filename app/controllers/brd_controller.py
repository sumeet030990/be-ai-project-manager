import uuid

from fastapi import UploadFile

from app.core.dependencies import DBSession
from app.schemas.brd import BRDAnalysisResult, BRDBulkSaveRequest, BRDBulkSaveResponse
from app.services.brd_service import BRDService


async def analyze_brd(
    project_id: uuid.UUID,
    file: UploadFile,
    db: DBSession,
    config_id: uuid.UUID | None = None,
) -> BRDAnalysisResult:
    return await BRDService(db).analyze_brd(project_id=project_id, file=file, config_id=config_id)


async def save_brd_analysis(
    project_id: uuid.UUID,
    payload: BRDBulkSaveRequest,
    db: DBSession,
) -> BRDBulkSaveResponse:
    return await BRDService(db).save_brd_analysis(project_id=project_id, payload=payload)
