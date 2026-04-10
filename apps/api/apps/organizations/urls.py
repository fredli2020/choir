from django.urls import path

from apps.organizations.views import CurrentOrganizationMembershipView, OrganizationPermissionView

urlpatterns = [
    path(
        "orgs/<uuid:org_id>/membership",
        CurrentOrganizationMembershipView.as_view(),
        name="org-membership",
    ),
    path(
        "orgs/<uuid:org_id>/permissions",
        OrganizationPermissionView.as_view(),
        name="org-permissions",
    ),
]
