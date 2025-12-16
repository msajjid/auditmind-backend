# audit_api/serializers.py

from rest_framework import serializers

from django.contrib.auth import get_user_model

from audit_api.models import Evidence, Organization, OrganizationMembership



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
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "ai_classification", "created_at", "updated_at"]

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
