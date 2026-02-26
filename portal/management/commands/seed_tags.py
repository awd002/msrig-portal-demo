from django.core.management.base import BaseCommand
from portal.models import Tag


DEFAULT_TAGS = [
    "Neurosurgery",
    "Spine",
    "Orthopedics",
    "Radiology",
    "Epidemiology",
    "Data Science",
    "AI/ML",
    "Clinical Research",
    "Basic Science",
]


class Command(BaseCommand):
    help = "Create default tags if none exist."

    def handle(self, *args, **options):
        created = 0
        for name in DEFAULT_TAGS:
            _, was_created = Tag.objects.get_or_create(name=name)
            created += int(was_created)

        self.stdout.write(self.style.SUCCESS(f"Tags ensured. Created {created}. Total: {Tag.objects.count()}"))