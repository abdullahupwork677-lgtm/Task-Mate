"""Authentication module exports."""

from src.auth.dependencies import get_current_user
from src.auth.jwt import create_jwt_token, verify_jwt_token, get_token_expiry_seconds
from src.auth.password import verify_password, hash_password

# Backward compatibility alias
create_access_token = create_jwt_token

__all__ = [
    "get_current_user",
    "create_jwt_token",
    "create_access_token",  # Backward compatibility
    "verify_jwt_token",
    "get_token_expiry_seconds",
    "verify_password",
    "hash_password",
]
