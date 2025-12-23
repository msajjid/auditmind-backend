from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit_api", "0004_agent_runs_events"),
    ]

    operations = [
        migrations.AlterField(
            model_name="organizationmembership",
            name="role",
            field=models.CharField(
                choices=[("admin", "Admin"), ("member", "Member"), ("viewer", "Viewer")],
                default="member",
                max_length=50,
            ),
        ),
    ]
