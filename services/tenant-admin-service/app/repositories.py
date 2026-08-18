from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Department, Invitation, Membership, Tenant, TenantSetting


class TenantRepository:
    def __init__(self, db: Session):
        self.db = db

    def tenant(self, tenant_id: int):
        return self.db.get(Tenant, tenant_id)

    def tenant_by_owner(self, user_id: int):
        return self.db.scalar(select(Tenant).where(Tenant.owner_user_id == user_id))

    def tenant_by_slug(self, slug: str):
        return self.db.scalar(select(Tenant).where(Tenant.slug == slug))

    def create_tenant(self, obj: Tenant):
        self.db.add(obj)
        self.db.flush()
        return obj

    def settings(self, tenant_id: int):
        return self.db.get(TenantSetting, tenant_id)

    def membership(self, user_id: int, tenant_id: int | None = None, active_only: bool = False):
        q = select(Membership).where(Membership.user_id == user_id)
        if tenant_id is not None:
            q = q.where(Membership.tenant_id == tenant_id)
        if active_only:
            q = q.where(Membership.status == "active")
        return self.db.scalar(q)

    def memberships_for_user(self, user_id: int):
        return list(self.db.scalars(select(Membership).where(Membership.user_id == user_id)))

    def memberships(self, tenant_id: int):
        return list(self.db.scalars(select(Membership).where(Membership.tenant_id == tenant_id).order_by(Membership.id)))

    def membership_by_id(self, membership_id: int):
        return self.db.get(Membership, membership_id)

    def count_memberships(self, tenant_id: int, status: str | None = None):
        q = select(func.count(Membership.id)).where(Membership.tenant_id == tenant_id)
        if status:
            q = q.where(Membership.status == status)
        return int(self.db.scalar(q) or 0)

    def department(self, department_id: int):
        return self.db.get(Department, department_id)

    def departments(self, tenant_id: int):
        return list(self.db.scalars(select(Department).where(Department.tenant_id == tenant_id).order_by(Department.id)))

    def invitation(self, invitation_id: int):
        return self.db.get(Invitation, invitation_id)

    def invitation_by_hash(self, token_hash: str):
        return self.db.scalar(select(Invitation).where(Invitation.token_hash == token_hash))

    def pending_invitation(self, tenant_id: int, email: str):
        return self.db.scalar(select(Invitation).where(Invitation.tenant_id == tenant_id, Invitation.email == email.lower(), Invitation.status == "pending"))

    def invitations(self, tenant_id: int, status: str | None = None):
        q = select(Invitation).where(Invitation.tenant_id == tenant_id).order_by(Invitation.created_at.desc())
        if status:
            q = q.where(Invitation.status == status)
        return list(self.db.scalars(q))

    def save(self, obj):
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj):
        self.db.delete(obj)
        self.db.commit()

    def commit(self):
        self.db.commit()
