from typing import Any

from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission
from rest_framework.request import Request as DRFRequest

from apps.users.models import UserRole

class IsBusiness(BasePermission):
    """Allow access only for logged-in users with business role."""

    messages = _("Only a business can do this")

    def has_permission(self, request: DRFRequest, view: Any) -> bool:
        """Return True if the user is logged in and is a business"""
        user: Any = request.user
        return bool(user and user.is_authenticated and user.role == UserRole.BUSINESS)

class IsBlogger(BasePermission):
    """Allow access only for logged-in users with the blogger role"""
    messages = _("Only a blogger can do this")

    
    def has_permission(self, request: DRFRequest, view: Any) -> bool:
        """Return True if the user is logged in and is a blogger"""
        user: Any = request.user
        return bool(user and user.is_authenticated and user.role == UserRole.BLOGGER)
