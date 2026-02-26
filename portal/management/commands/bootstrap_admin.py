import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create a superuser from env vars (one-time bootstrap)."

    def handle(self, *args, **options):
        if os.environ.get("CREATE_SUPERUSER", "0") != "1":
            self.stdout.write("CREATE_SUPERUSER not enabled; skipping.")
            return

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin").strip()
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")

        if not password:
            self.stdout.write(self.style.ERROR("DJANGO_SUPERUSER_PASSWORD missing; cannot create superuser."))
            return

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write("Superuser already exists; skipping.")
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS("✅ Superuser created."))