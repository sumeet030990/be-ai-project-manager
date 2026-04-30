from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.project import Project
from database.models.project_user import ProjectUser
from database.models.user import User

# (project_name, user_email)
PROJECT_USERS = [
    ("AI Project Manager", "admin@example.com"),
    ("AI Project Manager", "manager@example.com"),
    ("AI Project Manager", "developer@example.com"),
    ("AI Project Manager", "qa@example.com"),
    ("Goibibo", "admin@example.com"),
    ("Goibibo", "manager@example.com"),
    ("Goibibo", "developer@example.com"),
    ("Goibibo", "qa@example.com"),
]


async def seed_project_users(
    session: AsyncSession,
    projects: list[Project],
    users: list[User],
) -> None:
    project_map = {p.name: p for p in projects}
    user_map = {u.email: u for u in users}

    result = await session.execute(select(ProjectUser))
    existing_pairs = {(pu.project_id, pu.user_id) for pu in result.scalars().all()}

    created = 0
    for project_name, user_email in PROJECT_USERS:
        project = project_map.get(project_name)
        user = user_map.get(user_email)

        if not project:
            print(f"[project_user_seeder] project '{project_name}' not found — skipping.")
            continue
        if not user:
            print(f"[project_user_seeder] user '{user_email}' not found — skipping.")
            continue
        if (project.id, user.id) in existing_pairs:
            continue

        session.add(ProjectUser(project_id=project.id, user_id=user.id))
        created += 1

    await session.flush()
    skipped = len(PROJECT_USERS) - created
    print(f"[project_user_seeder] seeded {created} assignment(s), skipped {skipped} existing.")
