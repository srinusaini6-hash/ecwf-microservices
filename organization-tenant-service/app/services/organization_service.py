from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.organization_repository import OrganizationRepository
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.schemas.tenant import TenantCreate, TenantUpdate


class OrganizationService:

    # ---------------- Organization ---------------- #

    @staticmethod
    def create_organization(db: Session, organization: OrganizationCreate):
        return OrganizationRepository.create_organization(db, organization)

    @staticmethod
    def get_organization(db: Session, organization_id: int):
        organization = OrganizationRepository.get_organization_by_id(
            db, organization_id
        )

        if not organization:
            raise HTTPException(
                status_code=404,
                detail="Organization not found",
            )

        return organization

    @staticmethod
    def get_all_organizations(db: Session):
        return OrganizationRepository.get_all_organizations(db)

    @staticmethod
    def update_organization(
        db: Session,
        organization_id: int,
        organization: OrganizationUpdate,
    ):
        db_organization = OrganizationRepository.get_organization_by_id(
            db, organization_id
        )

        if not db_organization:
            raise HTTPException(
                status_code=404,
                detail="Organization not found",
            )

        return OrganizationRepository.update_organization(
            db,
            db_organization,
            organization,
        )

    @staticmethod
    def delete_organization(db: Session, organization_id: int):
        db_organization = OrganizationRepository.get_organization_by_id(
            db, organization_id
        )

        if not db_organization:
            raise HTTPException(
                status_code=404,
                detail="Organization not found",
            )

        OrganizationRepository.delete_organization(
            db,
            db_organization,
        )

        return {"message": "Organization deleted successfully"}

    # ---------------- Tenant ---------------- #

    @staticmethod
    def create_tenant(db: Session, tenant: TenantCreate):
        organization = OrganizationRepository.get_organization_by_id(
            db,
            tenant.organization_id,
        )

        if not organization:
            raise HTTPException(
                status_code=404,
                detail="Organization not found",
            )

        return OrganizationRepository.create_tenant(db, tenant)

    @staticmethod
    def get_tenant(db: Session, tenant_id: int):
        tenant = OrganizationRepository.get_tenant_by_id(db, tenant_id)

        if not tenant:
            raise HTTPException(
                status_code=404,
                detail="Tenant not found",
            )

        return tenant

    @staticmethod
    def get_all_tenants(db: Session):
        return OrganizationRepository.get_all_tenants(db)

    @staticmethod
    def update_tenant(
        db: Session,
        tenant_id: int,
        tenant: TenantUpdate,
    ):
        db_tenant = OrganizationRepository.get_tenant_by_id(
            db,
            tenant_id,
        )

        if not db_tenant:
            raise HTTPException(
                status_code=404,
                detail="Tenant not found",
            )

        return OrganizationRepository.update_tenant(
            db,
            db_tenant,
            tenant,
        )

    @staticmethod
    def delete_tenant(db: Session, tenant_id: int):
        db_tenant = OrganizationRepository.get_tenant_by_id(
            db,
            tenant_id,
        )

        if not db_tenant:
            raise HTTPException(
                status_code=404,
                detail="Tenant not found",
            )

        OrganizationRepository.delete_tenant(
            db,
            db_tenant,
        )

        return {"message": "Tenant deleted successfully"}