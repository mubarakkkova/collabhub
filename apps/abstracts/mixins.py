"""Mixins for ViewSets of all apps"""

from typing import Any

from rest_framework.pagination import BasePagination
from rest_framework.request import Request as DRFRequest
from rest_framework.serializers import Serializer
from rest_framework.status import HTTP_200_OK
from rest_framework.response import Response as DRFResponse


class DRFResponseMixin:
    """Mixin to get DRF response."""

    def get_drf_response(
        self,
        request: DRFRequest,
        data: Any,
        serializer_class: type[Serializer],
        many: bool = False,
        paginator: BasePagination | None = None,
        status_code: int = HTTP_200_OK,
    ) -> DRFResponse:
        """Serialize the data. And Return one page if a paginator is given"""
        serializer_context: dict[str, Any] = {"request": request}

        if paginator and many:
            objects: list[Any] = paginator.paginate_query(
                queryset=data,
                request=request,
                view=self,
            )
            serializer = serializer_class(
                data,
                many=many,
                context=serializer_context,
            )
            return DRFResponse(data=serializer.data, status=status_code)
