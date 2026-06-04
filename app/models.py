from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class CommentModel(BaseModel):
    id: str
    actor: Optional[str] = None
    comment_html: Optional[str] = None
    comment_stripped: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IssueModel(BaseModel):
    id: str
    sequence_id: Optional[int] = None
    name: str
    description_html: Optional[str] = None
    description_stripped: Optional[str] = None
    state: Optional[str] = None
    state_detail: Optional[dict] = None
    priority: Optional[str] = None
    assignees: list[str] = []
    label_ids: list[str] = []
    module: Optional[str] = None
    cycle: Optional[str] = None
    comments: list[CommentModel] = []
    sub_issues: list[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    due_date: Optional[str] = None
    start_date: Optional[str] = None
    completed_at: Optional[datetime] = None


class StateModel(BaseModel):
    id: str
    name: str
    color: Optional[str] = None
    group: Optional[str] = None
    sequence: Optional[float] = None


class LabelModel(BaseModel):
    id: str
    name: str
    color: Optional[str] = None
    parent: Optional[str] = None


class ModuleModel(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    target_date: Optional[str] = None
    issues: list[str] = []


class CycleModel(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    issues: list[str] = []


class ViewModel(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    filters: Optional[dict] = None
    created_at: Optional[datetime] = None


class MemberModel(BaseModel):
    id: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[int] = None
    role_display: Optional[str] = None


class ProjectModel(BaseModel):
    id: str
    name: str
    identifier: Optional[str] = None
    description: Optional[str] = None
    network: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    states: list[StateModel] = []
    labels: list[LabelModel] = []
    members: list[MemberModel] = []
    modules: list[ModuleModel] = []
    cycles: list[CycleModel] = []
    views: list[ViewModel] = []
    issues: list[IssueModel] = []


class WorkspaceModel(BaseModel):
    slug: str
    name: str
    id: Optional[str] = None
    logo: Optional[str] = None
    created_at: Optional[datetime] = None
    members: list[MemberModel] = []
    projects: list[ProjectModel] = []


class WorkspaceResponse(BaseModel):
    workspace: WorkspaceModel
    extracted_at: datetime
    total_issues: int
    total_projects: int
    errors: list[dict[str, Any]] = []


class ProjectsResponse(BaseModel):
    workspace_slug: str
    projects: list[ProjectModel]
    extracted_at: datetime
    total_projects: int
    errors: list[dict[str, Any]] = []


class IssuesResponse(BaseModel):
    workspace_slug: str
    issues: list[IssueModel]
    extracted_at: datetime
    total_issues: int
    errors: list[dict[str, Any]] = []
