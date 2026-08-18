from fastapi import APIRouter, Depends, Query, Request, Header
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import current_user
from app.repositories import TenantRepository
from app.schemas import DepartmentCreate, DepartmentStatusUpdate, DepartmentUpdate, InvitationAction, InvitationCreate, MembershipUpdate, OrganizationProfileUpdate, TenantCreate, TenantSettingsUpdate
from app.services import TenantAdminService


router = APIRouter(prefix="/api/v1", tags=["Tenant Administration"])

def require_internal_key(
    x_internal_api_key: str = Header(
        ...,
        alias="X-Internal-API-Key",
    ),
) -> None:
    if x_internal_api_key != settings.internal_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid internal API key",
        )


def svc(request: Request, db: Session = Depends(get_db)):
    return TenantAdminService(db, request.app.state.http)


@router.post("/organizations", status_code=201)
def create_organization(data: TenantCreate, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.create_organization(data, user)


@router.get("/tenants/me")
def my_tenant(user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.profile(user)


@router.get("/organizations/profile")
def organization_profile(user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.profile(user)


@router.put("/organizations/profile")
def update_organization_profile(data: OrganizationProfileUpdate, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.update_profile(data, user)


@router.get("/organizations/settings")
def organization_settings(user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.profile(user)["settings"]


@router.put("/organizations/settings")
def update_organization_settings(data: TenantSettingsUpdate, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.update_settings(data, user)


@router.get("/dashboard/organization")
def organization_dashboard(user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.dashboard(user)


@router.post("/departments", status_code=201)
@router.post("/organizations/departments", status_code=201, include_in_schema=False)
def create_department(data: DepartmentCreate, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.create_department(data, user)


@router.get("/departments")
@router.get("/organizations/departments", include_in_schema=False)
def list_departments(user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.list_departments(user)


@router.get("/organizations/departments/tree", include_in_schema=False,)
def department_tree(user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.department_tree(user)


@router.get("/organizations/departments/{department_id}", include_in_schema=False,)
def get_department(department_id: int, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.get_department(department_id, user)


@router.put("/organizations/departments/{department_id}", include_in_schema=False,)
def update_department(department_id: int, data: DepartmentUpdate, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.update_department(department_id, data, user)


@router.patch("/organizations/departments/{department_id}/status", include_in_schema=False,)
def update_department_status(department_id: int, data: DepartmentStatusUpdate, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.set_department_status(department_id, data.is_active, user)


@router.delete("/organizations/departments/{department_id}, include_in_schema=False,", status_code=204)
def delete_department(department_id: int, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    service.delete_department(department_id, user)


@router.post("/invitations", status_code=201)
@router.post("/organizations/users/invite", status_code=201)
async def invite(data: InvitationCreate, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return await service.invite(data, user)


@router.get("/organizations/invitations")
def list_invitations(status_filter: str | None = Query(default=None, alias="status"), user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.list_invitations(user, status_filter)


@router.get("/organizations/invitations/preview")
def preview_invitation(token: str = Query(min_length=20), service: TenantAdminService = Depends(svc)):
    return service.preview_invitation(token)


@router.post("/invitations/accept")
@router.post("/organizations/invitations/accept")
async def accept_invitation(data: InvitationAction, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return await service.accept_invitation(data.token, user)


@router.post("/invitations/reject")
@router.post("/organizations/invitations/reject")
def reject_invitation(data: InvitationAction, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.reject_invitation(data.token, user)


@router.post("/organizations/invitations/{invitation_id}/resend")
async def resend_invitation(invitation_id: int, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return await service.resend_invitation(invitation_id, user)


@router.delete("/organizations/invitations/{invitation_id}")
def cancel_invitation(invitation_id: int, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.cancel_invitation(invitation_id, user)


@router.get("/memberships")
@router.get("/organizations/users")
def list_memberships(user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.list_memberships(user)


@router.get("/organizations/users/{membership_id}")
def get_membership(membership_id: int, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.get_membership(membership_id, user)


@router.put("/memberships/{membership_id}")
@router.put("/organizations/users/{membership_id}")
def update_membership(membership_id: int, data: MembershipUpdate, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.update_membership(membership_id, data, user)


@router.patch("/organizations/users/{membership_id}/status")
def update_membership_status(membership_id: int, data: MembershipUpdate, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    return service.update_membership(membership_id, data, user)


@router.delete("/organizations/users/{membership_id}", status_code=204)
def delete_membership(membership_id: int, user=Depends(current_user), service: TenantAdminService = Depends(svc)):
    service.delete_membership(membership_id, user)


@router.get("/internal/memberships/validate", dependencies=[Depends(require_internal_key)], include_in_schema=False)
def validate_membership(user_id: int, tenant_id: int, service: TenantAdminService = Depends(svc)):
    return service.validate_membership(user_id, tenant_id)


@router.get("/internal/memberships/by-user/{user_id}", dependencies=[Depends(require_internal_key)])
def membership_context(user_id: int, service: TenantAdminService = Depends(svc)):
    return service.membership_context_by_user(user_id)
