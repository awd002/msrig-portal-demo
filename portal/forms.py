from django import forms
from django.forms import formset_factory

from .models import Proposal, ProposalQuestion, Signup, SignupAnswer, Tag


# -------------------------------------------------------
# Proposal creation form
# -------------------------------------------------------
class ProposalForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select all specialties/domains that apply.",
    )

    class Meta:
        model = Proposal
        fields = [
            "created_by_name",
            "created_by_email",
            "title",
            "summary",
            "background",
            "aims",
            "status",
            "tags",
        ]
        widgets = {
            "created_by_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Your name"}
            ),
            "created_by_email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "your.email@domain.com"}
            ),
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Short, clear project title"}
            ),
            "summary": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "1–2 paragraph overview"}
            ),
            "background": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Optional background/context"}
            ),
            "aims": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Optional aims / tasks"}
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


# -------------------------------------------------------
# Proposal creation: dynamic "Application Questions" formset
# (Use a plain FormSet, since the Proposal doesn't exist yet.)
# -------------------------------------------------------
class ProposalQuestionCreateForm(forms.Form):
    prompt = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g., What year are you? Any stats/software experience?",
            }
        ),
    )
    is_required = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


# Start with 0 rows; user adds via the ➕ button on the create page.
# If you want one row visible by default, change extra=1.
QuestionFormSet = formset_factory(
    ProposalQuestionCreateForm,
    extra=0,
    can_delete=True,
)


# -------------------------------------------------------
# Signup forms
# -------------------------------------------------------
class SignupForm(forms.ModelForm):
    class Meta:
        model = Signup
        fields = ["name", "email"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Your name"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "your.email@domain.com"}),
        }


class SignupAnswerForm(forms.ModelForm):
    class Meta:
        model = SignupAnswer
        fields = ["answer_text"]
        widgets = {
            "answer_text": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
