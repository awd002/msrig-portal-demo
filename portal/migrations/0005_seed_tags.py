from django.db import migrations

TAG_NAMES = [
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


def seed_tags(apps, schema_editor):
    Tag = apps.get_model("portal", "Tag")
    for name in TAG_NAMES:
        Tag.objects.get_or_create(name=name)


def unseed_tags(apps, schema_editor):
    Tag = apps.get_model("portal", "Tag")
    Tag.objects.filter(name__in=TAG_NAMES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0004_tag_alter_proposalquestion_options_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_tags, reverse_code=unseed_tags),
    ]
