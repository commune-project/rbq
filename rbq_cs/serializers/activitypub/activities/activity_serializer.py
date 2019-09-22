from rest_framework import serializers

class ActivitySerializer(serializers.Serializer):
    type = serializers.CharField()
    object = serializers.JSONField()

    def validate(self, data):
        return data