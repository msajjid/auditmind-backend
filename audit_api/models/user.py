import uuid
from django.db import models


class User(models.Model):
    """
    Domain user (NOT django.contrib.auth.User).
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    organization = models.ForeignKey(
        "Organization",
        on_delete=models.CASCADE,
        related_name="users",
        db_column="organization_id",
    )
    email = models.CharField(max_length=255, unique=True)
    full_name = models.CharField(max_length=255)
    password_hash = models.TextField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    auth_provider = models.CharField(max_length=50, default="local")
    role = models.CharField(max_length=50, default="user")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"

    def __str__(self) -> str:
        return self.email