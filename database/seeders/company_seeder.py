from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.company import Company

COMPANIES = [
    {
        "name": "Neighborly Software",
        "gst_no": "27AABCN1234A1Z5",
        "email": "info@neighborlysoftware.com",
        "phone": "9100000001",
        "website": "https://www.neighborlysoftware.com",
        "address_line_1": "101 Tech Park",
        "address_line_2": "Building A",
        "city": "Pune",
        "state": "Maharashtra",
        "country": "India",
        "pincode": "411001",
    },
    {
        "name": "Acme Corp",
        "gst_no": None,
        "email": "contact@acmecorp.com",
        "phone": "9100000002",
        "website": None,
        "address_line_1": "202 Business Hub",
        "address_line_2": None,
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "pincode": "400001",
    },
]


async def seed_companies(session: AsyncSession) -> list[Company]:
    result = await session.execute(select(Company))
    existing_emails = {c.email for c in result.scalars().all()}

    created: list[Company] = []
    for data in COMPANIES:
        if data["email"] not in existing_emails:
            company = Company(**data)
            session.add(company)
            created.append(company)

    await session.flush()
    print(f"[company_seeder] seeded {len(created)} company(ies), skipped {len(COMPANIES) - len(created)} existing.")

    result = await session.execute(select(Company))
    return list(result.scalars().all())
