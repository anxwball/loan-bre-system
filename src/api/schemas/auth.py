"""Define authentication payloads for token issuance."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class TokenRequest(BaseModel):
    """Represent username/password credentials for token issuance."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Represent JWT token response for API clients."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    role: Literal["admin", "analyst"]
    expires_in: int
