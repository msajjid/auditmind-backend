# audit_api/urls.py

from django.urls import path
from .views import (
    HealthCheckView,
    EvidenceListCreateView,
    EvidenceClassifyView,
    OrganizationListCreateView,
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
    path(
        "evidence/<uuid:evidence_id>/classify/",
        EvidenceClassifyView.as_view(),
        name="evidence-classify",
    ),
]
