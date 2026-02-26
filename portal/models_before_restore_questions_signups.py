from django.db import models
from django.utils.text import slugify
import secrets


class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Proposal(models.Model):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("INPROG", "In Progress"),
        ("CLOSED", "Closed"),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    created_by_name = models.CharField(max_length=120)
    created_by_email = models.EmailField()
    title = models.CharField(max_length=180)

    slug = models.SlugField(max_length=220, unique=True, blank=True)

    summary = models.TextField()
    background = models.TextField(blank=True)
    aims = models.TextField(blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="OPEN")

    # Used for owner dashboard link security
    owner_token = models.CharField(max_length=64, unique=True, blank=True, editable=False)

    # Pre-defined specialties/tags (many-to-many)
    tags = models.ManyToManyField(Tag, blank=True, related_name="proposals")

    def save(self, *args, **kwargs):
        # Owner token
        if not self.owner_token:
            self.owner_token = secrets.token_hex(32)

        # Slug
        if not self.slug:
            base = slugify(self.title)[:200] or "proposal"
            candidate = base
            i = 2
            while Proposal.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{i}"
                i += 1
            self.slug = candidate

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
