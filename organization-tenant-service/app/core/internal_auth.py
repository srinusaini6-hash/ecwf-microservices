import os

from fastapi import Header, HTTPException, status

INTERNAL_API_KEY = os.getenv(
    "INTERNAL_API_KEY",
    "ecwf-internal-key",
)


def verify_internal_api_key(
    x_internal_api_key: str = Header(...),
):
    if x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Internal API Key",
        )