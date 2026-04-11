from django_filters import rest_framework as filters

from apps.communications.models import MessageCampaign


class MessageCampaignFilterSet(filters.FilterSet):
    status = filters.ChoiceFilter(choices=MessageCampaign.Status.choices)

    class Meta:
        model = MessageCampaign
        fields = ["status"]
