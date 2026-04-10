from django.contrib import admin

from apps.members.models import Group, GroupMember, MemberProfile


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = [
        "first_name",
        "last_name",
        "organization",
        "email",
        "voice_part",
        "status",
        "user",
    ]
    list_filter = ["organization", "voice_part", "status"]
    search_fields = ["first_name", "last_name", "email"]
    readonly_fields = ["id", "created_at", "updated_at"]


class GroupMemberInline(admin.TabularInline):
    model = GroupMember
    extra = 0


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "organization", "created_at", "updated_at"]
    list_filter = ["organization", "type"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [GroupMemberInline]


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ["group", "member_profile", "role", "created_at"]
    list_filter = ["group__organization", "group__type"]
    search_fields = [
        "group__name",
        "member_profile__first_name",
        "member_profile__last_name",
        "member_profile__email",
    ]
    readonly_fields = ["id", "created_at"]
