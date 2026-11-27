"""Middleware that turns on the language of the user for every request"""

from typing import Any, Callable

from django.core.cache import cache
from django.utils import translation  
from django.http import HttpRequest, HttpResponse
from django.conf import settings


from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

USER_LANGUAGE_KEY = "user_lang:{user_id}"
USER_LANGUAGE_TIMEOUT = 60 * 60 * 24 #it like 1 day 


class UserLanguageMiddleware: 
    """Lang: from Redis for a user, from Accept-Language for guest """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.jwt_authentication: JWTAuthentication = JWTAuthentication()

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Activate the language, run the view, add Content-Language"""
        language: str = self.get_language(request)
        translation.activate(language)
        request.LANGUAGE_CODE = language

        response: HttpResponse = self.get_response(request)

        response.headers["Content-Language"] = translation.get_language()
        translation.deactivate()
        return response

    def get_language(self, request: HttpResponse)-> str:
        """return the lang code for this reqs: en,ru,kk"""
        user_id: str | None = self.get_user_id(request)
        if user_id is None: 
            return translation.get_language_from_request(request)

        key: str = USER_LANGUAGE_KEY.format(user_id = user_id)
        language: str | None = cache.get(key)
        if language is None: 
            language = (
                self.get_user_model()
                .objects.filter(id=user_id)
                .values_list("prefered_language", flat = True)
                .first()
            ) or settings.LANGUAGE_CODE
            cache.set(key, language, USER_LANGUAGE_TIMEOUT)
        return language


    def get_user_id(self, request: HttpRequest) -> str | None: 
        """Read the user id from JWT without a SQL(DB) query"""
        try:
            header: bytes | None = self.jwt_authentication.get_header(request)
            if header is None: 
                return None
            raw_token: bytes | None = self.jwt_authentication.get_raw_token(header)
            if raw_token is None:
                return None
            token: Any = self.jwt_authentication.get_validated_token(raw_token)
        except: 
            return None
        return str(token["user_id"])    
         
        