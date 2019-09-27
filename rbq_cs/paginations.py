from typing import Dict, Optional

from django.db.models import QuerySet
from rest_framework import pagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.utils.urls import remove_query_param, replace_query_param

class MastodonPagination(pagination.LimitOffsetPagination):
    limit_query_param: str = 'limit'
    default_limit: int = 40
    min_id_query_param: str = 'min_id'
    max_id_query_param: str = 'max_id'
    queryset_id_field: str = 'id'

    def paginate_queryset(self, queryset: QuerySet, request: Request, view=None) -> Optional[list]:
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        self.queryset = queryset
        self.request = request
        self.limit: int = self.get_limit(request)

        new_queryset = queryset
        try:
            self.max_id: int = request.query_params[self.max_id_query_param]
            new_queryset = self._gen_subset(new_queryset, max_id=self.max_id)
        except (KeyError, ValueError):
            self.max_id: int = new_queryset.last().id
        try:
            self.min_id: int = request.query_params[self.min_id_query_param]
            new_queryset = self._gen_subset(new_queryset, min_id=self.min_id)
        except (KeyError, ValueError):
            self.min_id: int = 0

        return list(new_queryset[:self.limit])

    def get_paginated_response(self, data):
        rels = {
            "prev": self.get_previous_link(),
            "next": self.get_next_link()
        }

        link = '; '.join(['<%s>; rel="%s"' % (rels[k], k) for k in rels if rels[k] is not None])

        return Response(data, headers={
            "link": link
        })

    def get_next_link(self) -> Optional[str]:
        "Returns the link url pointed to next subset."
        if self._gen_subset(self.queryset, min_id=self.max_id)[:self.limit].count() <= 0:
            return None
        url = self.request.build_absolute_uri()
        url = replace_query_param(url, self.limit_query_param, self.limit)
        url = replace_query_param(url, self.min_id_query_param, self.max_id)
        url = remove_query_param(url, self.max_id_query_param)
        return url

    def get_previous_link(self) -> Optional[str]:
        "Returns the link url pointed to previous subset."
        if self._gen_subset(self.queryset, max_id=self.min_id)[:self.limit].count() <= 0:
            return None
        url = self.request.build_absolute_uri()
        url = replace_query_param(url, self.limit_query_param, self.limit)
        url = replace_query_param(url, self.max_id_query_param, self.max_id)
        url = remove_query_param(url, self.min_id_query_param)
        return url

    def _gen_subset(self,
                    queryset: QuerySet,
                    min_id: int = None,
                    max_id: int = None) -> QuerySet:
        "Generate a subset of the QuerySet by min_id and max_id"
        if min_id is not None:
            queryset = queryset.filter(**{self.queryset_id_field+"__gt": min_id})
        if max_id is not None:
            queryset = queryset.filter(**{self.queryset_id_field+"__lt": max_id})
        return queryset
