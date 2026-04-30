import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.core.database import AsyncSessionFactory
from database.seeders.company_seeder import seed_companies
from database.seeders.project_seeder import seed_projects
from database.seeders.project_user_seeder import seed_project_users
from database.seeders.role_seeder import seed_roles
from database.seeders.user_seeder import seed_users


async def run() -> None:
    async with AsyncSessionFactory() as session:
        try:
            companies = await seed_companies(session)
            roles = await seed_roles(session)
            users = await seed_users(session, roles)
            projects = await seed_projects(session, companies, users)
            await seed_project_users(session, projects, users)
            await session.commit()
            print("[runner] seeding completed successfully.")
        except Exception:
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(run())
