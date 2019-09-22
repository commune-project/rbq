from rest_framework import serializers
from misaca_federation.models import Status

class NoteSerializer(serializers.ModelSerializer):
    id = serializers.URLField(source='uri')
    type = serializers.ChoiceField(choices=["Note"])
    class Meta:
        model = Status
        fields = (
            'id',
        )
