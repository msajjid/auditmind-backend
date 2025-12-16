# audit_api/services/framework_service.py

from typing import Iterable
from uuid import UUID

from audit_api.models import Framework


class FrameworkService:
    def list(self) -> Iterable[Framework]:
        return Framework.objects.order_by("name")

    def get(self, framework_id: UUID) -> Framework:
        return Framework.objects.get(pk=framework_id)

    def create(
        self,
        *,
        code: str,
        name: str,
        version: str,
        description: str | None,
    ) -> Framework:
        return Framework.objects.create(
            code=code,
            name=name,
            version=version,
            description=description,
        )