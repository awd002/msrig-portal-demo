import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create/update a superuser from env vars (for Render free plan without shell)."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "").strip()

        if not username or not password:
            self.stdout.write(self.style.WARNING(
                "Skipping ensure_superuser: DJANGO_SUPERUSER_USERNAME/PASSWORD not set."
            ))
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username, defaults={"email": email})

        if email and user.email != email:
            user.email = email

        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        msg = "Created superuser." if created else "Updated superuser."
        self.stdout.write(self.style.SUCCESS(f"{msg} username={username!r}"))