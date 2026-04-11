from django.contrib import admin

from apps.communications.models import (
    Announcement,
    AnnouncementAudience,
    MessageCampaign,
    MessageRecipient,
)


class AnnouncementAudienceInline(admin.TabularInline):
    model = AnnouncementAudience
    extra = 0


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["title", "organization", "published", "published_at", "created_at"]
    list_filter = ["organization", "published"]
    search_fields = ["title", "body"]
    readonly_fields = ["id", "created_at", "updated_at", "published_at"]
    inlines = [AnnouncementAudienceInline]


class MessageRecipientInline(admin.TabularInline):
    model = MessageRecipient
    extra = 0
    readonly_fields = ["created_at", "updated_at"]


@admin.register(MessageCampaign)
class MessageCampaignAdmin(admin.ModelAdmin):
    list_display = ["subject", "organization", "status", "sent_at", "created_at"]
    list_filter = ["organization", "status"]
    search_fields = ["subject", "body", "audience_description"]
    readonly_fields = ["id", "created_at", "updated_at", "sent_at"]
    inlines = [MessageRecipientInline]
