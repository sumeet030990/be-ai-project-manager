import uuid
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_client import get_project_ai_client
from app.core.exceptions import BadRequestException, NotFoundException
from app.repositories.epic_repository import EpicRepository
from app.repositories.feature_repository import FeatureRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.story_repository import StoryRepository
from app.schemas.brd import (
    BRDAnalysisResult,
    BRDBulkSaveRequest,
    BRDBulkSaveResponse,
    BRDEpicResult,
    BRDFeatureResult,
    BRDRefineRequest,
    BRDRefineResponse,
    BRDStoryResult,
)
from database.models.epic import Epic
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
                "epics": {
                    "type": "array",
                    "description": "Top-level epics extracted from the BRD, ordered by logical implementation sequence.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Epic name — high-level business objective (e.g. 'User Management', 'Payment & Billing').",
                            },
                            "description": {
                                "type": "string",
                                "description": "Comprehensive description of the epic's scope, business value, and goals.",
                            },
                            "order": {
                                "type": "integer",
                                "description": "Implementation order, 1-based. Foundational epics first.",
                            },
                            "priority": {
                                "type": "integer",
                                "description": "Priority: 1=critical, 2=high, 3=medium, 4=low, 5=nice-to-have.",
                                "minimum": 1,
                                "maximum": 5,
                            },
                            "features": {
                                "type": "array",
                                "description": "Features that implement this epic, ordered by implementation sequence.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "Feature name — a specific capability within the epic (e.g. 'User Registration', 'OAuth Login').",
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Detailed description of what this feature entails and its business value.",
                                        },
                                        "business_rules": {
                                            "type": "string",
                                            "description": "Key business rules, constraints, and logic specific to this feature.",
                                        },
                                        "acceptance_criteria": {
                                            "type": "string",
                                            "description": "Testable acceptance criteria in Given/When/Then format or bullet points.",
                                        },
                                        "order": {
                                            "type": "integer",
                                            "description": "Order within the epic, 1-based.",
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
                                                        "description": "What needs to be built and why, including key technical considerations.",
                                                    },
                                                    "business_rules": {
                                                        "type": "string",
                                                        "description": "Business rules, edge cases, validations, and constraints for this story.",
                                                    },
                                                    "acceptance_criteria": {
                                                        "type": "string",
                                                        "description": "Testable acceptance criteria in Given/When/Then format or bullet points.",
                                                    },
                                                    "order": {
                                                        "type": "integer",
                                                        "description": "Order within the feature, 1-based.",
                                                    },
                                                    "story_points": {
                                                        "type": "integer",
                                                        "description": "Fibonacci story points. Use 3 for standard scope, 5 for larger work, 8 for very large. Max 13.",
                                                        "minimum": 1,
                                                        "maximum": 13,
                                                    },
                                                    "priority": {
                                                        "type": "integer",
                                                        "description": "Priority: 1=critical, 2=high, 3=medium, 4=low, 5=nice-to-have.",
                                                        "minimum": 1,
                                                        "maximum": 5,
                                                    },
                                                },
                                                "required": ["title", "description", "business_rules", "acceptance_criteria", "order", "story_points", "priority"],
                                            },
                                        },
                                    },
                                    "required": ["name", "description", "business_rules", "acceptance_criteria", "order", "priority", "stories"],
                                },
                            },
                        },
                        "required": ["name", "description", "order", "priority", "features"],
                    },
                },
            },
            "required": ["project_context", "epics"],
        },
    },
}


