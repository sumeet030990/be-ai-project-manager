import uuid
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_client import get_project_ai_client
from app.core.exceptions import BadRequestException, NotFoundException
from app.repositories.feature_repository import FeatureRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.story_repository import StoryRepository
from app.schemas.brd import (
    BRDAnalysisResult,
    BRDBulkSaveRequest,
    BRDBulkSaveResponse,
    BRDSyncStatus,
)
from database.models.feature import Feature
from database.models.story import Story


_ANALYZE_BRD_TOOL: Any = {
    "type": "function",
    "function": {
        "name": "save_brd_analysis",
        "description": "Save the structured analysis of the Business Requirements Document.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_context": {
                    "type": "string",
                    "description": (
                        "A comprehensive project context summary derived from the BRD. "
                        "Include goals, scope, key stakeholders, constraints, domain context, "
                        "and technical considerations. This will be stored as the project_info "
                        "and used to inform AI story generation."
                    ),
                },
                "features": {
                    "type": "array",
                    "description": "Features extracted from the BRD, ordered by logical implementation sequence.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Feature name — concise, action-oriented (e.g. 'User Authentication', 'Payment Processing')",
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of what this feature entails and its business value.",
                            },
                            "order": {
                                "type": "integer",
                                "description": "Implementation order, 1-based. Lower numbers should be built first.",
                            },
                            "priority": {
                                "type": "integer",
                                "description": "Priority: 1=critical, 2=high, 3=medium, 4=low, 5=nice-to-have.",
                                "minimum": 1,
                                "maximum": 5,
                            },
                            "stories": {
                                "type": "array",
                                "description": "User stories for this feature, ordered by implementation sequence.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {
                                            "type": "string",
                                            "description": (
                                                "Story title with a type prefix: [FE] frontend, [BE] backend, "
                                                "[API] API/integration, [DB] database, [Infra] infrastructure, [Test] testing."
                                            ),
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "What needs to be built and why.",
                                        },
                                        "order": {
                                            "type": "integer",
                                            "description": "Order within the feature, 1-based.",
                                        },
                                        "story_points": {
                                            "type": "integer",
                                            "description": "Fibonacci story points. Use 3 for standard scope, 5 for clearly larger work. Never exceed 5.",
                                            "minimum": 1,
                                            "maximum": 5,
                                        },
                                        "priority": {
                                            "type": "integer",
                                            "description": "Priority: 1=critical, 2=high, 3=medium, 4=low, 5=nice-to-have.",
                                            "minimum": 1,
                                            "maximum": 5,
                                        },
                                    },
                                    "required": ["title", "description", "order", "story_points", "priority"],
                                },
                            },
                        },
                        "required": ["name", "description", "order", "priority", "stories"],
                    },
                },
            },
            "required": ["project_context", "features"],
        },
    },
}


