import uuid

from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.prompt import PromptCreate, PromptResponse
from app.services.prompt_service import PromptService


async def list_prompts(
    module_id: uuid.UUID, story_id: uuid.UUID, page: int, size: int, db: DBSession
) -> PaginatedResponse[PromptResponse]:
    return await PromptService(db).list_prompts(
        module_id=module_id, story_id=story_id, page=page, size=size
    )


async def save_prompt(
    module_id: uuid.UUID, story_id: uuid.UUID, payload: PromptCreate, db: DBSession
) -> PromptResponse:
    return await PromptService(db).save_prompt(
        module_id=module_id, story_id=story_id, payload=payload
    )
