from rest_framework import viewsets
from rest_framework.response import Response
from rbq_backend.models import Status
from rbq_cs.serializers.mastodon.status_serializer import StatusSerializer

class StatusViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = Status.objects.all()
    serializer_class = StatusSerializer
    #permission_classes = [IsAccountAdminOrReadOnly]
