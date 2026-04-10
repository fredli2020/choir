from django.urls import path

from apps.members.views import (
    DirectoryView,
    GroupAssignmentCreateView,
    GroupAssignmentDeleteView,
    GroupDetailView,
    GroupListCreateView,
    MemberDetailView,
    MemberListCreateView,
    MyProfileView,
)

urlpatterns = [
    path(
        "orgs/<uuid:org_id>/members",
        MemberListCreateView.as_view(),
        name="member-list",
    ),
    path(
        "orgs/<uuid:org_id>/members/<uuid:member_id>",
        MemberDetailView.as_view(),
        name="member-detail",
    ),
    path(
        "orgs/<uuid:org_id>/directory",
        DirectoryView.as_view(),
        name="member-directory",
    ),
    path(
        "orgs/<uuid:org_id>/my-profile",
        MyProfileView.as_view(),
        name="my-member-profile",
    ),
    path(
        "orgs/<uuid:org_id>/groups",
        GroupListCreateView.as_view(),
        name="group-list",
    ),
    path(
        "orgs/<uuid:org_id>/groups/<uuid:group_id>",
        GroupDetailView.as_view(),
        name="group-detail",
    ),
    path(
        "orgs/<uuid:org_id>/groups/<uuid:group_id>/members",
        GroupAssignmentCreateView.as_view(),
        name="group-member-assign",
    ),
    path(
        "orgs/<uuid:org_id>/groups/<uuid:group_id>/members/<uuid:member_id>",
        GroupAssignmentDeleteView.as_view(),
        name="group-member-remove",
    ),
]
