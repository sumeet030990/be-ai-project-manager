import uuid

from fastapi import APIRouter, File, Form, UploadFile, status

from app.controllers import brd_controller
from app.core.dependencies import DBSession
from app.schemas.brd import (
    BRDAnalysisResult,
    BRDBulkSaveRequest,
    BRDBulkSaveResponse,
    BRDRefineRequest,
    BRDRefineResponse,
)

router = APIRouter(prefix="/projects/{project_id}/brd", tags=["BRD Analysis"])


@router.post("/analyze", response_model=BRDAnalysisResult)
async def analyze_brd(
    project_id: uuid.UUID,
    db: DBSession,
    file: UploadFile = File(..., description="Business Requirements Document (.txt, .pdf, .docx)"),
    config_id: uuid.UUID | None = Form(default=None),
):
    return await brd_controller.analyze_brd(
        project_id=project_id,
        file=file,
        db=db,
        config_id=config_id,
    )


@router.post("/refine", response_model=BRDRefineResponse)
async def refine_item(
    project_id: uuid.UUID,
    payload: BRDRefineRequest,
    db: DBSession,
):
    return await brd_controller.refine_item(
        project_id=project_id,
        payload=payload,
        db=db,
    )


@router.post("/save", response_model=BRDBulkSaveResponse, status_code=status.HTTP_201_CREATED)
async def save_brd_analysis(
    project_id: uuid.UUID,
    payload: BRDBulkSaveRequest,
    db: DBSession,
):
    return await brd_controller.save_brd_analysis(
        project_id=project_id,
        payload=payload,
        db=db,
    )
