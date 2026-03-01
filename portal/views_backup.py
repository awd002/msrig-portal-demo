from __future__ import annotations

import traceback
from typing import Any

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .emailer import send_email
from .forms import ProposalForm, QuestionFormSet, SignupForm
from .models import Proposal, ProposalQuestion, Signup, SignupAnswer, Tag

VALID_STATUSES = {"OPEN", "INPROG", "CLOSED"}
VALID_DECISIONS = {"approve": "APPROVED", "reject": "REJECTED"}


# -------------------------------------------------------
# Utilities
# -------------------------------------------------------
def _safe_email(*, subject: str, text_body: str, to_email: str, html_body: str | None = None) -> None:
    """
    Never crash user flow due to email issues.
    Must match send_email(subject, to_email, text_body, html_body=None).
    """
    if not (to_email or "").strip():
        print("ℹ️ Email skipped: empty recipient.")
        return
    try:
        send_email(subject=subject, to_email=to_email, text_body=text_body, html_body=html_body)
        print(f"✅ Email attempted to={to_email} subject={subject!r}")
    except Exception as e:
        print(f"❌ Email FAILED to={to_email} subject={subject!r}")
        print(repr(e))
        print(traceback.format_exc())


def _get_owner_proposal_or_404(slug: str, token: str) -> Proposal:
    proposal = get_object_or_404(Proposal, slug=slug)
    if not getattr(proposal, "owner_token", None) or proposal.owner_token != token:
        raise Http404("Owner page not found.")
    return proposal


def _proposal_questions(proposal: Proposal) -> list[ProposalQuestion]:
    """
    Returns proposal questions regardless of related_name implementation.
    Preferred: related_name="questions".
    """
    if hasattr(proposal, "questions"):
        return list(proposal.questions.all().order_by("sort_order", "id"))
    if hasattr(proposal, "proposalquestion_set"):
        return list(proposal.proposalquestion_set.all().order_by("sort_order", "id"))
    return []


def _clean_str(v: Any) -> str:
    return ("" if v is None else str(v)).strip()


def _signup_field_value(cd: dict[str, Any], *keys: str) -> str:
    for k in keys:
        s = _clean_str(cd.get(k))
        if s:
            return s
    return ""


def _signup_display_name(signup: Signup) -> str:
    return _clean_str(getattr(signup, "volunteer_name", None)) or _clean_str(getattr(signup, "name", None)) or f"Signup #{signup.pk}"


def _signup_display_email(signup: Signup) -> str:
    return _clean_str(getattr(signup, "volunteer_email", None)) or _clean_str(getattr(signup, "email", None))


def _make_signup_instance(*, proposal: Proposal, name: str, email: str, message: str, role: str) -> Signup:
    """
    Create a Signup instance that supports either schema:
      - volunteer_name / volunteer_email / interest_reason
      - name / email / message / role
    """
    s = Signup()
    s.proposal = proposal

    if hasattr(s, "volunteer_name"):
        s.volunteer_name = name
    elif hasattr(s, "name"):
        s.name = name

    if hasattr(s, "volunteer_email"):
        s.volunteer_email = email
    elif hasattr(s, "email"):
        s.email = email

    if hasattr(s, "interest_reason"):
        s.interest_reason = message
    elif hasattr(s, "message"):
        s.message = message

    if hasattr(s, "role"):
        s.role = role

    return s


def _normalize_signup_for_template(s: Signup) -> dict[str, Any]:
    """
    Normalize Signup fields so templates can always rely on:
      name, email, message, role, status, created_at, id, answers, obj
    """
    name = _clean_str(getattr(s, "volunteer_name", None)) or _clean_str(getattr(s, "name", None))
    email = _clean_str(getattr(s, "volunteer_email", None)) or _clean_str(getattr(s, "email", None))
    message_txt = _clean_str(getattr(s, "interest_reason", None)) or _clean_str(getattr(s, "message", None))
    role = _clean_str(getattr(s, "role", None))
    status = _clean_str(getattr(s, "status", None))
    created_at = getattr(s, "created_at", None)
    answers = list(s.answers.all()) if hasattr(s, "answers") else []
    return {
        "obj": s,
        "id": s.id,
        "created_at": created_at,
        "name": name or f"Signup #{s.id}",
        "email": email,
        "message": message_txt,
        "role": role,
        "status": status,
        "answers": answers,
    }


def _set_signup_status(signup: Signup, status: str) -> None:
    """
    Update status using model method if present, else via status field.
    """
    if hasattr(signup, "set_status") and callable(getattr(signup, "set_status")):
        signup.set_status(status)
        return
    if hasattr(signup, "status"):
        signup.status = status
        signup.save(update_fields=["status"])
        return
    signup.save()


