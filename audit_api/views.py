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

from audit_api.serializers import (
    EvidenceCreateSerializer,
    EvidenceSerializer,
    OrganizationCreateSerializer,
    OrganizationSerializer,
    OrganizationMembershipSerializer,
    AuthUserSerializer,
)
from audit_api.services import EvidenceService, OrganizationService
from audit_api.orchestration.coordinator import OrchestrationCoordinator
from audit_api.models import Evidence, OrganizationMembership

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

        if not OrganizationMembership.objects.filter(
            user=request.user, organization_id=data["organization_id"], is_active=True
        ).exists():
            return Response({"detail": "Not a member of this organization."}, status=status.HTTP_403_FORBIDDEN)

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

        if not OrganizationMembership.objects.filter(
            user=request.user, organization_id=evidence.organization_id, is_active=True
        ).exists():
            return Response({"detail": "Not a member of this organization."}, status=status.HTTP_403_FORBIDDEN)

        coordinator = OrchestrationCoordinator()
        # either pass evidence_id or evidence — keep whatever your coordinator expects
        result = coordinator.classify_evidence(evidence_id=str(evidence.id))

        return Response(result, status=status.HTTP_200_OK)
