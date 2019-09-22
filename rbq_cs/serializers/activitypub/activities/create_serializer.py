from rest_framework import serializers
from misaca_federation.serializers.activitypub.activities.activity_serializer import ActivitySerializer

class CreateSerializer(ActivitySerializer):
    type = serializers.ChoiceField(choices=["Create"])