import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from app import plane_client as pc
from app.models import (
    CommentModel,
    CycleModel,
    IssueModel,
    LabelModel,
    MemberModel,
    ModuleModel,
    ProjectModel,
    StateModel,
    ViewModel,
    WorkspaceModel,
    WorkspaceResponse,
)

logger = logging.getLogger(__name__)

ROLE_MAP = {10: "Viewer", 15: "Guest", 20: "Member", 30: "Admin", 5: "Guest"}


def _member(raw: dict) -> MemberModel:
    member_data = raw.get("member", raw)
    role = raw.get("role")
    return MemberModel(
        id=member_data.get("id", ""),
        display_name=member_data.get("display_name") or member_data.get("username"),
        email=member_data.get("email"),
        avatar=member_data.get("avatar"),
        role=role,
        role_display=ROLE_MAP.get(role, str(role)) if role else None,
    )


def _state(raw: dict) -> StateModel:
    return StateModel(
        id=raw.get("id", ""),
        name=raw.get("name", ""),
        color=raw.get("color"),
        group=raw.get("group"),
        sequence=raw.get("sequence"),
    )


def _label(raw: dict) -> LabelModel:
    return LabelModel(
        id=raw.get("id", ""),
        name=raw.get("name", ""),
        color=raw.get("color"),
        parent=raw.get("parent"),
    )


def _view(raw: dict) -> ViewModel:
    return ViewModel(
        id=raw.get("id", ""),
        name=raw.get("name", ""),
        description=raw.get("description"),
        filters=raw.get("filters"),
        created_at=raw.get("created_at"),
    )


def _comment(raw: dict) -> CommentModel:
    actor = raw.get("actor_detail", {})
    return CommentModel(
        id=raw.get("id", ""),
        actor=actor.get("display_name") or actor.get("email") if actor else raw.get("actor"),
        comment_html=raw.get("comment_html"),
        comment_stripped=raw.get("comment_stripped"),
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
    )


async def _build_issue(slug: str, project_id: str, raw: dict, errors: list) -> IssueModel:
    issue_id = raw.get("id", "")

    # Fetch comments concurrently with sub-issues
    try:
        comments_raw, sub_issues_raw = await asyncio.gather(
            pc.get_issue_comments(slug, project_id, issue_id),
            pc.get_issue_sub_issues(slug, project_id, issue_id),
        )
    except Exception as exc:
        logger.warning(f"Failed fetching details for issue {issue_id}: {exc}")
        errors.append({"resource": f"issue_details:{issue_id}", "error": str(exc)})
        comments_raw, sub_issues_raw = [], []

    state_detail = raw.get("state_detail")
    state_name = None
    if state_detail:
        state_name = state_detail.get("name")
    elif raw.get("state"):
        state_name = raw.get("state")

    return IssueModel(
        id=issue_id,
        sequence_id=raw.get("sequence_id"),
        name=raw.get("name", ""),
        description_html=raw.get("description_html"),
        description_stripped=raw.get("description_stripped"),
        state=state_name,
        state_detail=state_detail,
        priority=raw.get("priority"),
        assignees=raw.get("assignees", []),
        label_ids=raw.get("label_ids", raw.get("labels", [])),
        module=raw.get("module_id"),
        cycle=raw.get("cycle_id"),
        comments=[_comment(c) for c in comments_raw],
        sub_issues=[si.get("id", "") for si in sub_issues_raw if isinstance(si, dict)],
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
        due_date=raw.get("target_date") or raw.get("due_date"),
        start_date=raw.get("start_date"),
        completed_at=raw.get("completed_at"),
    )


