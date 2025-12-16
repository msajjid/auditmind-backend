import uuid
from django.db import models


class Framework(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "frameworks"

    def __str__(self) -> str:
        return f"{self.code} {self.version}"