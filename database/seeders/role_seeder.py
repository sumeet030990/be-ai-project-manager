from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.role import Role

ROLES = [
    {"name": "Admin", "slug": "admin"},
    {"name": "Manager", "slug": "manager"},
    {"name": "Developer", "slug": "developer"},
    {"name": "QA", "slug": "qa"},
]


async def seed_roles(session: AsyncSession) -> list[Role]:
    result = await session.execute(select(Role))
    existing_slugs = {r.slug for r in result.scalars().all()}

    created: list[Role] = []
    for data in ROLES:
        if data["slug"] not in existing_slugs:
            role = Role(name=data["name"], slug=data["slug"])
            session.add(role)
            created.append(role)

    await session.flush()
    print(f"[role_seeder] seeded {len(created)} role(s), skipped {len(ROLES) - len(created)} existing.")

    result = await session.execute(select(Role))
    return list(result.scalars().all())
