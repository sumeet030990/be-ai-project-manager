from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.company import Company
from database.models.project import Project
from database.models.user import User

PROJECTS = [
    {
        "name": "Goibibo",
        "description": "Copy of goibibo.com for learning purposes.",
        "status": "active",
        "company_email": "info@neighborlysoftware.com",
        "created_by_email": "admin@example.com",
    }, 
    {
        "name": "AI Project Manager",
        "description": "Internal AI-powered project management tool.",
        "status": "active",
        "company_email": "info@neighborlysoftware.com",
        "created_by_email": "admin@example.com",
    },
]


async def seed_projects(
    session: AsyncSession,
    companies: list[Company],
    users: list[User],
) -> list[Project]:
    company_map = {c.email: c for c in companies}
    user_map = {u.email: u for u in users}

    result = await session.execute(select(Project))
    existing_names = {p.name for p in result.scalars().all()}

    created = 0
    for data in PROJECTS:
        if data["name"] in existing_names:
            continue

        company = company_map.get(data["company_email"])
        creator = user_map.get(data["created_by_email"])

        if not company:
            print(f"[project_seeder] company '{data['company_email']}' not found — skipping '{data['name']}'.")
            continue
        if not creator:
            print(f"[project_seeder] user '{data['created_by_email']}' not found — skipping '{data['name']}'.")
            continue

        project = Project(
            name=data["name"],
            description=data["description"],
            status=data["status"],
            company_id=company.id,
            created_by=creator.id,
        )
        session.add(project)
        created += 1

    await session.flush()
    print(f"[project_seeder] seeded {created} project(s), skipped {len(PROJECTS) - created} existing.")

    result = await session.execute(select(Project))
    return list(result.scalars().all())
