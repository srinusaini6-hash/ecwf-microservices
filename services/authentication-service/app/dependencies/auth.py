from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.core.security import decode_token
from app.database.session import get_db
from app.repositories import AuthRepository

bearer=HTTPBearer(auto_error=False,scheme_name="BearerAuth")


def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials | None = Security(bearer), db: Session = Depends(get_db)):
    token = credentials.credentials if credentials else request.cookies.get("access_token")
    if not token: raise HTTPException(401,"Access token is missing")
    try: payload=decode_token(token)
    except ValueError as exc: raise HTTPException(401,str(exc)) from exc
    if payload.get("type")!="access": raise HTTPException(401,"Invalid access token")
    user=AuthRepository(db).user_by_id(int(payload["sub"]))
    if not user or not user.is_active or user.token_version!=int(payload.get("ver",-1)): raise HTTPException(401,"Token is invalid or revoked")
    return user