# -------------------------------------------------------
# Public Views
# -------------------------------------------------------
def home(request: HttpRequest) -> HttpResponse:
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()
    selected_tags = [t.strip() for t in request.GET.getlist("tags") if t and t.strip()]

    proposals = (
        Proposal.objects.all()
        .annotate(signups_count=Count("signups"))
        .prefetch_related("tags")
        .order_by("-created_at")
    )

    if q:
        proposals = proposals.filter(Q(title__icontains=q) | Q(summary__icontains=q))

    if status in VALID_STATUSES:
        proposals = proposals.filter(status=status)

    if selected_tags:
        proposals = proposals.filter(tags__slug__in=selected_tags).distinct()

    all_tags = Tag.objects.all().order_by("name")

    return render(
        request,
        "portal/home.html",
        {
            "proposals": proposals,
            "q": q,
            "status": status,
            "all_tags": all_tags,
            "selected_tags": set(selected_tags),
        },
    )


def proposal_detail(request: HttpRequest, slug: str) -> HttpResponse:
    proposal = get_object_or_404(
        Proposal.objects.prefetch_related("tags", "questions"),
        slug=slug,
    )
    return render(request, "portal/proposal_detail.html", {"proposal": proposal})


@require_http_methods(["GET", "POST"])
def proposal_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ProposalForm(request.POST)
        qset = QuestionFormSet(request.POST, prefix="q")

        if form.is_valid() and qset.is_valid():
            with transaction.atomic():
                proposal = form.save()

                sort_order = 0
                questions_to_create: list[ProposalQuestion] = []
                for f in qset:
                    if f.cleaned_data.get("DELETE"):
                        continue
                    prompt = _clean_str(f.cleaned_data.get("prompt"))
                    if not prompt:
                        continue
                    questions_to_create.append(
                        ProposalQuestion(
                            proposal=proposal,
                            prompt=prompt,
                            is_required=bool(f.cleaned_data.get("is_required")),
                            sort_order=sort_order,
                        )
                    )
                    sort_order += 1

                if questions_to_create:
                    ProposalQuestion.objects.bulk_create(questions_to_create)

            recipient = _clean_str(getattr(proposal, "created_by_email", None))
            if recipient:
                owner_dashboard_link = request.build_absolute_uri(
                    reverse("proposal_owner_dashboard", kwargs={"slug": proposal.slug, "token": proposal.owner_token})
                )
                _safe_email(
                    subject=f"MSRIG Proposal Created – Owner Dashboard Link – {proposal.title}",
                    text_body=(
                        "Your proposal has been created successfully!\n\n"
                        f"Title: {proposal.title}\n\n"
                        "Owner dashboard (bookmark this link):\n"
                        f"{owner_dashboard_link}\n\n"
                        "This link gives you access to:\n"
                        "- View signups\n"
                        "- Approve / Reject volunteers\n"
                        "- Close / Reopen listing\n"
                        "- Delete listing (with confirmation)\n\n"
                        "Best,\nMSRIG"
                    ),
                    to_email=recipient,
                )

            messages.success(request, "Proposal created! The owner dashboard link has been sent to the owner email.")
            return redirect("proposal_detail", slug=proposal.slug)
    else:
        form = ProposalForm()
        qset = QuestionFormSet(prefix="q")

    return render(request, "portal/proposal_create.html", {"form": form, "qset": qset})


