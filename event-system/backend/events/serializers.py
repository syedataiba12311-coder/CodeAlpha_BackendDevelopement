from rest_framework import serializers
from .models import Event, Registration

class EventSerializer(serializers.ModelSerializer):
    seats_left = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ['id','title','description','date','location','capacity','seats_left']

    def get_seats_left(self, obj):
        return obj.seats_left()

class RegistrationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    event_detail = EventSerializer(source='event', read_only=True)

    class Meta:
        model = Registration
        fields = ['id','user','event','event_detail','registered_at','status']
        read_only_fields = ['registered_at','status','user']
