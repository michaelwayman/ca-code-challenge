from django.contrib.auth import authenticate
from ninja import NinjaAPI, Schema

from .tokens import SigningKeyMissing, issue_token

api = NinjaAPI(urls_namespace="auth", docs_url=None)


class LoginIn(Schema):
    username: str
    password: str


class TokenOut(Schema):
    access_token: str
    token_type: str
    expires_in: int


class ErrorOut(Schema):
    detail: str


@api.post("/auth/login", response={200: TokenOut, 401: ErrorOut, 503: ErrorOut}, auth=None)
def login(request, payload: LoginIn):
    user = authenticate(request, username=payload.username, password=payload.password)
    if user is None:
        return 401, {"detail": "Invalid credentials"}
    try:
        return 200, issue_token(user)
    except SigningKeyMissing as exc:
        return 503, {"detail": str(exc)}