_REFINE_ITEM_TOOL: Any = {
    "type": "function",
    "function": {
        "name": "return_refined_item",
        "description": "Return the enriched item details.",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Clear, detailed description of this item's scope and business value.",
                },
                "business_rules": {
                    "type": "string",
                    "description": "Specific business rules, constraints, validations, and edge cases.",
                },
                "acceptance_criteria": {
                    "type": "string",
                    "description": "Testable acceptance criteria in Given/When/Then format or as bullet points.",
                },
            },
            "required": ["description"],
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
    ai_epics: list[dict],
    existing_epics: list[Epic],
) -> list[BRDEpicResult]:
    existing_by_name: dict[str, Epic] = {
        _normalize(e.name): e for e in existing_epics
    }

    enriched_epics = []
    for ai_epic in ai_epics:
        existing_epic = existing_by_name.get(_normalize(ai_epic["name"]))

        if existing_epic is None:
            epic_status = "new"
            epic_existing_id = None
            existing_features_by_name: dict[str, Feature] = {}
        else:
            ai_desc = (ai_epic.get("description") or "").strip()
            ex_desc = (existing_epic.description or "").strip()
            if ai_desc != ex_desc or existing_epic.priority != ai_epic.get("priority", 0):
                epic_status = "update"
            else:
                epic_status = "exists"
            epic_existing_id = str(existing_epic.id)
            existing_features_by_name = {
                _normalize(f.name): f for f in (existing_epic.features or [])
            }

        enriched_features = []
        for ai_feat in ai_epic.get("features", []):
            existing_feat = existing_features_by_name.get(_normalize(ai_feat["name"]))

            if existing_feat is None:
                feat_status = "new"
                feat_existing_id = None
                existing_stories_by_title: dict[str, Story] = {}
            else:
                ai_fdesc = (ai_feat.get("description") or "").strip()
                ex_fdesc = (existing_feat.description or "").strip()
                if ai_fdesc != ex_fdesc or existing_feat.priority != ai_feat.get("priority", 0):
                    feat_status = "update"
                else:
                    feat_status = "exists"
                feat_existing_id = str(existing_feat.id)
                existing_stories_by_title = {
                    _normalize(s.title): s for s in (existing_feat.stories or [])
                }

            enriched_stories = []
            for story in ai_feat.get("stories", []):
                existing_story = existing_stories_by_title.get(_normalize(story["title"]))

                if existing_story is None:
                    story_status = "new"
                    story_existing_id = None
                else:
                    ai_sdesc = (story.get("description") or "").strip()
                    ex_sdesc = (existing_story.description or "").strip()
                    if (
                        ai_sdesc != ex_sdesc
                        or existing_story.priority != story.get("priority", 0)
                        or existing_story.story_points != story.get("story_points")
                    ):
                        story_status = "update"
                    else:
                        story_status = "exists"
                    story_existing_id = str(existing_story.id)

                enriched_stories.append(BRDStoryResult(
                    title=story["title"],
                    description=story.get("description"),
                    business_rules=story.get("business_rules"),
                    acceptance_criteria=story.get("acceptance_criteria"),
                    order=story["order"],
                    story_points=story["story_points"],
                    priority=story["priority"],
                    sync_status=story_status,
                    existing_id=story_existing_id,
                ))

            enriched_features.append(BRDFeatureResult(
                name=ai_feat["name"],
                description=ai_feat.get("description"),
                business_rules=ai_feat.get("business_rules"),
                acceptance_criteria=ai_feat.get("acceptance_criteria"),
                order=ai_feat["order"],
                priority=ai_feat["priority"],
                stories=enriched_stories,
                sync_status=feat_status,
                existing_id=feat_existing_id,
            ))

        enriched_epics.append(BRDEpicResult(
            name=ai_epic["name"],
            description=ai_epic.get("description"),
            order=ai_epic["order"],
            priority=ai_epic["priority"],
            features=enriched_features,
            sync_status=epic_status,
            existing_id=epic_existing_id,
        ))

    return enriched_epics


