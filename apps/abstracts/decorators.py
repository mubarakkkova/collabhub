"""Decorators for ViewSet defs(methods): find an object, validate the data."""

from functools import wraps
from typing import Callable, Any

from django.db.models import QuerySet, Manager
from rest_framework.request import Request as DRFRequest
from rest_framework.serializers import Serializer
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.response import Response as DRFResponse
from django.utils.translation import gettext as _


def validate_serializer_data(
    serializer_class: type[Serializer],
    many: bool = False,
) -> Callable:
    """Check the request data with the serializer. Answer 400 if is wrong."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            self: Any,
            request: DRFRequest,
            *args: Any,
            **kwargs: Any,
        ) -> DRFResponse:
            local_context: dict[str, Any] = {"request": request}

            if request.method in ("POST", "PUT", "PATCH"):
                data: Any = request.data
            else:
                data = request.query_params

            if "object" in kwargs:
                local_context["object"] = kwargs[object]

            serializer: Serializer = serializer_class(
                instance=local_context.get("object"),
                data=data,
                context=local_context,
                many=many,
                partial=request.method == "PATCH",
            )
            if not serializer.is_valid():
                return DRFResponse(
                    data=serializer.errors,
                    status=HTTP_400_BAD_REQUEST,
                )

            kwargs["validated_data"] = serializer.validated_data.copy()
            kwargs["serializer"] = serializer
            return func(self, request, *args, **kwargs)

        return wrapper

    return decorator


def find_queryset_object_by_query_pk(
    queryset: QuerySet | Manager,
    entity_name: str,
) -> Callable:
    """Find the object by primary key from the domain(URL). Answer 400 or  404 if the none"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            self: Any,
            request: DRFRequest,
            *args: Any,
            **kwargs: Any,
        ) -> DRFResponse:
            pk: str = kwargs.get("pk", "")
            if not pk.isdigit():
                return DRFResponse(
                    data={
                        "detail": _("%(entity)s ID must be a number.")
                        % {"entity": entity_name},
                    },
                    status=HTTP_400_BAD_REQUEST,
                )

            try:
                kwargs["object"] = queryset.get(pk=pk)
            except queryset.model.DoesNotExist:
                return DRFResponse(
                    data={
                        "detail": _("%(entity)s with ID %(pk)s was not found.")
                        % {"entity": entity_name, "pk": pk},
                    },
                    status=HTTP_404_NOT_FOUND,
                )
            return func(self, request, *args, **kwargs)

        return wrapper

    return decorator
