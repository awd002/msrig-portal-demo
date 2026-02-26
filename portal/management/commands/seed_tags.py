from django.core.management.base import BaseCommand
from django.utils.text import slugify
from portal.models import Tag


DEFAULT_TAGS = [
    "AI/ML",
    "Anesthesiology",
    "Biomechanics",
    "Cardiology",
    "Case Report/Case Series",
    "Clinical Trials",
    "Dermatology",
    "ENT",
    "Education",
    "Emergency Medicine",
    "Endocrinology",
    "Epidemiology/Public Health",
    "Family Medicine",
    "Gastroenterology",
    "General Surgery",
    "Imaging",
    "Infectious Disease",
    "Internal Medicine",
    "Neurology",
    "Neurosurgery",
    "OB/GYN",
    "Oncology",
    "Ophthalmology",
    "Orthopedics",
    "Outcomes Research",
    "PM&R",
    "Pathology",
    "Pediatrics",
    "Plastic Surgery",
    "Psychiatry",
    "Pulmonology/Critical Care",
    "Quality Improvement",
    "Radiology",
    "Rheumatology",
    "Systematic Review/Meta-analysis",
    "Urology",
    "Vascular Surgery",
]


class Command(BaseCommand):
    help = "Seed default tags safely (idempotent)."

    def handle(self, *args, **options):
        created = 0

        for name in DEFAULT_TAGS:
            slug = slugify(name)[:250]

            _, was_created = Tag.objects.get_or_create(
                slug=slug,
                defaults={"name": name},
            )

            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Tags ensured. Created {created}. Total: {Tag.objects.count()}"
            )
        )