async def _build_project(slug: str, raw: dict, errors: list) -> ProjectModel:
    project_id = raw.get("id", "")
    logger.info(f"Building project: {raw.get('name')} ({project_id})")

    # Fetch all project-level resources in parallel
    async def safe_fetch(name: str, coro):
        try:
            return await coro
        except Exception as exc:
            logger.warning(f"Failed fetching {name} for project {project_id}: {exc}")
            errors.append({"resource": f"{name}:{project_id}", "error": str(exc)})
            return []

    states_raw, labels_raw, members_raw, modules_raw, cycles_raw, views_raw, issues_raw = await asyncio.gather(
        safe_fetch("states", pc.get_states(slug, project_id)),
        safe_fetch("labels", pc.get_labels(slug, project_id)),
        safe_fetch("members", pc.get_project_members(slug, project_id)),
        safe_fetch("modules", pc.get_modules(slug, project_id)),
        safe_fetch("cycles", pc.get_cycles(slug, project_id)),
        safe_fetch("views", pc.get_views(slug, project_id)),
        safe_fetch("issues", pc.get_issues(slug, project_id)),
    )

    # Build module objects and fetch their issues
    async def build_module(m: dict) -> ModuleModel:
        module_id = m.get("id", "")
        try:
            mi_raw = await pc.get_module_issues(slug, project_id, module_id)
            issue_ids = [mi.get("issue_id") or mi.get("issue") or mi.get("id", "") for mi in mi_raw]
        except Exception as exc:
            logger.warning(f"Failed fetching module issues {module_id}: {exc}")
            errors.append({"resource": f"module_issues:{module_id}", "error": str(exc)})
            issue_ids = []
        return ModuleModel(
            id=module_id,
            name=m.get("name", ""),
            description=m.get("description"),
            status=m.get("status"),
            start_date=m.get("start_date"),
            target_date=m.get("target_date"),
            issues=issue_ids,
        )

    async def build_cycle(c: dict) -> CycleModel:
        cycle_id = c.get("id", "")
        try:
            ci_raw = await pc.get_cycle_issues(slug, project_id, cycle_id)
            issue_ids = [ci.get("issue_id") or ci.get("issue") or ci.get("id", "") for ci in ci_raw]
        except Exception as exc:
            logger.warning(f"Failed fetching cycle issues {cycle_id}: {exc}")
            errors.append({"resource": f"cycle_issues:{cycle_id}", "error": str(exc)})
            issue_ids = []
        return CycleModel(
            id=cycle_id,
            name=c.get("name", ""),
            description=c.get("description"),
            status=c.get("status"),
            start_date=c.get("start_date"),
            end_date=c.get("end_date"),
            issues=issue_ids,
        )

    modules, cycles = await asyncio.gather(
        asyncio.gather(*[build_module(m) for m in modules_raw]),
        asyncio.gather(*[build_cycle(c) for c in cycles_raw]),
    )

    # Build issues with comments and sub-issues
    # Process in batches of 10 to avoid overwhelming Plane
    issues: list[IssueModel] = []
    batch_size = 10
    for i in range(0, len(issues_raw), batch_size):
        batch = issues_raw[i : i + batch_size]
        batch_results = await asyncio.gather(
            *[_build_issue(slug, project_id, issue, errors) for issue in batch]
        )
        issues.extend(batch_results)
        if i + batch_size < len(issues_raw):
            await asyncio.sleep(0.2)

    return ProjectModel(
        id=project_id,
        name=raw.get("name", ""),
        identifier=raw.get("identifier"),
        description=raw.get("description"),
        network=raw.get("network"),
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
        states=[_state(s) for s in states_raw],
        labels=[_label(l) for l in labels_raw],
        members=[_member(m) for m in members_raw],
        modules=list(modules),
        cycles=list(cycles),
        views=[_view(v) for v in views_raw],
        issues=issues,
    )


async def extract_workspace(slug: str) -> WorkspaceResponse:
    errors: list[dict[str, Any]] = []
    logger.info(f"Starting full extraction for workspace: {slug}")

    # Fetch workspace info and members in parallel
    try:
        ws_raw, members_raw = await asyncio.gather(
            pc.get_workspace(slug),
            pc.get_workspace_members(slug),
        )
    except Exception as exc:
        logger.error(f"Failed to fetch workspace {slug}: {exc}")
        errors.append({"resource": f"workspace:{slug}", "error": str(exc)})
        ws_raw = {"slug": slug, "name": slug}
        members_raw = []

    # Fetch all projects
    try:
        projects_raw = await pc.get_projects(slug)
    except Exception as exc:
        logger.error(f"Failed to fetch projects for {slug}: {exc}")
        errors.append({"resource": f"projects:{slug}", "error": str(exc)})
        projects_raw = []

    logger.info(f"Found {len(projects_raw)} projects in workspace {slug}")

    # Build each project (sequential to avoid rate limiting)
    projects: list[ProjectModel] = []
    for proj_raw in projects_raw:
        try:
            project = await _build_project(slug, proj_raw, errors)
            projects.append(project)
        except Exception as exc:
            pid = proj_raw.get("id", "unknown")
            logger.error(f"Failed building project {pid}: {exc}")
            errors.append({"resource": f"project:{pid}", "error": str(exc)})

    total_issues = sum(len(p.issues) for p in projects)
    logger.info(f"Extraction complete: {len(projects)} projects, {total_issues} issues, {len(errors)} errors")

    workspace = WorkspaceModel(
        slug=ws_raw.get("slug", slug),
        name=ws_raw.get("name", slug),
        id=ws_raw.get("id"),
        logo=ws_raw.get("logo"),
        created_at=ws_raw.get("created_at"),
        members=[_member(m) for m in members_raw],
        projects=projects,
    )

    return WorkspaceResponse(
        workspace=workspace,
        extracted_at=datetime.now(timezone.utc),
        total_issues=total_issues,
        total_projects=len(projects),
        errors=errors,
    )
