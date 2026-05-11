import uuid

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.controllers import test_case_controller
from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.test_case import TestCaseCreate, TestCaseGenerateRequest, TestCaseResponse, TestCaseUpdate

router = APIRouter(tags=["Test Cases"])

_PREFIX = "/modules/{module_id}/stories/{story_id}/test-cases"


@router.get(_PREFIX, response_model=PaginatedResponse[TestCaseResponse])
async def list_test_cases(
    module_id: uuid.UUID,
    story_id: uuid.UUID,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    return await test_case_controller.list_test_cases(
        module_id=module_id, story_id=story_id, page=page, size=size, db=db
    )


@router.get(_PREFIX + "/{test_case_id}", response_model=TestCaseResponse)
async def get_test_case(module_id: uuid.UUID, story_id: uuid.UUID, test_case_id: uuid.UUID, db: DBSession):
    return await test_case_controller.get_test_case(
        module_id=module_id, story_id=story_id, test_case_id=test_case_id, db=db
    )


@router.post(_PREFIX, response_model=TestCaseResponse, status_code=201)
async def create_test_case(
    module_id: uuid.UUID, story_id: uuid.UUID, payload: TestCaseCreate, db: DBSession
):
    return await test_case_controller.create_test_case(
        module_id=module_id, story_id=story_id, payload=payload, db=db
    )


@router.patch(_PREFIX + "/{test_case_id}", response_model=TestCaseResponse)
async def update_test_case(
    module_id: uuid.UUID, story_id: uuid.UUID, test_case_id: uuid.UUID, payload: TestCaseUpdate, db: DBSession
):
    return await test_case_controller.update_test_case(
        module_id=module_id, story_id=story_id, test_case_id=test_case_id, payload=payload, db=db
    )


@router.delete(_PREFIX + "/{test_case_id}", status_code=204)
async def delete_test_case(
    module_id: uuid.UUID, story_id: uuid.UUID, test_case_id: uuid.UUID, db: DBSession
) -> Response:
    return await test_case_controller.delete_test_case(
        module_id=module_id, story_id=story_id, test_case_id=test_case_id, db=db
    )


@router.post(_PREFIX + "/generate", response_model=list[TestCaseResponse], status_code=201)
async def generate_test_cases(
    module_id: uuid.UUID, story_id: uuid.UUID, payload: TestCaseGenerateRequest, db: DBSession
):
    return await test_case_controller.generate_test_cases(
        module_id=module_id, story_id=story_id, payload=payload, db=db
    )
