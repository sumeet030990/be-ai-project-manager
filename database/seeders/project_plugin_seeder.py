from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.project import Project
from database.models.project_plugin import ProjectPlugin
from database.models.project_tech_stack import ProjectTechStack

PLUGINS = [
    {
        "project_name": "AI Project Manager",
        "plugins": [
            # ── Backend (pip) — linked to FastAPI tech stack ─────────────────
            {"name": "fastapi", "version": "0.136.1", "ecosystem": "pip", "tech_stack": "FastAPI", "description": "Python async web framework."},
            {"name": "uvicorn", "version": "0.46.0", "ecosystem": "pip", "tech_stack": "FastAPI", "description": "ASGI server with standard extras."},
            {"name": "pydantic", "version": "2.13.3", "ecosystem": "pip", "tech_stack": "FastAPI", "description": "Data validation and settings management."},
            {"name": "sqlalchemy", "version": "2.0.49", "ecosystem": "pip", "tech_stack": "FastAPI", "description": "Async ORM and SQL toolkit."},
            {"name": "alembic", "version": "1.18.4", "ecosystem": "pip", "tech_stack": "FastAPI", "description": "Database migration tool for SQLAlchemy."},
            # ── Frontend (npm) — linked to React tech stack ──────────────────
            {"name": "next", "version": "16.0.3", "ecosystem": "npm", "tech_stack": "React", "description": "React full-stack framework (App Router)."},
            {"name": "@mui/material", "version": "7.3.5", "ecosystem": "npm", "tech_stack": "React", "description": "MUI component library."},
            {"name": "@mui/icons-material", "version": "7.3.5", "ecosystem": "npm", "tech_stack": "React", "description": "MUI icon set."},
            {"name": "@tanstack/react-query", "version": "5.100.7", "ecosystem": "npm", "tech_stack": "React", "description": "Server state management and data fetching."},
            {"name": "@emotion/react", "version": "11.14.0", "ecosystem": "npm", "tech_stack": "React", "description": "CSS-in-JS library (MUI peer dependency)."},
            {"name": "@emotion/styled", "version": "11.14.1", "ecosystem": "npm", "tech_stack": "React", "description": "Styled components for Emotion (MUI peer dependency)."},
            {"name": "apexcharts", "version": "5.3.6", "ecosystem": "npm", "tech_stack": "React", "description": "Charting library for dashboards."},
            {"name": "react-apexcharts", "version": "1.8.0", "ecosystem": "npm", "tech_stack": "React", "description": "React wrapper for ApexCharts."},
            {"name": "@tabler/icons-react", "version": "3.35.0", "ecosystem": "npm", "tech_stack": "React", "description": "Tabler icon set for React."},
            {"name": "typescript", "version": "5.9.3", "ecosystem": "npm", "tech_stack": "Node.js", "description": "Typed superset of JavaScript."},
        ],
    },
]


async def seed_project_plugins(session: AsyncSession, projects: list[Project]) -> None:
    project_map = {p.name: p for p in projects}

    created = 0
    skipped = 0

    for entry in PLUGINS:
        project = project_map.get(entry["project_name"])
        if not project:
            print(f"[plugin_seeder] project '{entry['project_name']}' not found — skipping.")
            continue

        # Build a name→id map for this project's tech stacks
        stack_result = await session.execute(
            select(ProjectTechStack).where(ProjectTechStack.project_id == project.id)
        )
        stack_map = {s.name: s.id for s in stack_result.scalars().all()}

        existing_result = await session.execute(
            select(ProjectPlugin).where(ProjectPlugin.project_id == project.id)
        )
        existing_names = {p.name for p in existing_result.scalars().all()}

        for plugin_data in entry["plugins"]:
            if plugin_data["name"] in existing_names:
                skipped += 1
                continue

            tech_stack_id = stack_map.get(plugin_data.get("tech_stack"))
            if not tech_stack_id:
                print(f"[plugin_seeder] tech stack '{plugin_data.get('tech_stack')}' not found — '{plugin_data['name']}' will have no tech_stack_id.")

            session.add(ProjectPlugin(
                project_id=project.id,
                tech_stack_id=tech_stack_id,
                name=plugin_data["name"],
                version=plugin_data["version"],
                ecosystem=plugin_data["ecosystem"],
                description=plugin_data.get("description"),
            ))
            created += 1

    await session.flush()
    print(f"[plugin_seeder] seeded {created} plugin(s), skipped {skipped} existing.")
