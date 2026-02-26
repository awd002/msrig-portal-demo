from django.db import migrations
from django.utils.text import slugify

TAGS = [
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
    for name in TAGS:
        slug = slugify(name)[:250]
        Tag.objects.get_or_create(slug=slug, defaults={"name": name})

class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0004_tag_alter_proposalquestion_options_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_tags, migrations.RunPython.noop),
    ]
