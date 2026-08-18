from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.dependencies.auth import current_user
from app.repositories import UserRepository
from app.schemas import AccountSettingsUpdate, ChangePasswordRequest, UserProfileUpdate
from app.services import UserService


router = APIRouter(prefix="/api/v1", tags=["Users"])


def svc(request: Request, db: Session = Depends(get_db)):
    return UserService(UserRepository(db), request.app.state.http)


def require_internal_key(x_internal_api_key: str = Header(...)):
    if x_internal_api_key != settings.internal_api_key:
        raise HTTPException(401, "Invalid internal API key")


@router.post("/internal/users/{user_id}/bootstrap", dependencies=[Depends(require_internal_key)])
def bootstrap_profile(user_id: int, db: Session = Depends(get_db)):
    UserRepository(db).ensure(user_id)
    return {"message": "User profile initialized", "user_id": user_id}


@router.get("/users/me")
@router.get("/users/profile")
async def profile(user=Depends(current_user), service: UserService = Depends(svc)):
    return await service.profile(user)


@router.put("/users/profile")
async def update_profile(data: UserProfileUpdate, user=Depends(current_user), service: UserService = Depends(svc)):
    return await service.update_profile(data, user)


@router.put("/users/settings")
@router.put("/users/account-settings")
async def update_settings(data: AccountSettingsUpdate, user=Depends(current_user), service: UserService = Depends(svc)):
    return await service.update_settings(data, user)


@router.post("/users/change-password")
async def change_password(data: ChangePasswordRequest, response: Response, user=Depends(current_user), service: UserService = Depends(svc)):
    result = await service.change_password(data, user)
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return result


@router.get("/users/dashboard", include_in_schema=False)
@router.get("/dashboard/individual")
async def dashboard(user=Depends(current_user), service: UserService = Depends(svc)):
    return await service.dashboard(user)
