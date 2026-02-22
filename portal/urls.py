from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("create/", views.proposal_create, name="proposal_create"),

    path("proposal/<slug:slug>/", views.proposal_detail, name="proposal_detail"),
    path("proposal/<slug:slug>/signup/", views.proposal_signup, name="proposal_signup"),

    # -----------------------------
    # Owner dashboard
    # -----------------------------
    path(
        "proposal/<slug:slug>/owner/<str:token>/",
        views.proposal_owner_dashboard,
        name="proposal_owner_dashboard",
    ),

    # Approve / Reject volunteer
    path(
        "proposal/<slug:slug>/owner/<str:token>/decide/<int:signup_id>/<str:decision>/",
        views.proposal_owner_decide_signup,
        name="proposal_owner_decide_signup",
    ),

    # Close / Reopen listing
    path(
        "proposal/<slug:slug>/owner/<str:token>/close/",
        views.proposal_owner_close,
        name="proposal_owner_close",
    ),
    path(
        "proposal/<slug:slug>/owner/<str:token>/reopen/",
        views.proposal_owner_reopen,
        name="proposal_owner_reopen",
    ),

    # -----------------------------
    # Delete proposal (with confirmation)
    # -----------------------------
    path(
        "proposal/<slug:slug>/owner/<str:token>/delete/",
        views.proposal_owner_delete_confirm,
        name="proposal_owner_delete_confirm",
    ),
    path(
        "proposal/<slug:slug>/owner/<str:token>/delete/confirm/",
        views.proposal_owner_delete,
        name="proposal_owner_delete",
    ),
]
