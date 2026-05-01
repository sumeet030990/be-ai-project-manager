from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.company import Company
from database.models.project import Project
from database.models.user import User

PROJECTS = [
    {
        "name": "SmartFlyers",
        "description": "An App which provides flight booking and travel planning services.",
        "project_info": (
            "SmartFlyers is an Indian online travel aggregator (OTA) offering end-to-end booking for flights, hotels, trains, buses, and cabs across domestic and international routes. "
            "It serves consumers via mobile apps and a web platform, competing in the price-sensitive Indian travel market.\n\n"
            "CORE BUSINESS DOMAINS:\n"
            "- Flights: Domestic and international ticket booking with real-time seat availability and fare comparison.\n"
            "- Hotels: Aggregated listings with last-minute deals and price-match guarantees.\n"
            "- Transport: Bus bookings (including premium 'Primo' buses), train tickets, and cab rentals.\n"
            "- Ancillaries: Travel insurance, seat upgrades, meal add-ons.\n\n"
            "KEY BUSINESS RULES:\n"
            "- sfCash rewards: Users earn sfCash on bookings; redeemable on future transactions with per-booking caps.\n"
            "- Cancellation & refunds: Governed by supplier policies (airline/hotel); SmartFlyers processes refunds within defined SLAs.\n"
            "- Payment: Supports UPI, net banking, credit/debit cards, and wallets; fast-checkout is a key differentiator.\n"
            "- Pricing: Dynamic pricing from supplier APIs; SmartFlyers adds a service fee layer on top.\n"
            "- Inventory: Real-time availability from GDS (flights), hotel aggregator APIs, and transport operator APIs.\n\n"
            "USERS & ROLES:\n"
            "- Travelers: Primary end-users who search, compare, and book travel products.\n"
            "- Suppliers: Airlines, hotel chains, bus operators, and cab providers integrated via APIs.\n"
            "- Admins: Internal team managing promotions, refunds, content, and fraud flags.\n\n"
            "PLATFORM CONSTRAINTS:\n"
            "- High concurrency during sale events and holiday seasons (Diwali, summer vacations).\n"
            "- Regulatory compliance with Indian aviation (DGCA) and GST invoicing requirements.\n"
            "- Latency-sensitive: Booking confirmation must complete within seconds to prevent fare expiry."
        ),
        "status": "active",
        "company_email": "info@neighborlysoftware.com",
        "created_by_email": "admin@example.com",
    }, 
    {
        "name": "AI Project Manager",
        "description": "Internal AI-powered project management tool.",
        "project_info": "This project focuses on enhancing productivity and collaboration within teams by leveraging AI-driven insights and automation.",
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
            project_info=data["project_info"],
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
