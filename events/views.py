from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Event, Registration
from .serializers import EventSerializer, RegistrationSerializer

class EventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve events. (Read-only for public)
    """
    queryset = Event.objects.all().order_by('date')
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]

class RegistrationViewSet(viewsets.ModelViewSet):
    """
    Users can list/create their registrations; cancel is a custom action.
    """
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # users only get their own registrations
        return Registration.objects.filter(user=self.request.user).select_related('event')

    def perform_create(self, serializer):
        event = serializer.validated_data['event']
        # capacity check
        active_count = event.registrations.filter(status=Registration.STATUS_ACTIVE).count()
        if active_count >= event.capacity:
            raise serializers.ValidationError({'event': 'Event capacity reached'})
        # unique_together will also protect, but check friendly message:
        if Registration.objects.filter(user=self.request.user, event=event, status=Registration.STATUS_ACTIVE).exists():
            raise serializers.ValidationError({'detail': 'You are already registered for this event.'})
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        reg = self.get_object()
        if reg.user != request.user:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        if reg.status == Registration.STATUS_CANCELED:
            return Response({'detail': 'Already canceled'}, status=status.HTTP_400_BAD_REQUEST)
        reg.status = Registration.STATUS_CANCELED
        reg.save()
        return Response({'status': 'canceled'})
