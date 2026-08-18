from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.internal_auth import verify_internal_api_key
from app.database.database import get_db

from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)

from app.schemas.tenant import (
    TenantCreate,
    TenantResponse,
    TenantUpdate,
)

from app.services.organization_service import OrganizationService

router = APIRouter(
    prefix="/organization",
    tags=["Organization & Tenant"],
)

# =====================================================
# Organization APIs
# =====================================================

@router.post(
    "/",
    response_model=OrganizationResponse,
)
def create_organization(
    organization: OrganizationCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_api_key),
):
    return OrganizationService.create_organization(
        db,
        organization,
    )


@router.get(
    "/",
    response_model=list[OrganizationResponse],
)
def get_all_organizations(
    db: Session = Depends(get_db),
):
    return OrganizationService.get_all_organizations(db)


# =====================================================
# Tenant APIs
# =====================================================

@router.post(
    "/tenant",
    response_model=TenantResponse,
)
def create_tenant(
    tenant: TenantCreate,
    db: Session = Depends(get_db),
):
    return OrganizationService.create_tenant(
        db,
        tenant,
    )


@router.get(
    "/tenant",
    response_model=list[TenantResponse],
)
def get_all_tenants(
    db: Session = Depends(get_db),
):
    return OrganizationService.get_all_tenants(db)


@router.get(
    "/tenant/{tenant_id}",
    response_model=TenantResponse,
)
def get_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    return OrganizationService.get_tenant(
        db,
        tenant_id,
    )


@router.put(
    "/tenant/{tenant_id}",
    response_model=TenantResponse,
)
def update_tenant(
    tenant_id: int,
    tenant: TenantUpdate,
    db: Session = Depends(get_db),
):
    return OrganizationService.update_tenant(
        db,
        tenant_id,
        tenant,
    )


@router.delete(
    "/tenant/{tenant_id}",
)
def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    return OrganizationService.delete_tenant(
        db,
        tenant_id,
    )


# =====================================================
# Organization APIs with Path Parameter
# =====================================================

@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
def get_organization(
    organization_id: int,
    db: Session = Depends(get_db),
):
    return OrganizationService.get_organization(
        db,
        organization_id,
    )


@router.put(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
def update_organization(
    organization_id: int,
    organization: OrganizationUpdate,
    db: Session = Depends(get_db),
):
    return OrganizationService.update_organization(
        db,
        organization_id,
        organization,
    )


@router.delete(
    "/{organization_id}",
)
def delete_organization(
    organization_id: int,
    db: Session = Depends(get_db),
):
    return OrganizationService.delete_organization(
        db,
        organization_id,
    )