# audit_api/views.py

from uuid import UUID

from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Prefetch
from django.contrib.auth import get_user_model
import django_rq

from audit_api.serializers import (
    EvidenceCreateSerializer,
    EvidenceSerializer,
    EvidenceFileUploadSerializer,
    OrganizationCreateSerializer,
    OrganizationSerializer,
    OrganizationMembershipSerializer,
    OrganizationMembershipDetailSerializer,
    AuthUserSerializer,
    AgentRunSerializer,
    AgentRunDetailSerializer,
    AgentStepLogSerializer,
    EventSerializer,
    OrganizationInviteSerializer,
    PromptTemplateSerializer,
    ModelRegistrySerializer,
    TaskSerializer,
)
from audit_api.services import EvidenceService, OrganizationService, TaskService
from audit_api.orchestration.coordinator import OrchestrationCoordinator
from audit_api.models import (
    Evidence,
    Organization,
    OrganizationMembership,
    AgentRun,
    AgentStepLog,
    Event,
    PromptTemplate,
    ModelRegistry,
    Task,
)
from audit_api.tasks import enqueue_classification, classify_evidence_task
from django_rq import get_queue

UserModel = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        full_name = request.data.get("full_name", "")
        organization_name = request.data.get("organization_name")
        domain = (request.data.get("domain") or "").strip() or None

        if not email or not password or not organization_name:
            return Response(
                {"detail": "email, password, and organization_name are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = UserModel.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=full_name,
            )
        except IntegrityError:
            return Response({"detail": "User already exists."}, status=status.HTTP_400_BAD_REQUEST)

        org_service = OrganizationService()
        try:
            org = org_service.create(name=organization_name, domain=domain, plan="team")
        except IntegrityError:
            return Response(
                {"detail": "An organization with this domain already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        org_service.add_admin_membership(org, user)

        token, _ = Token.objects.get_or_create(user=user)
        memberships = OrganizationMembership.objects.filter(user=user, is_active=True)
        return Response(
            {
                "token": token.key,
                "user": AuthUserSerializer(user).data,
                "memberships": OrganizationMembershipSerializer(memberships, many=True).data,
                "active_organization_id": str(org.id),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        if not email or not password:
            return Response({"detail": "email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        token, _ = Token.objects.get_or_create(user=user)
        memberships = OrganizationMembership.objects.filter(user=user, is_active=True)
        return Response(
            {
                "token": token.key,
                "user": AuthUserSerializer(user).data,
                "memberships": OrganizationMembershipSerializer(memberships, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    def get(self, request, *args, **kwargs):
        memberships = OrganizationMembership.objects.filter(user=request.user, is_active=True)
        return Response(
            {
                "user": AuthUserSerializer(request.user).data,
                "memberships": OrganizationMembershipSerializer(memberships, many=True).data,
            }
        )


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class OrganizationListCreateView(APIView):
    """
    GET /api/organizations/
    POST /api/organizations/
    """

    def get(self, request, *args, **kwargs):
        service = OrganizationService()
        orgs = service.list_for_user(request.user.id)
        serializer = OrganizationSerializer(orgs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = OrganizationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = OrganizationService()
        org = service.create(
            name=data["name"],
            domain=data.get("domain"),
            industry=data.get("industry"),
            plan=data.get("plan", "free"),
            is_active=data.get("is_active", True),
        )
        service.add_admin_membership(org, request.user)

        out = OrganizationSerializer(org)
        return Response(out.data, status=status.HTTP_201_CREATED)


class EvidenceListCreateView(APIView):
    """
    GET /api/evidence/?organization_id=<uuid>
    POST /api/evidence/
    """

    @staticmethod
    def _has_role(user, organization_id, allowed_roles):
        return OrganizationMembership.objects.filter(
            user=user,
            organization_id=organization_id,
            is_active=True,
            role__in=allowed_roles,
        ).exists()

    def get(self, request, *args, **kwargs):
        org_id = request.query_params.get("organization_id")
        if not org_id:
            return Response(
                {"detail": "organization_id query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            org_uuid = UUID(org_id)
        except ValueError:
            return Response(
                {"detail": "organization_id must be a valid UUID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not OrganizationMembership.objects.filter(
            user=request.user, organization_id=org_uuid, is_active=True
        ).exists():
            return Response({"detail": "Not a member of this organization."}, status=status.HTTP_403_FORBIDDEN)

        service = EvidenceService()
        items = service.list_by_org(organization_id=org_uuid)
        serializer = EvidenceSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = EvidenceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not self._has_role(request.user, data["organization_id"], {"admin", "member"}):
            return Response(
                {"detail": "Only members or admins can upload evidence."},
                status=status.HTTP_403_FORBIDDEN,
            )

        service = EvidenceService()

        # ✅ Option A: server generates storage_path and extracted_text
        evidence = service.create_from_payload(data)

        # Automatically run classification after successful creation
        classification = None
        try:
            coordinator = OrchestrationCoordinator()
            classification = coordinator.classify_evidence(evidence_id=str(evidence.id))
            # refresh to include ai_classification written by the agent
            evidence.refresh_from_db(fields=["ai_classification", "updated_at"])
        except Exception as exc:  # keep evidence creation successful even if classification fails
            classification = {"error": str(exc)}

        out = EvidenceSerializer(evidence)
        return Response(
            {"evidence": out.data, "classification": classification},
            status=status.HTTP_201_CREATED,
        )


class EvidenceClassifyView(APIView):
    """
    POST /api/evidence/<evidence_id>/classify/
    """

    def post(self, request, evidence_id: str, *args, **kwargs):
        # ensure UUID + existence
        evidence = get_object_or_404(Evidence, pk=evidence_id)

        if not EvidenceListCreateView._has_role(request.user, evidence.organization_id, {"admin", "member"}):
            return Response(
                {"detail": "Only members or admins can classify evidence."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if request.query_params.get("async") in {"1", "true", "yes"}:
            job = enqueue_classification(str(evidence.id))
            return Response(
                {"job_id": job.id, "status": "queued", "evidence_id": str(evidence.id)},
                status=status.HTTP_202_ACCEPTED,
            )

        coordinator = OrchestrationCoordinator()
        result = coordinator.classify_evidence(evidence_id=str(evidence.id))
        return Response(result, status=status.HTTP_200_OK)


class EvidenceFileUploadView(APIView):
    """
    POST /api/evidence/upload/
    """

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = EvidenceFileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not EvidenceListCreateView._has_role(request.user, data["organization_id"], {"admin", "member"}):
            return Response(
                {"detail": "Only members or admins can upload evidence."},
                status=status.HTTP_403_FORBIDDEN,
            )

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"detail": "No file attached."}, status=status.HTTP_400_BAD_REQUEST)

        service = EvidenceService()
        evidence = service.create_from_file(
            organization_id=data["organization_id"],
            uploaded_by=data.get("uploaded_by"),
            file=uploaded_file,
            title=data.get("title"),
            description=data.get("description"),
            evidence_type_id=data.get("evidence_type_id"),
            source_type_id=data.get("source_type_id"),
        )

        classification = None
        try:
            coordinator = OrchestrationCoordinator()
            classification = coordinator.classify_evidence(evidence_id=str(evidence.id))
            evidence.refresh_from_db(fields=["ai_classification", "updated_at"])
        except Exception as exc:
            classification = {"error": str(exc)}

        out = EvidenceSerializer(evidence)
        return Response(
            {"evidence": out.data, "classification": classification},
            status=status.HTTP_201_CREATED,
        )


class EvidenceAgentRunsView(APIView):
    """
    GET /api/evidence/<evidence_id>/agent-runs/
    Returns agent runs (with pipeline_run + step logs) for an evidence item.
    """

    def get(self, request, evidence_id: str, *args, **kwargs):
        evidence = get_object_or_404(Evidence, pk=evidence_id)

        if not OrganizationMembership.objects.filter(
            user=request.user, organization_id=evidence.organization_id, is_active=True
        ).exists():
            return Response({"detail": "Not a member of this organization."}, status=status.HTTP_403_FORBIDDEN)

        runs = (
            evidence.agent_runs.select_related("pipeline_run")
            .prefetch_related(Prefetch("step_logs", queryset=AgentStepLog.objects.order_by("started_at")))
            .order_by("-created_at")
        )
        serializer = AgentRunDetailSerializer(runs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AgentRunStepLogsView(APIView):
    """
    GET /api/agent-runs/<agent_run_id>/steps/
    """

    def get(self, request, agent_run_id: str, *args, **kwargs):
        agent_run = get_object_or_404(
            AgentRun.objects.select_related("evidence"),
            pk=agent_run_id,
        )
        evidence = agent_run.evidence
        if evidence:
            if not OrganizationMembership.objects.filter(
                user=request.user, organization_id=evidence.organization_id, is_active=True
            ).exists():
                return Response(
                    {"detail": "Not a member of this organization."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        logs = agent_run.step_logs.order_by("started_at")
        serializer = AgentStepLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EvidenceEventsView(APIView):
    """
    GET /api/evidence/<evidence_id>/events/
    """

    def get(self, request, evidence_id: str, *args, **kwargs):
        evidence = get_object_or_404(Evidence, pk=evidence_id)

        if not OrganizationMembership.objects.filter(
            user=request.user, organization_id=evidence.organization_id, is_active=True
        ).exists():
            return Response({"detail": "Not a member of this organization."}, status=status.HTTP_403_FORBIDDEN)

        events = evidence.events.order_by("-created_at")
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EvidenceTimelineView(APIView):
    """
    GET /api/evidence/<evidence_id>/timeline/
    Returns runs (with steps) and events in one payload.
    """

    def get(self, request, evidence_id: str, *args, **kwargs):
        evidence = get_object_or_404(Evidence, pk=evidence_id)

        if not OrganizationMembership.objects.filter(
            user=request.user, organization_id=evidence.organization_id, is_active=True
        ).exists():
            return Response({"detail": "Not a member of this organization."}, status=status.HTTP_403_FORBIDDEN)

        runs = (
            evidence.agent_runs.select_related("pipeline_run")
            .prefetch_related(Prefetch("step_logs", queryset=AgentStepLog.objects.order_by("started_at")))
            .order_by("-created_at")
        )
        events = evidence.events.order_by("-created_at")

        runs_data = AgentRunDetailSerializer(runs, many=True).data
        events_data = EventSerializer(events, many=True).data
        return Response({"runs": runs_data, "events": events_data}, status=status.HTTP_200_OK)


class TaskListView(APIView):
    """
    GET /api/tasks/?organization_id=<uuid>
    """

    def get(self, request, *args, **kwargs):
        org_id = request.query_params.get("organization_id")
        if not org_id:
            return Response({"detail": "organization_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not EvidenceListCreateView._has_role(request.user, org_id, {"admin", "member", "viewer"}):
            return Response({"detail": "Not a member of this organization."}, status=status.HTTP_403_FORBIDDEN)

        tasks = TaskService().list_by_org(org_id)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrganizationMembershipView(APIView):
    """
    GET /api/organizations/<org_id>/memberships/
    POST /api/organizations/<org_id>/memberships/  (invite existing user by email)
    """

    def get(self, request, org_id: str, *args, **kwargs):
        get_object_or_404(Organization, pk=org_id)
        if not EvidenceListCreateView._has_role(request.user, org_id, {"admin", "member", "viewer"}):
            return Response({"detail": "Not a member of this organization."}, status=status.HTTP_403_FORBIDDEN)

        memberships = OrganizationMembership.objects.filter(organization_id=org_id, is_active=True).select_related("user")
        serializer = OrganizationMembershipDetailSerializer(memberships, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, org_id: str, *args, **kwargs):
        if not EvidenceListCreateView._has_role(request.user, org_id, {"admin"}):
            return Response({"detail": "Only org admins can invite members."}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrganizationInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            user = UserModel.objects.get(email=data["email"])
        except UserModel.DoesNotExist:
            return Response({"detail": "User with this email does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        membership, created = OrganizationMembership.objects.get_or_create(
            organization_id=org_id,
            user=user,
            defaults={"role": data["role"], "is_active": True},
        )
        if not created:
            membership.role = data["role"]
            membership.is_active = True
            membership.save(update_fields=["role", "is_active", "updated_at"])

        out = OrganizationMembershipDetailSerializer(membership)
        return Response(out.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class OrganizationMembershipDeactivateView(APIView):
    """
    POST /api/organizations/<org_id>/memberships/<membership_id>/deactivate/
    """

    def post(self, request, org_id: str, membership_id: str, *args, **kwargs):
        if not EvidenceListCreateView._has_role(request.user, org_id, {"admin"}):
            return Response({"detail": "Only org admins can deactivate members."}, status=status.HTTP_403_FORBIDDEN)

        membership = get_object_or_404(
            OrganizationMembership.objects.filter(organization_id=org_id),
            pk=membership_id,
        )
        membership.is_active = False
        membership.save(update_fields=["is_active", "updated_at"])
        return Response({"detail": "Membership deactivated."}, status=status.HTTP_200_OK)


class JobStatusView(APIView):
    """
    GET /api/jobs/<job_id>/
    """

    permission_classes = [AllowAny]

    def get(self, request, job_id: str, *args, **kwargs):
        queue = get_queue("default")
        job = queue.fetch_job(job_id)
        if not job:
            return Response({"detail": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
        resp = {"job_id": job.id, "status": job.get_status()}
        if job.is_finished:
            resp["result"] = job.result
        if job.is_failed:
            resp["error"] = str(job.exc_info).splitlines()[-1] if job.exc_info else "Job failed"
        return Response(resp, status=status.HTTP_200_OK)


class PromptTemplateListCreateView(APIView):
    """
    GET/POST prompt templates
    """

    def get(self, request, *args, **kwargs):
        prompts = PromptTemplate.objects.order_by("-created_at")
        return Response(PromptTemplateSerializer(prompts, many=True).data)

    def post(self, request, *args, **kwargs):
        serializer = PromptTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prompt = serializer.save()
        return Response(PromptTemplateSerializer(prompt).data, status=status.HTTP_201_CREATED)


class ModelRegistryListCreateView(APIView):
    """
    GET/POST model registry entries
    """

    def get(self, request, *args, **kwargs):
        models_qs = ModelRegistry.objects.order_by("-created_at")
        return Response(ModelRegistrySerializer(models_qs, many=True).data)

    def post(self, request, *args, **kwargs):
        serializer = ModelRegistrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        model_entry = serializer.save()
        return Response(ModelRegistrySerializer(model_entry).data, status=status.HTTP_201_CREATED)
