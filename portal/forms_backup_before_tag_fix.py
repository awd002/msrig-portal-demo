from django import forms
from django.forms import formset_factory
from .models import Proposal, ProposalQuestion


class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = [
            "created_by_name",
            "created_by_email",
            "title",
            "summary",
            "background",
            "aims",
            "methods",
            "skills_needed",
            "time_commitment",
            "tags",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 4}),
            "background": forms.Textarea(attrs={"rows": 4}),
            "aims": forms.Textarea(attrs={"rows": 4}),
            "methods": forms.Textarea(attrs={"rows": 4}),
        }


class QuestionMiniForm(forms.Form):
    prompt = forms.CharField(max_length=400, required=False)
    is_required = forms.BooleanField(required=False, initial=True)


QuestionFormSet = formset_factory(QuestionMiniForm, extra=3, can_delete=True)


class SignupForm(forms.Form):
    volunteer_name = forms.CharField(max_length=120)
    volunteer_email = forms.EmailField()
    interest_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, questions=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.questions = list(questions or [])
        for q in self.questions:
            self.fields[f"q_{q.id}"] = forms.CharField(
                label=q.prompt,
                required=q.is_required,
                widget=forms.Textarea(attrs={"rows": 3}),
            )