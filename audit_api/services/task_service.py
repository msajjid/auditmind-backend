# audit_api/services/task_service.py

from typing import Iterable, Optional
from uuid import UUID

from audit_api.models import Task


class TaskService:
    def list_by_org(self, organization_id: UUID) -> Iterable[Task]:
        return (
            Task.objects
            .filter(organization_id=organization_id)
            .order_by("-created_at")
        )

    def get(self, task_id: UUID) -> Task:
        return Task.objects.get(pk=task_id)

    def create(
        self,
        *,
        organization_id: UUID,
        title: str,
        description: Optional[str],
        framework_id: Optional[UUID] = None,
        control_id: Optional[UUID] = None,
        assignee_id: Optional[UUID] = None,
    ) -> Task:
        return Task.objects.create(
            organization_id=organization_id,
            framework_id=framework_id,
            control_id=control_id,
            title=title,
            description=description,
            assignee_id=assignee_id,
            status="open",
        )