from django import forms
from django.forms import inlineformset_factory

from .models import Proposal, ProposalQuestion, Signup, SignupAnswer, Tag


class ProposalForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select all specialties/domains that apply."
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
            "created_by_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Your name"}),
            "created_by_email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "your.email@domain.com"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Short, clear project title"}),
            "summary": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "1–2 paragraph overview"}),
            "background": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Optional background/context"}),
            "aims": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Optional aims / tasks"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class ProposalQuestionForm(forms.ModelForm):
    class Meta:
        model = ProposalQuestion
        fields = ["prompt", "is_required", "sort_order"]
        widgets = {
            "prompt": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., What year are you? Any stats/software experience?"}),
            "is_required": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }


# This is used when the proposal owner adds custom questions at creation time
QuestionFormSet = inlineformset_factory(
    Proposal,
    ProposalQuestion,
    form=ProposalQuestionForm,
    extra=3,
    can_delete=True
)


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
