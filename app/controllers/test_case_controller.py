import uuid

from fastapi import status
from fastapi.responses import Response

from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.test_case import TestCaseCreate, TestCaseGenerateRequest, TestCaseResponse, TestCaseUpdate
from app.services.test_case_service import TestCaseService


async def list_test_cases(
    module_id: uuid.UUID, story_id: uuid.UUID, page: int, size: int, db: DBSession
) -> PaginatedResponse[TestCaseResponse]:
    return await TestCaseService(db).list_test_cases(module_id=module_id, story_id=story_id, page=page, size=size)


async def get_test_case(
    module_id: uuid.UUID, story_id: uuid.UUID, test_case_id: uuid.UUID, db: DBSession
) -> TestCaseResponse:
    return await TestCaseService(db).get_test_case(module_id=module_id, story_id=story_id, test_case_id=test_case_id)


async def create_test_case(
    module_id: uuid.UUID, story_id: uuid.UUID, payload: TestCaseCreate, db: DBSession
) -> TestCaseResponse:
    return await TestCaseService(db).create_test_case(module_id=module_id, story_id=story_id, payload=payload)


async def update_test_case(
    module_id: uuid.UUID, story_id: uuid.UUID, test_case_id: uuid.UUID, payload: TestCaseUpdate, db: DBSession
) -> TestCaseResponse:
    return await TestCaseService(db).update_test_case(
        module_id=module_id, story_id=story_id, test_case_id=test_case_id, payload=payload
    )


async def delete_test_case(
    module_id: uuid.UUID, story_id: uuid.UUID, test_case_id: uuid.UUID, db: DBSession
) -> Response:
    await TestCaseService(db).delete_test_case(module_id=module_id, story_id=story_id, test_case_id=test_case_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def generate_test_cases(
    module_id: uuid.UUID, story_id: uuid.UUID, payload: TestCaseGenerateRequest, db: DBSession
) -> list[TestCaseResponse]:
    return await TestCaseService(db).generate_test_cases(module_id=module_id, story_id=story_id, payload=payload)
