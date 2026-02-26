from django.contrib import admin
from .models import Proposal, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by_name", "status", "created_at")
    list_filter = ("status", "created_at", "tags")
    search_fields = ("title", "summary", "created_by_name", "created_by_email")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
