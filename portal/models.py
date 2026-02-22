from django.db import models
from django.utils.text import slugify
from django.utils import timezone
import secrets


class Proposal(models.Model):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("INPROG", "In Progress"),
        ("CLOSED", "Closed"),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    created_by_name = models.CharField(max_length=120)
    created_by_email = models.EmailField()

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)

    # Private link token for proposal owners (no admin needed)
    owner_token = models.CharField(max_length=64, unique=True, blank=True)

    summary = models.TextField()
    background = models.TextField(blank=True)
    aims = models.TextField(blank=True)
    methods = models.TextField(blank=True)
    skills_needed = models.CharField(max_length=240, blank=True)
    time_commitment = models.CharField(max_length=120, blank=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="OPEN",
    )

    tags = models.CharField(max_length=240, blank=True)

    def save(self, *args, **kwargs):
        # Generate secure owner token once
        if not self.owner_token:
            self.owner_token = secrets.token_hex(32)

        # Generate unique slug once
        if not self.slug:
            base = slugify(self.title)[:200]
            slug = base
            counter = 2

            while Proposal.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ProposalQuestion(models.Model):
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    prompt = models.CharField(max_length=400)
    is_required = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.proposal.title}: {self.prompt}"


class Signup(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name="signups",
    )

    volunteer_name = models.CharField(max_length=120)
    volunteer_email = models.EmailField()
    interest_reason = models.TextField(blank=True)

    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    decided_at = models.DateTimeField(null=True, blank=True)

    def set_status(self, new_status: str):
        """
        Helper method to update decision status cleanly.
        Automatically records decision timestamp.
        """
        if new_status not in dict(self.STATUS_CHOICES):
            raise ValueError("Invalid status")

        self.status = new_status
        self.decided_at = timezone.now()
        self.save(update_fields=["status", "decided_at"])

    def __str__(self):
        return f"{self.volunteer_name} -> {self.proposal.title} ({self.status})"


class SignupAnswer(models.Model):
    signup = models.ForeignKey(
        Signup,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        ProposalQuestion,
        on_delete=models.CASCADE,
    )
    answer = models.TextField(blank=True)

    class Meta:
        unique_together = ("signup", "question")

    def __str__(self):
        return f"Answer to {self.question.prompt}"
