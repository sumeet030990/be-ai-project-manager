from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.project import Project
from database.models.project_tech_stack import ProjectTechStack

TECH_STACKS = [
    {
        "project_name": "AI Project Manager",
        "stacks": [
            {"name": "React", "version": "19.2.0", "category": "frontend", "description": "UI library for building component-based interfaces."},
            {"name": "Node.js", "version": "24.x", "category": "frontend", "description": "JavaScript runtime environment for the frontend build and tooling."},
            {"name": "FastAPI", "version": "0.136.1", "category": "backend", "description": "Python async web framework for building REST APIs."},
        ],
    },
]


async def seed_project_tech_stacks(session: AsyncSession, projects: list[Project]) -> None:
    project_map = {p.name: p for p in projects}

    created = 0
    skipped = 0

    for entry in TECH_STACKS:
        project = project_map.get(entry["project_name"])
        if not project:
            print(f"[tech_stack_seeder] project '{entry['project_name']}' not found — skipping.")
            continue

        existing_result = await session.execute(
            select(ProjectTechStack).where(ProjectTechStack.project_id == project.id)
        )
        existing_names = {s.name for s in existing_result.scalars().all()}

        for stack_data in entry["stacks"]:
            if stack_data["name"] in existing_names:
                skipped += 1
                continue

            session.add(ProjectTechStack(
                project_id=project.id,
                name=stack_data["name"],
                version=stack_data["version"],
                category=stack_data["category"],
                description=stack_data.get("description"),
            ))
            created += 1

    await session.flush()
    print(f"[tech_stack_seeder] seeded {created} tech stack(s), skipped {skipped} existing.")
