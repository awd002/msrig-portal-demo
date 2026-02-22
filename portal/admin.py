from django.contrib import admin
from .models import Proposal, ProposalQuestion, Signup, SignupAnswer


class ProposalQuestionInline(admin.TabularInline):
    model = ProposalQuestion
    extra = 1


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "created_by_name", "created_at")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProposalQuestionInline]


class SignupAnswerInline(admin.TabularInline):
    model = SignupAnswer
    extra = 0
    readonly_fields = ("question", "answer")


@admin.register(Signup)
class SignupAdmin(admin.ModelAdmin):
    list_display = ("proposal", "volunteer_name", "volunteer_email", "created_at")
    inlines = [SignupAnswerInline]


# Optional: make these visible/searchable too
@admin.register(ProposalQuestion)
class ProposalQuestionAdmin(admin.ModelAdmin):
    list_display = ("proposal", "prompt", "is_required", "sort_order")


@admin.register(SignupAnswer)
class SignupAnswerAdmin(admin.ModelAdmin):
    list_display = ("signup", "question")
