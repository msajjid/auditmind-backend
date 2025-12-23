from typing import Iterable, List
from audit_api.models import Evidence, Control, Task
from audit_api.tasks import enqueue_task_processing


class TaskAutoCreateService:
    """
    Creates remediation / evidence-collection tasks based on classified controls.
    """

    def create_tasks_for_controls(
        self,
        *,
        evidence: Evidence,
        controls: Iterable[Control],
    ) -> List[Task]:
        created: List[Task] = []

        for control in controls:
            title = f"Collect evidence for {control.reference}: {control.title}"

            # Prevent duplicates (simple rule: same org + same control + same title)
            exists = Task.objects.filter(
                organization=evidence.organization,
                control=control,
                title=title,
            ).exists()
            if exists:
                continue

            task = Task.objects.create(
                organization=evidence.organization,
                framework=control.framework,
                control=control,
                evidence=evidence,
                title=title,
                description=(
                    "Auto-created from evidence classification.\n\n"
                    f"Evidence: {evidence.title}\n"
                    f"Storage: {evidence.storage_path}"
                ),
                status="open",
            )
            created.append(task)
            try:
                enqueue_task_processing(str(task.id))
            except Exception:
                # Do not block pipeline on queue issues
                pass

        return created
