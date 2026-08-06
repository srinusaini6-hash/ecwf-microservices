from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.models.organization import Organization
from app.models.tenant import Tenant

from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
)

from app.schemas.tenant import (
    TenantCreate,
    TenantUpdate,
)


class OrganizationRepository:

    # ==================================================
    # Organization
    # ==================================================

    @staticmethod
    def create_organization(
        db: Session,
        organization: OrganizationCreate,
    ):
        existing = (
            db.query(Organization)
            .filter(Organization.name == organization.name)
            .first()
        )

        if existing:
            return existing

        db_organization = Organization(
            **organization.model_dump()
        )

        try:
            db.add(db_organization)
            db.commit()
            db.refresh(db_organization)
            return db_organization

        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Organization already exists.",
            )

    @staticmethod
    def get_organization_by_id(
        db: Session,
        organization_id: int,
    ):
        return (
            db.query(Organization)
            .filter(
                Organization.id == organization_id
            )
            .first()
        )

    @staticmethod
    def get_all_organizations(
        db: Session,
    ):
        return db.query(Organization).all()

    @staticmethod
    def update_organization(
        db: Session,
        db_organization: Organization,
        organization: OrganizationUpdate,
    ):
        update_data = organization.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():
            setattr(
                db_organization,
                key,
                value,
            )

        db.commit()
        db.refresh(db_organization)

        return db_organization

    @staticmethod
    def delete_organization(
        db: Session,
        db_organization: Organization,
    ):
        db.delete(db_organization)
        db.commit()

    # ==================================================
    # Tenant
    # ==================================================

    @staticmethod
    def create_tenant(
        db: Session,
        tenant: TenantCreate,
    ):
        db_tenant = Tenant(
            **tenant.model_dump()
        )

        db.add(db_tenant)
        db.commit()
        db.refresh(db_tenant)

        return db_tenant

    @staticmethod
    def get_tenant_by_id(
        db: Session,
        tenant_id: int,
    ):
        return (
            db.query(Tenant)
            .filter(
                Tenant.id == tenant_id
            )
            .first()
        )

    @staticmethod
    def get_all_tenants(
        db: Session,
    ):
        return db.query(Tenant).all()

    @staticmethod
    def update_tenant(
        db: Session,
        db_tenant: Tenant,
        tenant: TenantUpdate,
    ):
        update_data = tenant.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():
            setattr(
                db_tenant,
                key,
                value,
            )

        db.commit()
        db.refresh(db_tenant)

        return db_tenant

    @staticmethod
    def delete_tenant(
        db: Session,
        db_tenant: Tenant,
    ):
        db.delete(db_tenant)
        db.commit()