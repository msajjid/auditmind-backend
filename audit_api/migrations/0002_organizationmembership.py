import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('audit_api', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationMembership',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('admin', 'Admin'), ('member', 'Member')], default='member', max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(db_column='organization_id', on_delete=models.deletion.CASCADE, related_name='memberships', to='audit_api.organization')),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='org_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'organization_memberships',
                'unique_together': {('organization', 'user')},
            },
        ),
    ]
