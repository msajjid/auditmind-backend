# audit_api/serializers.py

from rest_framework import serializers

from django.contrib.auth import get_user_model

from audit_api.models import Evidence, Organization, OrganizationMembership, Task
from audit_api.models import AgentRun, AgentStepLog, Event, AiPipelineRun
from audit_api.models import PromptTemplate, ModelRegistry



class EvidenceCreateSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()
    uploaded_by = serializers.UUIDField(required=False, allow_null=True)

    # Title now optional; server will auto-generate if missing.
    title = serializers.CharField(max_length=255, required=False, allow_null=True, allow_blank=True)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    evidence_type_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    source_type_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    raw_text = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    raw_json = serializers.JSONField(required=False, allow_null=True)

    # optional — server can compute
    file_size = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        raw_text = attrs.get("raw_text")
        raw_json = attrs.get("raw_json")

        if not raw_text and raw_json is None:
            raise serializers.ValidationError("Provide either raw_text or raw_json.")
        return attrs


class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = [
            "id",
            "organization_id",
            "uploaded_by_id",
            "title",
            "description",
            "status",
            "storage_path",
            "evidence_type_id",
            "source_type_id",
            "file_size",
            "extracted_text",
            "ai_classification",
            "tags",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "ai_classification", "created_at", "updated_at"]


class EvidenceFileUploadSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()
    uploaded_by = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=False, allow_null=True, allow_blank=True)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    evidence_type_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    source_type_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    file = serializers.FileField()

class OrganizationCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    domain = serializers.CharField(
        max_length=255, required=False, allow_blank=True, allow_null=True
    )
    industry = serializers.CharField(
        max_length=255, required=False, allow_blank=True, allow_null=True
    )
    plan = serializers.CharField(
        max_length=50, required=False, default="free"
    )
    is_active = serializers.BooleanField(required=False, default=True)


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "domain",
            "industry",
            "plan",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer()

    class Meta:
        model = OrganizationMembership
        fields = ["organization", "role", "is_active", "created_at", "updated_at"]


class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "email", "first_name", "last_name"]


class OrganizationMembershipDetailSerializer(serializers.ModelSerializer):
    user = AuthUserSerializer()

    class Meta:
        model = OrganizationMembership
        fields = ["id", "user", "role", "is_active", "created_at", "updated_at"]


class OrganizationInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=OrganizationMembership.ROLE_CHOICES)


class AgentStepLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentStepLog
        fields = [
            "id",
            "step_name",
            "status",
            "started_at",
            "finished_at",
            "input_snapshot",
            "output_snapshot",
            "error",
            "metadata",
        ]


class AiPipelineRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiPipelineRun
        fields = [
            "id",
            "pipeline_type",
            "status",
            "started_at",
            "finished_at",
            "details",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class AgentRunSerializer(serializers.ModelSerializer):
    pipeline_run = AiPipelineRunSerializer(read_only=True)

    class Meta:
        model = AgentRun
        fields = [
            "id",
            "agent_name",
            "agent_version",
            "status",
            "started_at",
            "finished_at",
            "details",
            "pipeline_run",
            "evidence_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class AgentRunDetailSerializer(AgentRunSerializer):
    step_logs = AgentStepLogSerializer(many=True, read_only=True)

    class Meta(AgentRunSerializer.Meta):
        fields = AgentRunSerializer.Meta.fields + ["step_logs"]
        read_only_fields = fields


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id",
            "event_type",
            "evidence_id",
            "organization_id",
            "payload",
            "created_at",
        ]
        read_only_fields = fields


class PromptTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptTemplate
        fields = ["id", "name", "version", "content", "metadata", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ModelRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelRegistry
        fields = [
            "id",
            "name",
            "provider",
            "version",
            "model_type",
            "embedding_dims",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TaskSerializer(serializers.ModelSerializer):
    control_reference = serializers.CharField(source="control.reference", read_only=True)
    control_title = serializers.CharField(source="control.title", read_only=True)
    framework_code = serializers.CharField(source="framework.code", read_only=True)
    evidence_title = serializers.CharField(source="evidence.title", read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "organization_id",
            "framework_id",
            "framework_code",
            "control_id",
            "control_reference",
            "control_title",
            "evidence_id",
            "evidence_title",
            "title",
            "description",
            "status",
            "assignee_id",
            "due_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
