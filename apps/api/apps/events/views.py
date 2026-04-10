from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.events.models import Event
from apps.events.serializers import (
    AttendanceBulkUpdateSerializer,
    AttendanceRosterSerializer,
    CurrentMemberRSVPSerializer,
    EventAudienceSummarySerializer,
    EventAudienceWriteSerializer,
    EventReadSerializer,
    EventRSVPListSerializer,
    EventWriteSerializer,
    MyEventResponseSerializer,
    RSVPUpsertSerializer,
)
from apps.events.services import (
    bulk_upsert_attendance,
    create_event,
    delete_event,
    get_event,
    get_event_attendance_summary,
    get_event_audience_summary,
    get_event_for_user,
    get_event_rsvp_summary,
    get_linked_active_member_profile,
    get_member_event_rsvp,
    list_attendance_roster,
    list_event_rsvps,
    list_events,
    list_my_rsvp_responses,
    list_relevant_events,
    list_upcoming_relevant_events,
    replace_event_audience,
    update_event,
    upsert_member_rsvp,
)
from apps.organizations.services import require_active_membership
from apps.permissions.services import (
    can_view_events,
    require_can_manage_events,
    require_can_record_attendance,
    require_can_rsvp_to_events,
    require_can_view_events,
    require_can_view_relevant_events,
)


class OrganizationScopedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_organization(self, request, org_id):
        membership = require_active_membership(request.user, org_id)
        return membership.organization

    def handle_domain_error(self, exc):
        if isinstance(exc, DjangoPermissionDenied):
            raise PermissionDenied(str(exc)) from exc
        if isinstance(exc, DjangoValidationError):
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise ValidationError(detail) from exc
        raise exc