@require_http_methods(["GET", "POST"])
def proposal_signup(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Public signup flow.
    - Base fields handled by SignupForm
    - Custom questions handled by POST keys q_<question_id>
    """
    proposal = get_object_or_404(Proposal.objects.prefetch_related("questions"), slug=slug)

    if proposal.status != "OPEN":
        messages.warning(request, "This proposal is not accepting signups right now.")
        return redirect("proposal_detail", slug=proposal.slug)

    questions = _proposal_questions(proposal)
    q_errors: dict[int, str] = {}

    if request.method == "POST":
        # If SignupForm supports dynamic questions kwarg, use it; else fall back.
        try:
            form = SignupForm(request.POST, questions=questions)  # type: ignore[arg-type]
        except TypeError:
            form = SignupForm(request.POST)

        # Validate required custom questions
        for q in questions:
            val = _clean_str(request.POST.get(f"q_{q.id}"))
            if q.is_required and not val:
                q_errors[q.id] = "This question is required."

        if form.is_valid() and not q_errors:
            cd = form.cleaned_data
            name = _signup_field_value(cd, "volunteer_name", "name")
            email = _signup_field_value(cd, "volunteer_email", "email")
            message_txt = _signup_field_value(cd, "interest_reason", "message")
            role = _signup_field_value(cd, "role")

            if not name:
                messages.error(request, "Please enter your name.")
            elif not email:
                messages.error(request, "Please enter your email.")
            else:
                with transaction.atomic():
                    signup = _make_signup_instance(
                        proposal=proposal, name=name, email=email, message=message_txt, role=role
                    )
                    signup.save()

                    answers_to_create: list[SignupAnswer] = []
                    for q in questions:
                        val = _clean_str(request.POST.get(f"q_{q.id}"))
                        answers_to_create.append(SignupAnswer(signup=signup, question=q, answer=val))
                    if answers_to_create:
                        SignupAnswer.objects.bulk_create(answers_to_create)

                recipient = _clean_str(getattr(proposal, "created_by_email", None))
                if recipient:
                    owner_dashboard_link = request.build_absolute_uri(
                        reverse("proposal_owner_dashboard", kwargs={"slug": proposal.slug, "token": proposal.owner_token})
                    )
                    _safe_email(
                        subject=f"New MSRIG Signup – {proposal.title}",
                        text_body=(
                            "A new volunteer signed up for your proposal:\n\n"
                            f"Volunteer: {_signup_display_name(signup)}\n"
                            f"Email: {_signup_display_email(signup)}\n\n"
                            "Owner dashboard:\n"
                            f"{owner_dashboard_link}\n"
                        ),
                        to_email=recipient,
                    )

                messages.success(request, "Signed up! The proposal owner has been notified.")
                return redirect("proposal_detail", slug=proposal.slug)

        if q_errors:
            messages.error(request, "Please answer the required custom questions.")
    else:
        try:
            form = SignupForm(questions=questions)  # type: ignore[arg-type]
        except TypeError:
            form = SignupForm()

    return render(
        request,
        "portal/proposal_signup.html",
        {"proposal": proposal, "form": form, "questions": questions, "q_errors": q_errors},
    )


# -------------------------------------------------------
# Owner Dashboard
# -------------------------------------------------------
def proposal_owner_dashboard(request: HttpRequest, slug: str, token: str) -> HttpResponse:
    proposal = _get_owner_proposal_or_404(slug, token)

    signups_qs = (
        Signup.objects.filter(proposal=proposal)
        .order_by("-created_at")
        .prefetch_related("answers__question")
    )

    signups = [_normalize_signup_for_template(s) for s in signups_qs]

    return render(
        request,
        "portal/proposal_owner_dashboard.html",
        {"proposal": proposal, "signups": signups, "token": token},
    )


# -------------------------------------------------------
# Approve / Reject Volunteer
# -------------------------------------------------------
@require_http_methods(["POST"])
def proposal_owner_decide_signup(
    request: HttpRequest, slug: str, token: str, signup_id: int, decision: str
) -> HttpResponse:
    proposal = _get_owner_proposal_or_404(slug, token)

    if decision not in VALID_DECISIONS:
        raise Http404("Invalid decision.")

    signup = get_object_or_404(Signup, id=signup_id, proposal=proposal)
    new_status = VALID_DECISIONS[decision]

    _set_signup_status(signup, new_status)

    display_name = _signup_display_name(signup)
    display_email = _signup_display_email(signup)

    if new_status == "APPROVED":
        subject = f"MSRIG Update: Approved – {proposal.title}"
        text_body = (
            f"Hi {display_name},\n\n"
            "You have been APPROVED for:\n"
            f"{proposal.title}\n\n"
            "The proposal owner will contact you soon.\n\n"
            "Best,\nMSRIG"
        )
    else:
        subject = f"MSRIG Update: Not Selected – {proposal.title}"
        text_body = (
            f"Hi {display_name},\n\n"
            "Thank you for signing up for:\n"
            f"{proposal.title}\n\n"
            "At this time, you were not selected.\n\n"
            "Please feel free to apply for other opportunities.\n\n"
            "Best,\nMSRIG"
        )

    _safe_email(subject=subject, text_body=text_body, to_email=display_email)

    messages.success(request, f"{display_name} marked as {new_status}.")
    return redirect("proposal_owner_dashboard", slug=proposal.slug, token=proposal.owner_token)


# -------------------------------------------------------
# Close / Reopen Listing
# -------------------------------------------------------
@require_http_methods(["POST"])
def proposal_owner_close(request: HttpRequest, slug: str, token: str) -> HttpResponse:
    proposal = _get_owner_proposal_or_404(slug, token)
    proposal.status = "CLOSED"
    proposal.save(update_fields=["status"])
    messages.success(request, "Listing closed. New signups disabled.")
    return redirect("proposal_owner_dashboard", slug=proposal.slug, token=proposal.owner_token)


@require_http_methods(["POST"])
def proposal_owner_reopen(request: HttpRequest, slug: str, token: str) -> HttpResponse:
    proposal = _get_owner_proposal_or_404(slug, token)
    proposal.status = "OPEN"
    proposal.save(update_fields=["status"])
    messages.success(request, "Listing reopened. Signups enabled.")
    return redirect("proposal_owner_dashboard", slug=proposal.slug, token=proposal.owner_token)


# -------------------------------------------------------
# Delete Proposal (Confirmation Page)
# -------------------------------------------------------
def proposal_owner_delete_confirm(request: HttpRequest, slug: str, token: str) -> HttpResponse:
    proposal = _get_owner_proposal_or_404(slug, token)
    return render(
        request,
        "portal/proposal_owner_delete_confirm.html",
        {"proposal": proposal, "token": token},
    )


# -------------------------------------------------------
# Permanent Delete
# -------------------------------------------------------
@require_http_methods(["POST"])
def proposal_owner_delete(request: HttpRequest, slug: str, token: str) -> HttpResponse:
    proposal = _get_owner_proposal_or_404(slug, token)
    proposal.delete()
    messages.success(request, "Proposal permanently deleted.")
    return redirect("home")
