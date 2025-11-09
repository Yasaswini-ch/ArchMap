from __future__ import annotations

from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.services.projects import (
    create_project as _create_project,
    list_projects as _list_projects,
    get_project as _get_project,
    update_project as _update_project,
    delete_project as _delete_project,
)


async def create_project(
    session: AsyncSession,
    *,
    owner_id: Optional[UUID],
    name: str,
    repo_url: Optional[str] = None,
    description: Optional[str] = None,
) -> Project:
    return await _create_project(
        session,
        owner_id=owner_id,
        name=name,
        repo_url=repo_url,
        description=description,
    )


async def list_projects(
    session: AsyncSession,
    *,
    owner_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Project]:
    return await _list_projects(session, owner_id=owner_id, limit=limit, offset=offset)


async def get_project(session: AsyncSession, project_id: UUID, *, owner_id: Optional[UUID] = None) -> Optional[Project]:
    return await _get_project(session, project_id, owner_id=owner_id)


async def update_project(
    session: AsyncSession,
    project_id: UUID,
    *,
    owner_id: Optional[UUID] = None,
    name: Optional[str] = None,
    repo_url: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[Project]:
    return await _update_project(
        session,
        project_id,
        owner_id=owner_id,
        name=name,
        repo_url=repo_url,
        description=description,
    )


async def delete_project(session: AsyncSession, project_id: UUID, *, owner_id: Optional[UUID] = None) -> bool:
    return await _delete_project(session, project_id, owner_id=owner_id)
