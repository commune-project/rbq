from rest_framework import viewsets, permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.versioning import NamespaceVersioning
from rbq_backend.models import Account
from rbq_cs.serializers.mastodon.account_serializer import AccountSerializer
from rbq_cs.paginations import MastodonPagination

class AccountPermission(permissions.BasePermission):
    "Permission to view or modify any account."
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and (request.user.is_staff or request.user == obj):
            return True
        else:
            if request.method in permissions.SAFE_METHODS:
                if obj.is_locked:
                    return obj.followers.filter(id=request.user.id).count() == 1
                else:
                    return True
            else:
                # Modifications
                return False

class AccountViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = Account.objects.filter(type__in=["Person", "Service"])
    pagination_class = MastodonPagination
    serializer_class = AccountSerializer
    permission_classes = [AccountPermission]
    versioning_class = NamespaceVersioning

    def list(self, request):
        return Response(status=403)

    @action(detail=True, methods=["GET"])
    def followers(self, request: Request, pk: int = None) -> Response:
        """
        Accounts which follow the given account.

        Returns array of Account
        """
        followers = self.get_object().followers.all()
        page = self.paginate_queryset(followers)
        if page is not None:
            return self.get_paginated_response(self.serializer_class(page, many=True).data)
        return Response(self.serializer_class(followers, many=True).data)

    @action(detail=True, methods=["GET"])
    def following(self, request: Request, pk: int = None) -> Response:
        """
        Accounts which the given account is following.

        Returns array of Account
        """
        following = self.get_object().following.all()

        page = self.paginate_queryset(following)
        if page is not None:
            return self.get_paginated_response(self.serializer_class(page, many=True).data)
        return Response(self.serializer_class(following, many=True).data)

    @action(detail=False, methods=["PATCH"])
    def update_credentials(self, request: Request) -> Response:
        """
        Update user’s own account.

        Returns Account.
        """
        account = self.request.user
        return Response(self.serializer_class(account).data)
