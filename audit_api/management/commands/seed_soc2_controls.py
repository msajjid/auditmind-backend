from django.core.management.base import BaseCommand
from audit_api.models import Framework, Control


SOC2_CONTROLS = [
    # ref, title, description, risk_level
    ("CC1.1", "Control environment is established",
     "Organization demonstrates commitment to integrity and ethical values.", "medium"),

    ("CC2.1", "Communication of information",
     "Information is communicated to support functioning of internal control.", "medium"),

    ("CC3.1", "Risk identification and assessment",
     "Risks to objectives are identified and assessed.", "medium"),

    ("CC4.1", "Monitoring activities",
     "Monitoring is performed to assess internal control effectiveness.", "medium"),

    ("CC5.1", "Control activities",
     "Control activities contribute to mitigation of risks.", "medium"),

    ("CC6.1", "Logical access security",
     "Controls logical access to systems, including IAM policies, permissions, roles, cloud access rules, and resource authorization.", "high"),

    ("CC7.1", "System operations",
     "System operations are managed to detect and respond to issues.", "high"),

    ("CC8.1", "Change management",
     "Changes are authorized, designed, developed, implemented, and tested.", "high"),

    ("CC9.1", "Risk mitigation",
     "Risk mitigation activities are identified and implemented.", "high"),
]


class Command(BaseCommand):
    help = "Seed SOC 2 framework + controls (create missing + update descriptions for existing)."

    def handle(self, *args, **options):
        fw, _ = Framework.objects.get_or_create(
            code="SOC2",
            defaults={
                "name": "SOC 2",
                "version": "2017",
                "description": "Seeded SOC 2 framework",
            },
        )

        created = 0
        updated = 0

        for ref, title, desc, risk_level in SOC2_CONTROLS:
            reference = f"SOC2-{ref}"

            obj, was_created = Control.objects.get_or_create(
                framework=fw,
                reference=reference,
                defaults={
                    "title": title,
                    "description": desc,
                    "risk_level": risk_level,
                },
            )

            if was_created:
                created += 1
                continue

            # Update existing rows if anything is missing/outdated
            changed = False

            if obj.title != title:
                obj.title = title
                changed = True

            if not (obj.description or "").strip() or obj.description.strip() != desc.strip():
                obj.description = desc
                changed = True

            if not obj.risk_level:
                obj.risk_level = risk_level
                changed = True

            if changed:
                obj.save(update_fields=["title", "description", "risk_level", "updated_at"])
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete. Created {created} controls. Updated {updated} controls."
            )
        )