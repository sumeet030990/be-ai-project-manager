from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from database.models.role import Role
from database.models.user import User

USERS = [
    {
        "email": "admin@example.com",
        "contact_no": "9000000001",
        "first_name": "System",
        "middle_name": None,
        "last_name": "Admin",
        "password": "Admin@1234",
        "role_slug": "admin",
    },
    {
        "email": "manager@example.com",
        "contact_no": "9000000002",
        "first_name": "Project",
        "middle_name": None,
        "last_name": "Manager",
        "password": "Manager@1234",
        "role_slug": "manager",
    },
    {
        "email": "developer@example.com",
        "contact_no": "9000000003",
        "first_name": "John",
        "middle_name": None,
        "last_name": "Developer",
        "password": "Developer@1234",
        "role_slug": "developer",
    },
    {
        "email": "qa@example.com",
        "contact_no": "9000000004",
        "first_name": "Jane",
        "middle_name": None,
        "last_name": "Qa",
        "password": "Qa@1234",
        "role_slug": "qa",
    },
]


async def seed_users(session: AsyncSession, roles: list[Role]) -> list[User]:
    role_map = {r.slug: r for r in roles}

    result = await session.execute(select(User))
    existing_emails = {u.email for u in result.scalars().all()}

    created = 0
    for data in USERS:
        if data["email"] in existing_emails:
            continue

        role = role_map.get(data["role_slug"])
        if not role:
            print(f"[user_seeder] role '{data['role_slug']}' not found — skipping {data['email']}.")
            continue

        user = User(
            email=data["email"],
            contact_no=data["contact_no"],
            first_name=data["first_name"],
            middle_name=data["middle_name"],
            last_name=data["last_name"],
            hashed_password=hash_password(data["password"]),
            role_id=role.id,
        )
        session.add(user)
        created += 1

    await session.flush()
    print(f"[user_seeder] seeded {created} user(s), skipped {len(USERS) - created} existing.")

    result = await session.execute(select(User))
    return list(result.scalars().all())
