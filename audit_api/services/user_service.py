# audit_api/services/user_service.py

from typing import Iterable, Optional
from uuid import UUID

from django.db import transaction
from django.contrib.auth.hashers import make_password

from audit_api.models import User, Organization


class UserService:
    def list_by_org(self, organization_id: UUID) -> Iterable[User]:
        return (
            User.objects
            .filter(organization_id=organization_id)
            .order_by("-created_at")
        )

    def get(self, user_id: UUID) -> User:
        return User.objects.get(pk=user_id)

    @transaction.atomic
    def create(
        self,
        *,
        organization_id: UUID,
        email: str,
        full_name: str,
        password: Optional[str] = None,
    ) -> User:
        # Use Django's built-in password hasher to store a salted hash
        password_hash = make_password(password) if password else None

        return User.objects.create(
            organization_id=organization_id,
            email=email,
            full_name=full_name,
            password_hash=password_hash,
        )
