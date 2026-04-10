from django.urls import path

from apps.accounts.views import (
    CurrentUserContextView,
    CurrentUserOrganizationsView,
    CurrentUserView,
)

urlpatterns = [
    path("me", CurrentUserView.as_view(), name="current-user"),
    path("me/context", CurrentUserContextView.as_view(), name="current-user-context"),
    path(
        "me/organizations",
        CurrentUserOrganizationsView.as_view(),
        name="current-user-organizations",
    ),
]
