# audit_api/urls.py

from django.urls import path
from .views import (
    HealthCheckView,
    EvidenceListCreateView,
    EvidenceClassifyView,
    EvidenceFileUploadView,
    EvidenceAgentRunsView,
    AgentRunStepLogsView,
    EvidenceEventsView,
    EvidenceTimelineView,
    JobStatusView,
    PromptTemplateListCreateView,
    ModelRegistryListCreateView,
    OrganizationMembershipView,
    OrganizationMembershipDeactivateView,
    OrganizationListCreateView,
    TaskListView,
    RegisterView,
    LoginView,
    MeView,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("organizations/", OrganizationListCreateView.as_view(), name="organization-list-create"),
    path("evidence/", EvidenceListCreateView.as_view(), name="evidence-list-create"),
    path("evidence/upload/", EvidenceFileUploadView.as_view(), name="evidence-file-upload"),
    path(
        "evidence/<uuid:evidence_id>/classify/",
        EvidenceClassifyView.as_view(),
        name="evidence-classify",
    ),
    path(
        "evidence/<uuid:evidence_id>/agent-runs/",
        EvidenceAgentRunsView.as_view(),
        name="evidence-agent-runs",
    ),
    path(
        "evidence/<uuid:evidence_id>/timeline/",
        EvidenceTimelineView.as_view(),
        name="evidence-timeline",
    ),
    path(
        "agent-runs/<uuid:agent_run_id>/steps/",
        AgentRunStepLogsView.as_view(),
        name="agent-run-steps",
    ),
    path(
        "evidence/<uuid:evidence_id>/events/",
        EvidenceEventsView.as_view(),
        name="evidence-events",
    ),
    path(
        "organizations/<uuid:org_id>/memberships/",
        OrganizationMembershipView.as_view(),
        name="organization-memberships",
    ),
    path(
        "organizations/<uuid:org_id>/memberships/<uuid:membership_id>/deactivate/",
        OrganizationMembershipDeactivateView.as_view(),
        name="organization-membership-deactivate",
    ),
    path("tasks/", TaskListView.as_view(), name="task-list"),
    path(
        "jobs/<str:job_id>/",
        JobStatusView.as_view(),
        name="job-status",
    ),
    path("prompts/", PromptTemplateListCreateView.as_view(), name="prompt-list-create"),
    path("models/", ModelRegistryListCreateView.as_view(), name="model-registry-list-create"),
]
