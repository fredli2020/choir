import django_filters
from django.db.models import Q
from django.utils import timezone

from apps.events.models import Event


class EventFilterSet(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    type = django_filters.ChoiceFilter(choices=Event.Type.choices)
    window_start = django_filters.IsoDateTimeFilter(method="filter_window_start")
    window_end = django_filters.IsoDateTimeFilter(method="filter_window_end")
    upcoming = django_filters.BooleanFilter(method="filter_upcoming")

    class Meta:
        model = Event
        fields = ["search", "type", "window_start", "window_end", "upcoming"]

    def filter_search(self, queryset, name, value):
        del name
        normalized = value.strip()
        if not normalized:
            return queryset
        return queryset.filter(
            Q(title__icontains=normalized)
            | Q(description__icontains=normalized)
            | Q(location__icontains=normalized)
        )

    def filter_window_start(self, queryset, name, value):
        del name
        return queryset.filter(end_at__gte=value)

    def filter_window_end(self, queryset, name, value):
        del name
        return queryset.filter(start_at__lte=value)

    def filter_upcoming(self, queryset, name, value):
        del name
        if value:
            return queryset.filter(end_at__gte=timezone.now())
        return queryset
