import logging
from datetime import datetime, timezone

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.aggregator import extract_workspace
from app.auth import verify_api_key
from app.config import settings
from app.models import IssuesResponse, ProjectsResponse, WorkspaceResponse
from app import plane_client as pc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Plane Bridge API",
    description="Aggregator bridge between Plane and Claude Desktop",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get(
    "/workspace/{workspace_slug}",
    response_model=WorkspaceResponse,
    summary="Extract full workspace data",
)
async def get_workspace_full(
    workspace_slug: str = settings.default_workspace_slug,
    _: str = Depends(verify_api_key),
):
    return await extract_workspace(workspace_slug)


@app.get(
    "/workspace/{workspace_slug}/projects",
    response_model=ProjectsResponse,
    summary="List all projects in workspace",
)
async def get_workspace_projects(
    workspace_slug: str = settings.default_workspace_slug,
    _: str = Depends(verify_api_key),
):
    errors = []
    try:
        projects_raw = await pc.get_projects(workspace_slug)
    except Exception as exc:
        errors.append({"resource": "projects", "error": str(exc)})
        projects_raw = []

    from app.aggregator import _build_project

    projects = []
    for raw in projects_raw:
        try:
            proj = await _build_project(workspace_slug, raw, errors)
            projects.append(proj)
        except Exception as exc:
            errors.append({"resource": f"project:{raw.get('id')}", "error": str(exc)})

    return ProjectsResponse(
        workspace_slug=workspace_slug,
        projects=projects,
        extracted_at=datetime.now(timezone.utc),
        total_projects=len(projects),
        errors=errors,
    )


@app.get(
    "/workspace/{workspace_slug}/issues",
    response_model=IssuesResponse,
    summary="List all issues across all projects",
)
async def get_workspace_issues(
    workspace_slug: str = settings.default_workspace_slug,
    _: str = Depends(verify_api_key),
):
    errors = []
    all_issues = []

    try:
        projects_raw = await pc.get_projects(workspace_slug)
    except Exception as exc:
        errors.append({"resource": "projects", "error": str(exc)})
        projects_raw = []

    from app.aggregator import _build_issue
    import asyncio

    for proj in projects_raw:
        project_id = proj.get("id", "")
        try:
            issues_raw = await pc.get_issues(workspace_slug, project_id)
            batch_size = 10
            for i in range(0, len(issues_raw), batch_size):
                batch = issues_raw[i : i + batch_size]
                results = await asyncio.gather(
                    *[_build_issue(workspace_slug, project_id, issue, errors) for issue in batch]
                )
                all_issues.extend(results)
        except Exception as exc:
            errors.append({"resource": f"issues:{project_id}", "error": str(exc)})

    return IssuesResponse(
        workspace_slug=workspace_slug,
        issues=all_issues,
        extracted_at=datetime.now(timezone.utc),
        total_issues=len(all_issues),
        errors=errors,
    )
