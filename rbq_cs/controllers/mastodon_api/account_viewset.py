from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.versioning import NamespaceVersioning
from rbq_backend.models import Account
from rbq_backend.view_mixins import AtDomainViewMixin
from rbq_cs.serializers.mastodon.account_serializer import AccountSerializer

class AccountPermission(permissions.BasePermission):
    "Permission to view or modify any account."
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and (request.user.is_staff or request.user == obj):
            return True
        else:
            if request.method in permissions.SAFE_METHODS:
                if obj.is_locked:
                    return obj.followers.filter(id=request.user.id).count()==1
                else:
                    return True
            else:
                # Modifications
                return False

class AccountViewSet(AtDomainViewMixin, viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = Account.objects.filter(type__in=["Person", "Service"])
    serializer_class = AccountSerializer
    permission_classes = [AccountPermission]
    versioning_class = NamespaceVersioning
    lookup_field = 'username'
    lookup_value_regex = r'[^@\/]+'

    def list(self, request):
        return Response(status=403)

    @action(detail=True, methods=["GET"])
    def followers(self, request, pk=None):
        followers = get_object_or_404(Account.objects.all(), username=self._get_username(pk)).followers
        return Response(self.serializer_class(followers, many=True).data)

    @action(detail=True, methods=["GET"])
    def following(self, request, pk=None):
        following = get_object_or_404(Account.objects.all(), username=self._get_username(pk)).following
        return Response(self.serializer_class(following, many=True).data)
