import asyncio
import logging
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

HEADERS = {
    "X-Api-Key": settings.plane_api_token,
    "Content-Type": "application/json",
}

TIMEOUT = httpx.Timeout(30.0, connect=10.0)


async def _get_paginated(client: httpx.AsyncClient, url: str, params: Optional[dict] = None) -> list[dict]:
    """Fetch all pages from a paginated Plane endpoint."""
    results = []
    cursor = "1000:0:0"
    base_params = params or {}

    while True:
        page_params = {**base_params, "per_page": 1000, "cursor": cursor}
        response = await client.get(url, params=page_params)
        response.raise_for_status()
        data = response.json()

        # Handle both paginated and plain list responses
        if isinstance(data, list):
            results.extend(data)
            break
        elif isinstance(data, dict):
            page_results = data.get("results", data.get("data", []))
            results.extend(page_results)
            if not data.get("next_page_results", False):
                break
            cursor = data.get("next_cursor", "")
            if not cursor:
                break
        else:
            break

        await asyncio.sleep(0.1)

    return results


async def get_workspace(slug: str) -> dict:
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
        url = f"{settings.plane_base_url}/api/workspaces/{slug}/"
        logger.info(f"Fetching workspace: {slug}")
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


async def get_workspace_members(slug: str) -> list[dict]:
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
        url = f"{settings.plane_base_url}/api/workspaces/{slug}/members/"
        logger.info(f"Fetching workspace members: {slug}")
        return await _get_paginated(client, url)


async def get_projects(slug: str) -> list[dict]:
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
        url = f"{settings.plane_base_url}/api/v1/workspaces/{slug}/projects/"
        logger.info(f"Fetching projects for workspace: {slug}")
        return await _get_paginated(client, url)


async def get_project_members(slug: str, project_id: str) -> list[dict]:
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
        url = f"{settings.plane_base_url}/api/v1/workspaces/{slug}/projects/{project_id}/members/"
        logger.info(f"Fetching members for project: {project_id}")
        return await _get_paginated(client, url)


async def get_states(slug: str, project_id: str) -> list[dict]:
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
        url = f"{settings.plane_base_url}/api/v1/workspaces/{slug}/projects/{project_id}/states/"
        logger.info(f"Fetching states for project: {project_id}")
        return await _get_paginated(client, url)


async def get_labels(slug: str, project_id: str) -> list[dict]:
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
        url = f"{settings.plane_base_url}/api/v1/workspaces/{slug}/projects/{project_id}/labels/"
        logger.info(f"Fetching labels for project: {project_id}")
        return await _get_paginated(client, url)


async def get_modules(slug: str, project_id: str) -> list[dict]:
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
        url = f"{settings.plane_base_url}/api/v1/workspaces/{slug}/projects/{project_id}/modules/"
        logger.info(f"Fetching modules for project: {project_id}")
        return await _get_paginated(client, url)


async def get_module_issues(slug: str, project_id: str, module_id: str) -> list[dict]:
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
        url = f"{settings.plane_base_url}/api/v1/workspaces/{slug}/projects/{project_id}/modules/{module_id}/module-issues/"
        logger.info(f"Fetching issues for module: {module_id}")
        return await _get_paginated(client, url)


async def get_cycles(slug: str, project_id: str) -> list[dict]:
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
        url = f"{settings.plane_base_url}/api/v1/workspaces/{slug}/projects/{project_id}/cycles/"
        logger.info(f"Fetching cycles for project: {project_id}")
        return await _get_paginated(client, url)


async def get_cycle_issues(slug: str, project_id: str, cycle_id: str) -> list[dict]:
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
        url = f"{settings.plane_base_url}/api/v1/workspaces/{slug}/projects/{project_id}/cycles/{cycle_id}/cycle-issues/"
        logger.info(f"Fetching issues for cycle: {cycle_id}")
        return await _get_paginated(client, url)


async def get_views(slug: str, project_id: str) -> list[dict]:
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
        url = f"{settings.plane_base_url}/api/workspaces/{slug}/projects/{project_id}/views/"
        logger.info(f"Fetching views for project: {project_id}")
        return await _get_paginated(client, url)


async def get_issues(slug: str, project_id: str) -> list[dict]:
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
        url = f"{settings.plane_base_url}/api/v1/workspaces/{slug}/projects/{project_id}/issues/"
        logger.info(f"Fetching issues for project: {project_id}")
        return await _get_paginated(client, url)


async def get_issue_comments(slug: str, project_id: str, issue_id: str) -> list[dict]:
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
        url = f"{settings.plane_base_url}/api/v1/workspaces/{slug}/projects/{project_id}/work-items/{issue_id}/comments/"
        logger.info(f"Fetching comments for issue: {issue_id}")
        return await _get_paginated(client, url)


async def get_issue_sub_issues(slug: str, project_id: str, issue_id: str) -> list[dict]:
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
        url = f"{settings.plane_base_url}/api/v1/workspaces/{slug}/projects/{project_id}/issues/{issue_id}/sub-issues/"
        logger.info(f"Fetching sub-issues for issue: {issue_id}")
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return data
            return data.get("results", data.get("sub_issues", []))
        except httpx.HTTPStatusError:
            return []
