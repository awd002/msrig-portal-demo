from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import ProposalForm, SignupForm, QuestionFormSet
from .models import Proposal, ProposalQuestion, Signup, SignupAnswer, Tag


VALID_STATUSES = {"OPEN", "INPROG", "CLOSED"}
VALID_DECISIONS = {"approve": "APPROVED", "reject": "REJECTED"}


# -------------------------------------------------------
# Utility: Validate owner token
# -------------------------------------------------------
def _get_owner_proposal_or_404(slug, token):
    proposal = get_object_or_404(Proposal, slug=slug)
    if not proposal.owner_token or proposal.owner_token != token:
        raise Http404("Owner page not found.")
    return proposal


# -------------------------------------------------------
# Public Views
# -------------------------------------------------------
def home(request):
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()

    # Accept multiple tags via ?tags=slug&tags=slug2
    selected_tags = request.GET.getlist("tags")
    selected_tags = [t.strip() for t in selected_tags if t and t.strip()]

    proposals = (
        Proposal.objects.all()
        # IMPORTANT: don't use 'num_signups' (often a @property); use a safe annotation name
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
def proposal_detail(request, slug):
    proposal = get_object_or_404(
        Proposal.objects.prefetch_related("questions"),
        slug=slug,
    )
    return render(request, "portal/proposal_detail.html", {"proposal": proposal})


@require_http_methods(["GET", "POST"])
def proposal_create(request):
    if request.method == "POST":
        form = ProposalForm(request.POST)
        qset = QuestionFormSet(request.POST, prefix="q")

        if form.is_valid() and qset.is_valid():
            with transaction.atomic():
                proposal = form.save()

                sort_order = 0
                questions_to_create = []

                for f in qset:
                    if f.cleaned_data.get("DELETE"):
                        continue

                    prompt = (f.cleaned_data.get("prompt") or "").strip()
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

            # Email owner dashboard link immediately after creation
            recipient = getattr(proposal, "created_by_email", None)
            if recipient:
                owner_dashboard_link = request.build_absolute_uri(
                    reverse(
                        "proposal_owner_dashboard",
                        kwargs={"slug": proposal.slug, "token": proposal.owner_token},
                    )
                )

                send_mail(
                    subject=f"MSRIG Proposal Created – Owner Dashboard Link – {proposal.title}",
                    message=(
                        f"Your proposal has been created successfully!\n\n"
                        f"Title: {proposal.title}\n\n"
                        f"Owner dashboard (bookmark this link):\n"
                        f"{owner_dashboard_link}\n\n"
                        f"This link gives you access to:\n"
                        f"- View signups\n"
                        f"- Approve / Reject volunteers\n"
                        f"- Close / Reopen listing\n"
                        f"- Delete listing (with confirmation)\n\n"
                        f"Best,\nMSRIG"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    fail_silently=True,
                )

            messages.success(
                request,
                "Proposal created! The owner dashboard link has been sent to your email (printed in the server console during development)."
            )
            return redirect("proposal_detail", slug=proposal.slug)

    else:
        form = ProposalForm()
        qset = QuestionFormSet(prefix="q")

    return render(request, "portal/proposal_create.html", {"form": form, "qset": qset})


@require_http_methods(["GET", "POST"])
def proposal_signup(request, slug):
    proposal = get_object_or_404(
        Proposal.objects.prefetch_related("questions"),
        slug=slug,
    )
    questions = list(proposal.questions.all())

    if proposal.status != "OPEN":
        messages.warning(request, "This proposal is not accepting signups right now.")
        return redirect("proposal_detail", slug=proposal.slug)

    if request.method == "POST":
        form = SignupForm(request.POST, questions=questions)

        if form.is_valid():
            with transaction.atomic():
                signup = Signup.objects.create(
                    proposal=proposal,
                    volunteer_name=form.cleaned_data["volunteer_name"],
                    volunteer_email=form.cleaned_data["volunteer_email"],
                    interest_reason=form.cleaned_data.get("interest_reason", "") or "",
                )

                answers = [
                    SignupAnswer(
                        signup=signup,
                        question=q,
                        answer=form.cleaned_data.get(f"q_{q.id}", "") or "",
                    )
                    for q in questions
                ]

                if answers:
                    SignupAnswer.objects.bulk_create(answers)

            # Notify proposal owner
            recipient = getattr(proposal, "created_by_email", None)
            if recipient:
                owner_dashboard_link = request.build_absolute_uri(
                    reverse(
                        "proposal_owner_dashboard",
                        kwargs={"slug": proposal.slug, "token": proposal.owner_token},
                    )
                )

                send_mail(
                    subject=f"New MSRIG Signup – {proposal.title}",
                    message=(
                        f"A new volunteer signed up for your proposal:\n\n"
                        f"Volunteer: {signup.volunteer_name}\n"
                        f"Email: {signup.volunteer_email}\n\n"
                        f"Owner dashboard:\n{owner_dashboard_link}"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    fail_silently=True,
                )

            messages.success(request, "Signed up! The proposal owner has been notified.")
            return redirect("proposal_detail", slug=proposal.slug)

    else:
        form = SignupForm(questions=questions)

    return render(request, "portal/proposal_signup.html", {"proposal": proposal, "form": form})


# -------------------------------------------------------
# Owner Dashboard
# -------------------------------------------------------
def proposal_owner_dashboard(request, slug, token):
    proposal = _get_owner_proposal_or_404(slug, token)

    signups = (
        Signup.objects.filter(proposal=proposal)
        .order_by("-created_at")
        .prefetch_related("answers__question")
    )

    return render(
        request,
        "portal/proposal_owner_dashboard.html",
        {"proposal": proposal, "signups": signups, "token": token},
    )


# -------------------------------------------------------
# Approve / Reject Volunteer
# -------------------------------------------------------
@require_http_methods(["POST"])
def proposal_owner_decide_signup(request, slug, token, signup_id, decision):
    proposal = _get_owner_proposal_or_404(slug, token)

    if decision not in VALID_DECISIONS:
        raise Http404("Invalid decision.")

    signup = get_object_or_404(Signup, id=signup_id, proposal=proposal)
    new_status = VALID_DECISIONS[decision]

    signup.set_status(new_status)

    if new_status == "APPROVED":
        subject = f"MSRIG Update: Approved – {proposal.title}"
        body = (
            f"Hi {signup.volunteer_name},\n\n"
            f"You have been APPROVED for:\n{proposal.title}\n\n"
            f"The proposal owner will contact you soon.\n\n"
            f"Best,\nMSRIG"
        )
    else:
        subject = f"MSRIG Update: Not Selected – {proposal.title}"
        body = (
            f"Hi {signup.volunteer_name},\n\n"
            f"Thank you for signing up for:\n{proposal.title}\n\n"
            f"At this time, you were not selected.\n\n"
            f"Please feel free to apply for other opportunities.\n\n"
            f"Best,\nMSRIG"
        )

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[signup.volunteer_email],
        fail_silently=True,
    )

    messages.success(request, f"{signup.volunteer_name} marked as {new_status}.")
    return redirect("proposal_owner_dashboard", slug=proposal.slug, token=proposal.owner_token)


# -------------------------------------------------------
# Close / Reopen Listing
# -------------------------------------------------------
@require_http_methods(["POST"])
def proposal_owner_close(request, slug, token):
    proposal = _get_owner_proposal_or_404(slug, token)
    proposal.status = "CLOSED"
    proposal.save(update_fields=["status"])
    messages.success(request, "Listing closed. New signups disabled.")
    return redirect("proposal_owner_dashboard", slug=proposal.slug, token=proposal.owner_token)


@require_http_methods(["POST"])
def proposal_owner_reopen(request, slug, token):
    proposal = _get_owner_proposal_or_404(slug, token)
    proposal.status = "OPEN"
    proposal.save(update_fields=["status"])
    messages.success(request, "Listing reopened. Signups enabled.")
    return redirect("proposal_owner_dashboard", slug=proposal.slug, token=proposal.owner_token)


# -------------------------------------------------------
# Delete Proposal (Confirmation Page)
# -------------------------------------------------------
def proposal_owner_delete_confirm(request, slug, token):
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
def proposal_owner_delete(request, slug, token):
    proposal = _get_owner_proposal_or_404(slug, token)
    proposal.delete()
    messages.success(request, "Proposal permanently deleted.")
    return redirect("home")