class BRDService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.project_repository = ProjectRepository(session)
        self.epic_repository = EpicRepository(session)
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
            max_tokens=6000,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior software architect and project manager with deep expertise in full-stack systems, "
                        "security, infrastructure, and product delivery.\n\n"
                        "Your task: analyze the provided Business Requirements Document and produce a COMPLETE, PRODUCTION-READY "
                        "breakdown of Epics → Features → Stories covering every aspect needed to build and ship the product.\n\n"
                        "SCOPE — go beyond what is explicitly stated. You must infer and include:\n"
                        "- Authentication, authorization, and role/permission management\n"
                        "- All CRUD operations, search, filtering, pagination, and sorting\n"
                        "- Data validation, error handling, and user-facing error messages\n"
                        "- Audit logging, activity history, and soft deletes where appropriate\n"
                        "- Email/notification flows (confirmation, alerts, reminders)\n"
                        "- File upload/download if any entity has attachments\n"
                        "- Reporting, dashboards, and data export (CSV/PDF) if the domain implies it\n"
                        "- Admin panel / back-office capabilities\n"
                        "- Performance: caching strategies, background jobs, async processing\n"
                        "- Security: input sanitization, rate limiting, secrets management\n"
                        "- Infrastructure & DevOps: CI/CD, environment config, database migrations\n"
                        "- Onboarding, help, and empty-state UX for every major screen\n"
                        "- Settings and profile management\n\n"
                        "STRUCTURE RULES:\n"
                        "- EPICS = major business domains (e.g. Auth, User Management, Core Feature, Notifications, Admin, Infra)\n"
                        "- FEATURES = specific capabilities within an epic\n"
                        "- STORIES = atomic implementation tasks; titles MUST start with [FE], [BE], [API], [DB], or [Test]\n"
                        "- Every feature and story MUST have description, business_rules, and acceptance_criteria\n"
                        "- Cover both happy-path AND edge cases in acceptance_criteria\n\n"
                        "ORDERING — sequence everything by logical implementation dependency:\n"
                        "1. Foundation first: DB schema, auth, core models\n"
                        "2. Core domain logic next\n"
                        "3. Integrations and side-effects (notifications, exports) after core\n"
                        "4. Admin/reporting/infra last\n"
                        "- Priority: 1=critical (blocks others), 2=high, 3=medium, 4=low, 5=enhancement\n"
                        "- Within each epic, features must be ordered so no feature depends on a later one\n"
                        "- Within each feature, stories must be ordered: [DB] → [BE]/[API] → [FE] → [Test]\n\n"
                        "OUTPUT QUALITY:\n"
                        "- Be thorough, not minimal — a missing story is a gap that will become a bug or rework\n"
                        "- Every field must be filled — no empty strings, no 'TBD'\n"
                        "- Acceptance criteria must be testable conditions, not vague statements"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Analyze the BRD below. Produce the COMPLETE epic/feature/story breakdown.\n\n"
                        "Do NOT limit yourself to what is explicitly written — infer every capability required to build a production-ready system. "
                        "Order everything by logical implementation sequence (foundations first, integrations last). "
                        "Every item must have all fields filled with concrete, testable content.\n\n"
                        f"BRD Document:\n{text[:12000]}"
                    ),
                },
            ],
        )

        existing_epics = await self.epic_repository.get_all_with_features_and_stories(project_id)
        enriched_epics = _enrich_with_sync_status(result.arguments["epics"], existing_epics)

        return BRDAnalysisResult(
            project_context=result.arguments["project_context"],
            epics=enriched_epics,
        )

    async def refine_item(
        self,
        project_id: uuid.UUID,
        payload: BRDRefineRequest,
    ) -> BRDRefineResponse:
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundException("Project", str(project_id))

        item_label = payload.title or payload.name or "item"
        item_type_label = payload.item_type.capitalize()

        current_info_parts = []
        if payload.description:
            current_info_parts.append(f"Current description:\n{payload.description}")
        if payload.business_rules:
            current_info_parts.append(f"Current business rules:\n{payload.business_rules}")
        if payload.acceptance_criteria:
            current_info_parts.append(f"Current acceptance criteria:\n{payload.acceptance_criteria}")
        current_info = "\n\n".join(current_info_parts) if current_info_parts else "No details provided yet."

        extra = f"\n\nAdditional context: {payload.context}" if payload.context else ""

        ai_client = await get_project_ai_client(project_id, self.session, config_id=payload.config_id)
        result = await ai_client.chat_with_tools(
            tools=[_REFINE_ITEM_TOOL],
            tool_choice={"type": "function", "function": {"name": "return_refined_item"}},
            max_tokens=4096,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert software architect. Enrich software project items with detailed, "
                        "actionable content that developers can implement directly.\n\n"
                        "For epics: write a clear description of the business domain and goals.\n"
                        "For features and stories: write a detailed description plus specific business rules "
                        "(constraints, validations, edge cases, logic) and testable acceptance criteria "
                        "(Given/When/Then format preferred).\n\n"
                        "Be specific, concrete, and implementation-ready."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Refine this {item_type_label}: \"{item_label}\"\n\n"
                        f"{current_info}"
                        f"{extra}"
                    ),
                },
            ],
        )

        args = result.arguments
        return BRDRefineResponse(
            description=args.get("description"),
            business_rules=args.get("business_rules"),
            acceptance_criteria=args.get("acceptance_criteria"),
        )

    async def save_brd_analysis(
        self,
        project_id: uuid.UUID,
        payload: BRDBulkSaveRequest,
    ) -> BRDBulkSaveResponse:
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundException("Project", str(project_id))

        created_epics = 0
        updated_epics = 0
        created_features = 0
        updated_features = 0
        created_stories = 0
        updated_stories = 0

        for epic_data in payload.epics:
            if epic_data.existing_id:
                existing_epic = await self.epic_repository.get_by_id(uuid.UUID(epic_data.existing_id))
                if existing_epic:
                    existing_epic.name = epic_data.name
                    existing_epic.description = epic_data.description
                    existing_epic.order = epic_data.order
                    existing_epic.priority = epic_data.priority
                    epic = await self.epic_repository.update(existing_epic)
                    updated_epics += 1
                else:
                    epic = await self._create_epic(project_id, payload.created_by, epic_data)
                    created_epics += 1
            else:
                epic = await self._create_epic(project_id, payload.created_by, epic_data)
                created_epics += 1

            for feat_data in epic_data.features:
                if feat_data.existing_id:
                    existing_feature = await self.feature_repository.get_by_id(uuid.UUID(feat_data.existing_id))
                    if existing_feature:
                        existing_feature.name = feat_data.name
                        existing_feature.description = feat_data.description
                        existing_feature.business_rules = feat_data.business_rules
                        existing_feature.acceptance_criteria = feat_data.acceptance_criteria
                        existing_feature.order = feat_data.order
                        existing_feature.priority = feat_data.priority
                        feature = await self.feature_repository.update(existing_feature)
                        updated_features += 1
                    else:
                        feature = await self._create_feature(epic.id, payload.created_by, feat_data)
                        created_features += 1
                else:
                    feature = await self._create_feature(epic.id, payload.created_by, feat_data)
                    created_features += 1

                for story_data in feat_data.stories:
                    if story_data.existing_id:
                        existing_story = await self.story_repository.get_by_id(uuid.UUID(story_data.existing_id))
                        if existing_story:
                            existing_story.title = story_data.title
                            existing_story.description = story_data.description
                            existing_story.business_rules = story_data.business_rules
                            existing_story.acceptance_criteria = story_data.acceptance_criteria
                            existing_story.order = story_data.order
                            existing_story.story_points = min(story_data.story_points, 13)
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
            created_epics=created_epics,
            updated_epics=updated_epics,
            created_features=created_features,
            updated_features=updated_features,
            created_stories=created_stories,
            updated_stories=updated_stories,
        )

    async def _create_epic(self, project_id: uuid.UUID, created_by: uuid.UUID, epic_data) -> Epic:
        epic = Epic(
            project_id=project_id,
            created_by=created_by,
            name=epic_data.name,
            description=epic_data.description,
            order=epic_data.order,
            priority=epic_data.priority,
            status="draft",
        )
        return await self.epic_repository.create(epic)

    async def _create_feature(self, epic_id: uuid.UUID, created_by: uuid.UUID, feat_data) -> Feature:
        feature = Feature(
            epic_id=epic_id,
            created_by=created_by,
            name=feat_data.name,
            description=feat_data.description,
            business_rules=feat_data.business_rules,
            acceptance_criteria=feat_data.acceptance_criteria,
            order=feat_data.order,
            priority=feat_data.priority,
            status="draft",
            is_ai_generated=True,
        )
        return await self.feature_repository.create(feature)

    async def _create_story(self, feature_id: uuid.UUID, story_data) -> Story:
        story = Story(
            feature_id=feature_id,
            title=story_data.title,
            description=story_data.description,
            business_rules=story_data.business_rules,
            acceptance_criteria=story_data.acceptance_criteria,
            order=story_data.order,
            story_points=min(story_data.story_points, 13),
            priority=story_data.priority,
            status="draft",
            is_ai_generated=True,
        )
        self.story_repository.session.add(story)
        await self.story_repository.session.flush()
        await self.story_repository.session.refresh(story)
        return story