def _extract_text(content: bytes, filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "txt"

    if ext == "txt":
        return content.decode("utf-8", errors="replace")

    if ext == "pdf":
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(p for p in pages if p.strip())
        except ImportError:
            raise BadRequestException("PDF parsing requires pypdf. Run: pip install pypdf")

    if ext == "docx":
        try:
            import io
            from docx import Document
            doc = Document(io.BytesIO(content))
            return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        except ImportError:
            raise BadRequestException("DOCX parsing requires python-docx. Run: pip install python-docx")

    try:
        return content.decode("utf-8", errors="replace")
    except Exception:
        raise BadRequestException(f"Unsupported file format: .{ext}. Supported: .txt, .pdf, .docx")


def _normalize(s: str) -> str:
    return s.lower().strip()


def _enrich_with_sync_status(
    ai_features: list[dict],
    existing_features: list[Feature],
) -> list[dict]:
    existing_by_name: dict[str, Feature] = {
        _normalize(f.name): f for f in existing_features
    }

    enriched = []
    for ai_feat in ai_features:
        existing_feat = existing_by_name.get(_normalize(ai_feat["name"]))

        if existing_feat is None:
            feat_status = BRDSyncStatus.new
            feat_existing_id = None
            existing_stories_by_title: dict[str, Story] = {}
        else:
            ai_desc = (ai_feat.get("description") or "").strip()
            ex_desc = (existing_feat.description or "").strip()
            if ai_desc != ex_desc or existing_feat.priority != ai_feat.get("priority", 0):
                feat_status = BRDSyncStatus.update
            else:
                feat_status = BRDSyncStatus.exists
            feat_existing_id = str(existing_feat.id)
            existing_stories_by_title = {
                _normalize(s.title): s for s in (existing_feat.stories or [])
            }

        enriched_stories = []
        for story in ai_feat.get("stories", []):
            existing_story = existing_stories_by_title.get(_normalize(story["title"]))

            if existing_story is None:
                story_status = BRDSyncStatus.new
                story_existing_id = None
            else:
                ai_sdesc = (story.get("description") or "").strip()
                ex_sdesc = (existing_story.description or "").strip()
                if (
                    ai_sdesc != ex_sdesc
                    or existing_story.priority != story.get("priority", 0)
                    or existing_story.story_points != story.get("story_points")
                ):
                    story_status = BRDSyncStatus.update
                else:
                    story_status = BRDSyncStatus.exists
                story_existing_id = str(existing_story.id)

            enriched_stories.append({
                **story,
                "sync_status": story_status,
                "existing_id": story_existing_id,
            })

        enriched.append({
            **ai_feat,
            "stories": enriched_stories,
            "sync_status": feat_status,
            "existing_id": feat_existing_id,
        })

    return enriched


class BRDService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.project_repository = ProjectRepository(session)
        self.feature_repository = FeatureRepository(session)
        self.story_repository = StoryRepository(session)

    async def analyze_brd(
        self,
        project_id: uuid.UUID,
        file: UploadFile,
        config_id: uuid.UUID | None = None,
    ) -> BRDAnalysisResult:
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundException("Project", str(project_id))

        content = await file.read()
        if not content:
            raise BadRequestException("Uploaded file is empty.")

        text = _extract_text(content, file.filename or "document.txt")
        if not text.strip():
            raise BadRequestException("Could not extract any text from the uploaded file.")

        ai_client = await get_project_ai_client(project_id, self.session, config_id=config_id)
        result = await ai_client.chat_with_tools(
            tools=[_ANALYZE_BRD_TOOL],
            tool_choice={"type": "function", "function": {"name": "save_brd_analysis"}},
            max_tokens=8192,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert software architect and project manager. "
                        "Analyze Business Requirements Documents and extract structured, actionable features and user stories.\n\n"
                        "Rules:\n"
                        "- Group requirements into logical, cohesive features\n"
                        "- Each feature should have 3-8 user stories covering all layers (FE, BE, API, DB, etc.)\n"
                        "- Story titles must start with [FE], [BE], [API], [DB], [Infra], or [Test]\n"
                        "- Order features by logical implementation sequence (foundational work first)\n"
                        "- Priority 1=critical path, 5=enhancement\n"
                        "- Story points: 3 for standard, 5 for larger. Never exceed 5.\n"
                        "- project_context must be comprehensive enough for AI to generate detailed stories without the original document"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Analyze this Business Requirements Document. "
                        "Extract all features with their user stories, and write a comprehensive project context.\n\n"
                        f"Document:\n{text[:50000]}"
                    ),
                },
            ],
        )

        existing_features = await self.feature_repository.get_all_with_stories_by_project(project_id)
        enriched_features = _enrich_with_sync_status(result.arguments["features"], existing_features)

        return BRDAnalysisResult(
            project_context=result.arguments["project_context"],
            features=enriched_features,
        )

    async def save_brd_analysis(
        self,
        project_id: uuid.UUID,
        payload: BRDBulkSaveRequest,
    ) -> BRDBulkSaveResponse:
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundException("Project", str(project_id))

        created_features = 0
        updated_features = 0
        created_stories = 0
        updated_stories = 0

        for feat_data in payload.features:
            if feat_data.existing_id:
                existing_feature = await self.feature_repository.get_by_id(
                    uuid.UUID(feat_data.existing_id)
                )
                if existing_feature:
                    existing_feature.name = feat_data.name
                    existing_feature.description = feat_data.description
                    existing_feature.order = feat_data.order
                    existing_feature.priority = feat_data.priority
                    feature = await self.feature_repository.update(existing_feature)
                    updated_features += 1
                else:
                    feature = await self._create_feature(project_id, payload.created_by, feat_data)
                    created_features += 1
            else:
                feature = await self._create_feature(project_id, payload.created_by, feat_data)
                created_features += 1

            for story_data in feat_data.stories:
                if story_data.existing_id:
                    existing_story = await self.story_repository.get_by_id(
                        uuid.UUID(story_data.existing_id)
                    )
                    if existing_story:
                        existing_story.title = story_data.title
                        existing_story.description = story_data.description
                        existing_story.order = story_data.order
                        existing_story.story_points = min(story_data.story_points, 5)
                        existing_story.priority = story_data.priority
                        await self.story_repository.update(existing_story)
                        updated_stories += 1
                    else:
                        await self._create_story(feature.id, story_data)
                        created_stories += 1
                else:
                    await self._create_story(feature.id, story_data)
                    created_stories += 1

        if payload.save_context and payload.project_context:
            project.project_info = payload.project_context
            await self.project_repository.update(project)

        return BRDBulkSaveResponse(
            created_features=created_features,
            updated_features=updated_features,
            created_stories=created_stories,
            updated_stories=updated_stories,
        )

    async def _create_feature(self, project_id: uuid.UUID, created_by: uuid.UUID, feat_data) -> Feature:
        feature = Feature(
            project_id=project_id,
            created_by=created_by,
            name=feat_data.name,
            description=feat_data.description,
            order=feat_data.order,
            priority=feat_data.priority,
            status="draft",
        )
        return await self.feature_repository.create(feature)

    async def _create_story(self, feature_id: uuid.UUID, story_data) -> Story:
        story = Story(
            feature_id=feature_id,
            title=story_data.title,
            description=story_data.description,
            order=story_data.order,
            story_points=min(story_data.story_points, 5),
            priority=story_data.priority,
            status="draft",
            is_ai_generated=True,
        )
        self.story_repository.session.add(story)
        await self.story_repository.session.flush()
        await self.story_repository.session.refresh(story)
        return story
