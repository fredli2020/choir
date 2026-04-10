from django.contrib import admin

from apps.organizations.models import Organization, OrganizationMembership


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at", "updated_at"]
    search_fields = ["name", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ["organization", "user", "role", "status", "created_at", "updated_at"]
    list_filter = ["role", "status", "organization"]
    search_fields = ["organization__name", "organization__slug", "user__email", "user__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
