from django.shortcuts import render, get_object_or_404
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import api_view, action, renderer_classes, parser_classes, authentication_classes
from rbq_backend.models import Account, ASObject, ASActivity
from rbq_ap.serializers.actor import ActorSerializer
from rest_framework.request import Request
from rest_framework.response import Response
from rbq_backend.components import webfinger_component
from rbq_backend.view_mixins import AtDomainViewMixin
from rbq_ap.components import inbox_component, account_component
from rbq_ap.auth import APSignatureAuthentication

from rbq_ap.renderers import ActivityStreamsRenderer, ActivityStreamsLDJSONRenderer, WebfingerRenderer
from rbq_ap.parsers import ActivityStreamsParser


class ActorViewSet(AtDomainViewMixin, viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    base_name = 'user'
    queryset = Account.objects.all()
    serializer_class = ActorSerializer
    renderer_classes = (ActivityStreamsRenderer, ActivityStreamsLDJSONRenderer)
    parser_classes = (ActivityStreamsParser,)
    lookup_field = 'username'
    lookup_value_regex = r'[^@\/]+'

    @action(detail=True, methods=["POST"])
    def inbox(self, request: Request, username: str=None) -> Response:
        inbox_component.Inbox(request).handler(request.data)
        return Response(status=200)

    @action(detail=True, methods=["GET"])
    def followers(self, request: Request, username: str=None) -> Response:
        account = self.get_object()
        if 'page' in request.query_params.keys():
            page = int(request.query_params["page"])
            return Response(data=account_component.gen_followers_paged(account, page=page))
        else:
            return Response(data=account_component.gen_followers(account))

    @action(detail=True, methods=["GET"])
    def following(self, request: Request, username: str=None) -> Response:
        account = self.get_object()
        if 'page' in request.query_params.keys():
            page = int(request.query_params["page"])
            return Response(data=account_component.gen_following_paged(account, page=page))
        else:
            return Response(data=account_component.gen_following(account))


@api_view(["POST"])
@parser_classes((ActivityStreamsParser,))
def inbox_view(request: Request) -> Response:
    inbox_component.Inbox(request).handler(request.data)
    return Response(status=200)


@api_view(['GET'])
def find_object_or_activity(req: Request, path: str) -> Response:
    uri = "%s://%s/%s" % ("https", req.headers['Host'], path)
    try:
        obj = ASObject.objects.get(data__id=uri)
        return Response(data=obj.data)
    except ASObject.DoesNotExist:
        return Response(status=404)


@api_view(['GET'])
@renderer_classes((WebfingerRenderer,))
def webfinger(request: Request) -> Response:
    resource = request.query_params['resource']
    try:
        data = webfinger_component.webfinger(resource)
        return Response(data=data)
    except Account.DoesNotExist:
        return Response(status=404)
