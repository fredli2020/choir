import django_filters
from django.db.models import Q

from apps.members.models import Group, MemberProfile


class MemberProfileFilterSet(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")
    voice_part = django_filters.ChoiceFilter(choices=MemberProfile.VoicePart.choices)
    status = django_filters.ChoiceFilter(choices=MemberProfile.Status.choices)

    class Meta:
        model = MemberProfile
        fields = ["search", "email", "voice_part", "status"]

    def filter_search(self, queryset, name, value):
        del name
        normalized = value.strip()
        if not normalized:
            return queryset

        return queryset.filter(
            Q(first_name__icontains=normalized)
            | Q(last_name__icontains=normalized)
            | Q(email__icontains=normalized)
            | Q(first_name__icontains=normalized.split(" ")[0])
            | Q(last_name__icontains=normalized)
        )


class GroupFilterSet(django_filters.FilterSet):
    type = django_filters.ChoiceFilter(choices=Group.Type.choices)
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Group
        fields = ["type", "name"]