class EventListCreateView(OrganizationScopedAPIView):
    def get(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_view_events(request.user, organization)
        try:
            events = list_events(organization, request.query_params)
        except Exception as exc:
            self.handle_domain_error(exc)
        serializer = EventReadSerializer(events, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_events(request.user, organization)
        serializer = EventWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            event = create_event(organization, request.user, serializer.validated_data)
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(EventReadSerializer(event, context={"request": request}).data, status=201)


class EventDetailView(OrganizationScopedAPIView):
    def _get_event_for_request(self, request, organization, event_id):
        try:
            if can_view_events(request.user, organization):
                return get_event(organization, event_id)
            require_can_view_relevant_events(request.user, organization)
            return get_event_for_user(organization, event_id, request.user)
        except Event.DoesNotExist as exc:
            raise NotFound("Event not found.") from exc
        except Exception as exc:
            self.handle_domain_error(exc)

    def get(self, request, org_id, event_id):
        organization = self.get_organization(request, org_id)
        event = self._get_event_for_request(request, organization, event_id)
        return Response(EventReadSerializer(event, context={"request": request}).data)

    def patch(self, request, org_id, event_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_events(request.user, organization)
        serializer = EventWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            event = get_event(organization, event_id)
            event = update_event(event, serializer.validated_data)
        except Event.DoesNotExist as exc:
            raise NotFound("Event not found.") from exc
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(EventReadSerializer(event, context={"request": request}).data)

    def delete(self, request, org_id, event_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_events(request.user, organization)
        try:
            event = get_event(organization, event_id)
            delete_event(event)
        except Event.DoesNotExist as exc:
            raise NotFound("Event not found.") from exc
        return Response(status=204)


class EventAudienceView(OrganizationScopedAPIView):
    def get(self, request, org_id, event_id):
        organization = self.get_organization(request, org_id)
        try:
            if can_view_events(request.user, organization):
                event = get_event(organization, event_id)
            else:
                require_can_view_relevant_events(request.user, organization)
                event = get_event_for_user(organization, event_id, request.user)
        except Event.DoesNotExist as exc:
            raise NotFound("Event not found.") from exc
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(EventAudienceSummarySerializer(get_event_audience_summary(event)).data)

    def put(self, request, org_id, event_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_events(request.user, organization)
        serializer = EventAudienceWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            event = get_event(organization, event_id)
            event = replace_event_audience(event, serializer.validated_data)
        except Event.DoesNotExist as exc:
            raise NotFound("Event not found.") from exc
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(EventAudienceSummarySerializer(get_event_audience_summary(event)).data)


class RelevantEventListView(OrganizationScopedAPIView):
    def get(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_view_relevant_events(request.user, organization)
        try:
            events = list_relevant_events(organization, request.user, request.query_params)
        except Exception as exc:
            self.handle_domain_error(exc)
        serializer = EventReadSerializer(events, many=True, context={"request": request})
        return Response(serializer.data)


class UpcomingRelevantEventListView(OrganizationScopedAPIView):
    def get(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_view_relevant_events(request.user, organization)
        try:
            events = list_upcoming_relevant_events(organization, request.user, request.query_params)
        except Exception as exc:
            self.handle_domain_error(exc)
        serializer = EventReadSerializer(events, many=True, context={"request": request})
        return Response(serializer.data)


class MyEventResponsesView(OrganizationScopedAPIView):
    def get(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_view_relevant_events(request.user, organization)
        responses = list_my_rsvp_responses(organization, request.user, request.query_params)
        payload = [
            {
                "event": row["event"],
                "status": row["status"],
                "note": row["rsvp"].note if row["rsvp"] else None,
                "responded_at": row["rsvp"].responded_at if row["rsvp"] else None,
                "updated_at": row["rsvp"].updated_at if row["rsvp"] else None,
            }
            for row in responses
        ]
        serializer = MyEventResponseSerializer(payload, many=True, context={"request": request})
        return Response(serializer.data)


class MyRSVPView(OrganizationScopedAPIView):
    def get(self, request, org_id, event_id):
        organization = self.get_organization(request, org_id)
        require_can_rsvp_to_events(request.user, organization)
        try:
            event = get_event_for_user(organization, event_id, request.user)
        except Event.DoesNotExist as exc:
            raise NotFound("Event not found.") from exc
        except Exception as exc:
            self.handle_domain_error(exc)

        member_profile = get_linked_active_member_profile(organization, request.user)
        if member_profile is None:
            raise PermissionDenied("No active member profile is linked to the current user.")
        rsvp = get_member_event_rsvp(event, member_profile)
        payload = {
            "status": rsvp.status if rsvp else "no_response",
            "note": rsvp.note if rsvp else None,
            "responded_at": rsvp.responded_at if rsvp else None,
            "updated_at": rsvp.updated_at if rsvp else None,
        }
        return Response(CurrentMemberRSVPSerializer(payload).data)

    def put(self, request, org_id, event_id):
        organization = self.get_organization(request, org_id)
        require_can_rsvp_to_events(request.user, organization)
        serializer = RSVPUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member_profile = get_linked_active_member_profile(organization, request.user)
        if member_profile is None:
            raise PermissionDenied("No active member profile is linked to the current user.")

        try:
            event = get_event_for_user(organization, event_id, request.user)
            rsvp = upsert_member_rsvp(event, member_profile, serializer.validated_data)
        except Event.DoesNotExist as exc:
            raise NotFound("Event not found.") from exc
        except Exception as exc:
            self.handle_domain_error(exc)

        payload = {
            "status": rsvp.status if rsvp else "no_response",
            "note": rsvp.note if rsvp else None,
            "responded_at": rsvp.responded_at if rsvp else None,
            "updated_at": rsvp.updated_at if rsvp else None,
        }
        return Response(CurrentMemberRSVPSerializer(payload).data)


class EventRSVPListView(OrganizationScopedAPIView):
    def get(self, request, org_id, event_id):
        organization = self.get_organization(request, org_id)
        require_can_view_events(request.user, organization)
        try:
            event = get_event(organization, event_id)
        except Event.DoesNotExist as exc:
            raise NotFound("Event not found.") from exc
        payload = {
            "event_id": event.id,
            "summary": get_event_rsvp_summary(event),
            "responses": list_event_rsvps(event),
        }
        serializer = EventRSVPListSerializer(payload)
        return Response(serializer.data)


class AttendanceRosterView(OrganizationScopedAPIView):
    def get(self, request, org_id, event_id):
        organization = self.get_organization(request, org_id)
        require_can_record_attendance(request.user, organization)
        try:
            event = get_event(organization, event_id)
        except Event.DoesNotExist as exc:
            raise NotFound("Event not found.") from exc
        payload = {
            "event_id": event.id,
            "summary": get_event_attendance_summary(event),
            "roster": [
                {
                    **row,
                    "recorded_by_user_id": row["recorded_by_user"].id
                    if row["recorded_by_user"]
                    else None,
                }
                for row in list_attendance_roster(event)
            ],
        }
        serializer = AttendanceRosterSerializer(payload)
        return Response(serializer.data)

    def put(self, request, org_id, event_id):
        organization = self.get_organization(request, org_id)
        require_can_record_attendance(request.user, organization)
        serializer = AttendanceBulkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            event = get_event(organization, event_id)
            event = bulk_upsert_attendance(
                event, request.user, serializer.validated_data["records"]
            )
        except Event.DoesNotExist as exc:
            raise NotFound("Event not found.") from exc
        except Exception as exc:
            self.handle_domain_error(exc)
        payload = {
            "event_id": event.id,
            "summary": get_event_attendance_summary(event),
            "roster": [
                {
                    **row,
                    "recorded_by_user_id": row["recorded_by_user"].id
                    if row["recorded_by_user"]
                    else None,
                }
                for row in list_attendance_roster(event)
            ],
        }
        return Response(AttendanceRosterSerializer(payload).data)
