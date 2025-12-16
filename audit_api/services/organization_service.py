# audit_api/services/organization_service.py

from typing import Iterable, Optional
from uuid import UUID

from audit_api.models import Organization, OrganizationMembership
from django.contrib.auth import get_user_model


class OrganizationService:
    def list(self) -> Iterable[Organization]:
        return Organization.objects.order_by("name")

    def list_for_user(self, user_id: int) -> Iterable[Organization]:
        membership_ids = (
            OrganizationMembership.objects.filter(user_id=user_id, is_active=True)
            .values_list("organization_id", flat=True)
        )
        return Organization.objects.filter(id__in=membership_ids).order_by("name")

    def get(self, organization_id: UUID) -> Organization:
        return Organization.objects.get(pk=organization_id)

    def create(
        self,
        *,
        name: str,
        domain: Optional[str] = None,
        industry: Optional[str] = None,
        plan: str = "free",
        is_active: bool = True,
    ) -> Organization:
        return Organization.objects.create(
            name=name,
            domain=domain,
            industry=industry,
            plan=plan,
            is_active=is_active,
        )

    def add_admin_membership(self, organization: Organization, user: get_user_model()) -> OrganizationMembership:
        membership, _created = OrganizationMembership.objects.get_or_create(
            organization=organization,
            user=user,
            defaults={"role": "admin"},
        )
        if membership.role != "admin":
            membership.role = "admin"
            membership.save(update_fields=["role", "updated_at"])
        return membership
