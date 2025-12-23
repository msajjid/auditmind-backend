import django_rq

from audit_api.models import Task


def classify_evidence_task(evidence_id: str) -> dict:
    """Background job to classify evidence."""
    from audit_api.orchestration.coordinator import OrchestrationCoordinator

    coordinator = OrchestrationCoordinator()
    return coordinator.classify_evidence(evidence_id=evidence_id)


def enqueue_classification(evidence_id: str):
    queue = django_rq.get_queue("default")
    job = queue.enqueue(classify_evidence_task, evidence_id)
    return job


def process_task_task(task_id: str) -> dict:
    """
    Background job stub for downstream task processing.
    Extend this to create tickets/notifications/etc.
    """
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return {"status": "missing", "task_id": task_id}

    return {
        "status": "acknowledged",
        "task_id": task_id,
        "title": task.title,
        "control": task.control.reference if task.control else None,
        "framework": task.framework.code if task.framework else None,
    }


def enqueue_task_processing(task_id: str):
    queue = django_rq.get_queue("default")
    job = queue.enqueue("audit_api.tasks.process_task_task", task_id)
    return job
