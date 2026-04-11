import pytest
from django.core.management import call_command

from apps.communications.models import Announcement, MessageCampaign
from apps.events.models import Event
from apps.members.models import Group, MemberProfile
from apps.organizations.models import Organization


@pytest.mark.django_db
def test_seed_sample_data_is_idempotent():
    call_command("seed_sample_data")
    call_command("seed_sample_data")

    organization = Organization.objects.get(slug="sample-choir")

    assert MemberProfile.objects.filter(organization=organization).count() == 6
    assert Group.objects.filter(organization=organization).count() == 4
    assert Event.objects.filter(organization=organization).count() == 4
    assert Announcement.objects.filter(organization=organization).count() == 2
    assert MessageCampaign.objects.filter(organization=organization).count() == 2
