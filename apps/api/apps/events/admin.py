from django.contrib import admin

from apps.events.models import RSVP, AttendanceRecord, Event, EventAudience


class EventAudienceInline(admin.TabularInline):
    model = EventAudience
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "organization", "type", "start_at", "end_at", "is_all_day"]
    list_filter = ["organization", "type", "is_all_day"]
    search_fields = ["title", "description", "location"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [EventAudienceInline]


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ["event", "member_profile", "status", "responded_at", "updated_at"]
    list_filter = ["status", "event__organization"]
    search_fields = ["event__title", "member_profile__first_name", "member_profile__last_name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = [
        "event",
        "member_profile",
        "status",
        "recorded_by_user",
        "recorded_at",
        "updated_at",
    ]
    list_filter = ["status", "event__organization"]
    search_fields = ["event__title", "member_profile__first_name", "member_profile__last_name"]
    readonly_fields = ["id", "created_at", "updated_at"]
