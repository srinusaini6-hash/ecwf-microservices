import hashlib
import re
import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException
from httpx import AsyncClient

from app.core.config import settings
from app.models import Department, Invitation, Membership, Tenant, TenantSetting
from app.repositories import TenantRepository


class TenantAdminService:
    def __init__(self, db, http: AsyncClient):
        self.db = db
        self.repo = TenantRepository(db)
        self.http = http

    def create_organization(self, data, user: dict):
        if user.get("account_type") != "organization":
            raise HTTPException(403, "Only organization accounts can create an organization")
        if user.get("role") != "tenant_admin":
            raise HTTPException(403, "Tenant administrator permission required")

        owner_user_id = int(user["id"])
        existing = self.repo.tenant_by_owner(owner_user_id)
        if existing:
            raise HTTPException(409, "This tenant administrator already owns an organization")

        slug = data.slug or self._slugify(data.name)
        if self.repo.tenant_by_slug(slug):
            raise HTTPException(409, "Organization slug already exists")

        account_domain = str(user["email"]).rsplit("@", 1)[1].lower()
        primary_domain = data.primary_domain.strip().lower()
        if account_domain != primary_domain:
            raise HTTPException(400, "Organization primary domain must match the tenant administrator business email domain")

        tenant = Tenant(
            name=data.name,
            slug=slug,
            primary_domain=primary_domain,
            organization_type=data.organization_type,
            industry=data.industry,
            owner_user_id=owner_user_id,
            status="active",
        )
        self.repo.create_tenant(tenant)

        settings_obj = TenantSetting(
            tenant_id=tenant.id,
            allowed_domains=[primary_domain],
        )
        self.db.add(settings_obj)

        root = Department(
            tenant_id=tenant.id,
            name=f"{data.name} Root",
            code="ROOT",
            parent_id=None,
            description="Root department",
            is_active=True,
        )
        self.db.add(root)

        membership = Membership(
            tenant_id=tenant.id,
            user_id=owner_user_id,
            department_id=None,
            role_code="tenant_admin",
            status="active",
        )
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(tenant)
        self.db.refresh(settings_obj)
        self.db.refresh(membership)

        return {
            "tenant_id": tenant.id,
            "organization": tenant,
            "settings": settings_obj,
            "membership_id": membership.id,
        }

    def tenant_context(self, user: dict):
        memberships = [m for m in self.repo.memberships_for_user(user["id"]) if m.status == "active"]
        if not memberships:
            raise HTTPException(403, "Organization membership required")
        membership = memberships[0]
        tenant = self.repo.tenant(membership.tenant_id)
        if not tenant or tenant.status != "active":
            raise HTTPException(403, "Organization is inactive")
        return membership, tenant

    def require_admin(self, user: dict):
        membership, tenant = self.tenant_context(user)
        if membership.role_code not in {"tenant_admin", "super_admin"}:
            raise HTTPException(403, "Tenant administrator required")
        return membership, tenant

    def profile(self, user: dict):
        membership, tenant = self.tenant_context(user)
        return {"organization": tenant, "settings": self.repo.settings(tenant.id), "membership": membership}

    def update_profile(self, data, user: dict):
        _, tenant = self.require_admin(user)
        for key, value in data.model_dump(exclude_none=True).items():
            setattr(tenant, key, value)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def update_settings(self, data, user: dict):
        _, tenant = self.require_admin(user)
        obj = self.repo.settings(tenant.id) or TenantSetting(tenant_id=tenant.id)
        for key, value in data.model_dump().items():
            setattr(obj, key, value)
        return self.repo.save(obj)

    def dashboard(self, user: dict):
        membership, tenant = self.tenant_context(user)
        return {
            "tenant_id": tenant.id,
            "organization_name": tenant.name,
            "membership_role": membership.role_code,
            "department_id": membership.department_id,
            "active_users": self.repo.count_memberships(tenant.id, "active"),
            "departments": len(self.repo.departments(tenant.id)),
            "pending_invitations": len(self.repo.invitations(tenant.id, "pending")),
        }

    def create_department(self, data, user: dict):
        _, tenant = self.require_admin(user)
        if data.parent_id is not None:
            parent = self.repo.department(data.parent_id)
            if not parent or parent.tenant_id != tenant.id:
                raise HTTPException(404, "Parent department not found in this organization")
            if not parent.is_active:
                raise HTTPException(400, "Parent department is inactive")
        if data.head_membership_id is not None:
            head = self.repo.membership_by_id(data.head_membership_id)
            if not head or head.tenant_id != tenant.id or head.status != "active":
                raise HTTPException(404, "Department head must be an active member of this organization")
        if any(d.code.lower() == data.code.lower() for d in self.repo.departments(tenant.id)):
            raise HTTPException(409, "Department code already exists")
        obj = Department(tenant_id=tenant.id, name=data.name, code=data.code, parent_id=data.parent_id, head_membership_id=data.head_membership_id, description=data.description, is_active=True)
        obj = self.repo.save(obj)
        return obj

    def list_departments(self, user: dict):
        _, tenant = self.tenant_context(user)
        return self.repo.departments(tenant.id)

    def department_tree(self, user: dict):
        departments = self.list_departments(user)
        nodes = {d.id: {"id": d.id, "name": d.name, "code": d.code, "parent_id": d.parent_id, "is_active": d.is_active, "children": []} for d in departments}
        roots = []
        for d in departments:
            node = nodes[d.id]
            if d.parent_id and d.parent_id in nodes:
                nodes[d.parent_id]["children"].append(node)
            else:
                roots.append(node)
        return roots

    def get_department(self, department_id: int, user: dict):
        _, tenant = self.tenant_context(user)
        obj = self.repo.department(department_id)
        if not obj or obj.tenant_id != tenant.id:
            raise HTTPException(404, "Department not found")
        return obj

    def update_department(self, department_id: int, data, user: dict):
        _, tenant = self.require_admin(user)
        obj = self.get_department(department_id, user)
        values = data.model_dump(exclude_unset=True)
        parent_id = values.get("parent_id")
        if parent_id == department_id:
            raise HTTPException(400, "Department cannot be its own parent")
        if parent_id is not None:
            parent = self.repo.department(parent_id)
            if not parent or parent.tenant_id != tenant.id:
                raise HTTPException(404, "Parent department not found")
            cursor = parent
            while cursor and cursor.parent_id:
                if cursor.parent_id == department_id:
                    raise HTTPException(400, "Department hierarchy cycle is not allowed")
                cursor = self.repo.department(cursor.parent_id)
        if values.get("head_membership_id") is not None:
            head = self.repo.membership_by_id(values["head_membership_id"])
            if not head or head.tenant_id != tenant.id or head.status != "active":
                raise HTTPException(404, "Invalid department head")
        for key, value in values.items():
            setattr(obj, key, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def set_department_status(self, department_id: int, is_active: bool, user: dict):
        _, tenant = self.require_admin(user)
        obj = self.get_department(department_id, user)
        if obj.code == "ROOT" and not is_active:
            raise HTTPException(400, "ROOT department cannot be deactivated")
        obj.is_active = is_active
        self.db.commit()
        return obj

    def delete_department(self, department_id: int, user: dict):
        _, tenant = self.require_admin(user)
        obj = self.get_department(department_id, user)
        if obj.code == "ROOT":
            raise HTTPException(400, "ROOT department cannot be deleted")
        if any(d.parent_id == obj.id for d in self.repo.departments(tenant.id)):
            raise HTTPException(409, "Department has child departments")
        if any(m.department_id == obj.id for m in self.repo.memberships(tenant.id)):
            raise HTTPException(409, "Department has assigned members")
        self.repo.delete(obj)

    async def invite(self, data, user: dict):
        _, tenant = self.require_admin(user)
        email = str(data.email).lower()
        registered = await self._identity_by_email(email)
        if registered["account_type"] != "individual":
            raise HTTPException(400, "Only registered individual ECWF users can be invited")
        if not registered["is_verified"] or not registered["is_active"]:
            raise HTTPException(403, "Only active verified users can be invited")
        existing_membership = self.repo.membership(registered["id"], tenant.id)
        if existing_membership and existing_membership.status == "active":
            raise HTTPException(409, "User is already a member of this organization")
        if data.department_id is not None:
            department = self.repo.department(data.department_id)
            if not department or department.tenant_id != tenant.id:
                raise HTTPException(404, "Department not found in this organization")
        if self.repo.pending_invitation(tenant.id, email):
            raise HTTPException(409, "A pending invitation already exists for this user")
        token = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        invitation = Invitation(tenant_id=tenant.id, email=email, department_id=data.department_id, role_code=data.role_code, token_hash=self._token_hash(token), status="pending", expires_at=now + timedelta(days=settings.invitation_expire_days), last_sent_at=now)
        invitation = self.repo.save(invitation)
        await self._send_invitation(invitation, tenant.name, token)
        return {"invitation_id": invitation.id, "invitation_token": token, "status": invitation.status, "expires_at": invitation.expires_at}

    def list_invitations(self, user: dict, status_filter: str | None = None):
        _, tenant = self.require_admin(user)
        return self.repo.invitations(tenant.id, status_filter)

    def preview_invitation(self, token: str):
        inv = self._valid_invitation(token)
        tenant = self.repo.tenant(inv.tenant_id)
        return {"invitation_id": inv.id, "organization_name": tenant.name, "email": inv.email, "department_id": inv.department_id, "role_code": inv.role_code, "status": inv.status, "expires_at": inv.expires_at}

    async def accept_invitation(self, token: str, user: dict):
        inv = self._valid_invitation(token)
        if inv.email.lower() != user["email"].lower():
            raise HTTPException(403, "This invitation belongs to another user")
        registered = await self._identity_by_email(user["email"])
        if registered["id"] != user["id"] or not registered["is_verified"] or not registered["is_active"]:
            raise HTTPException(403, "Authenticated user cannot accept this invitation")
        membership = self.repo.membership(user["id"], inv.tenant_id)
        if membership and membership.status == "active":
            raise HTTPException(409, "User is already an active member of this organization")
        if membership:
            membership.status = "active"
            membership.department_id = inv.department_id
            membership.role_code = inv.role_code
            membership.joined_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(membership)
        else:
            membership = self.repo.save(Membership(tenant_id=inv.tenant_id, user_id=user["id"], department_id=inv.department_id, role_code=inv.role_code, status="active"))
        inv.status = "accepted"
        inv.accepted_at = datetime.utcnow()
        inv.accepted_by_user_id = user["id"]
        self.repo.save(inv)
        return {"message": "Invitation accepted successfully", "invitation_id": inv.id, "status": inv.status, "membership_id": membership.id}

    def reject_invitation(self, token: str, user: dict):
        inv = self._valid_invitation(token)
        if inv.email.lower() != user["email"].lower():
            raise HTTPException(403, "This invitation belongs to another user")
        inv.status = "rejected"
        inv.rejected_at = datetime.utcnow()
        self.repo.save(inv)
        return {"message": "Invitation rejected", "invitation_id": inv.id, "status": inv.status, "membership_id": None}

    async def resend_invitation(self, invitation_id: int, user: dict):
        _, tenant = self.require_admin(user)
        inv = self.repo.invitation(invitation_id)
        if not inv or inv.tenant_id != tenant.id:
            raise HTTPException(404, "Invitation not found")
        if inv.status == "accepted":
            raise HTTPException(409, "Accepted invitation cannot be resent")
        token = secrets.token_urlsafe(32)
        inv.token_hash = self._token_hash(token)
        inv.status = "pending"
        inv.expires_at = datetime.utcnow() + timedelta(days=settings.invitation_expire_days)
        inv.last_sent_at = datetime.utcnow()
        inv.resend_count += 1
        self.repo.save(inv)
        await self._send_invitation(inv, tenant.name, token)
        return {"invitation_id": inv.id, "invitation_token": token, "status": inv.status, "expires_at": inv.expires_at, "resend_count": inv.resend_count}

    def cancel_invitation(self, invitation_id: int, user: dict):
        _, tenant = self.require_admin(user)
        inv = self.repo.invitation(invitation_id)
        if not inv or inv.tenant_id != tenant.id:
            raise HTTPException(404, "Invitation not found")
        if inv.status == "accepted":
            raise HTTPException(409, "Accepted invitation cannot be cancelled")
        inv.status = "cancelled"
        inv.cancelled_at = datetime.utcnow()
        self.repo.save(inv)
        return {"message": "Invitation cancelled", "invitation_id": inv.id, "status": inv.status, "membership_id": None}

    def list_memberships(self, user: dict):
        _, tenant = self.require_admin(user)
        return self.repo.memberships(tenant.id)

    def get_membership(self, membership_id: int, user: dict):
        _, tenant = self.require_admin(user)
        obj = self.repo.membership_by_id(membership_id)
        if not obj or obj.tenant_id != tenant.id:
            raise HTTPException(404, "Membership not found")
        return obj

    def update_membership(self, membership_id: int, data, user: dict):
        _, tenant = self.require_admin(user)
        obj = self.get_membership(membership_id, user)
        if data.department_id is not None:
            department = self.repo.department(data.department_id)
            if not department or department.tenant_id != tenant.id:
                raise HTTPException(404, "Department not found in this organization")
        if obj.role_code == "tenant_admin" and data.role_code and data.role_code != "tenant_admin":
            admins = [m for m in self.repo.memberships(tenant.id) if m.role_code == "tenant_admin" and m.status == "active"]
            if len(admins) <= 1:
                raise HTTPException(400, "The final Tenant Admin cannot be removed")
        for key, value in data.model_dump(exclude_none=True).items():
            setattr(obj, key, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_membership(self, membership_id: int, user: dict):
        _, tenant = self.require_admin(user)
        obj = self.get_membership(membership_id, user)
        if obj.role_code == "tenant_admin":
            admins = [m for m in self.repo.memberships(tenant.id) if m.role_code == "tenant_admin" and m.status == "active"]
            if len(admins) <= 1:
                raise HTTPException(400, "The final Tenant Admin cannot be removed")
        self.repo.delete(obj)

    def validate_membership(self, user_id: int, tenant_id: int):
        membership = self.repo.membership(user_id, tenant_id, active_only=True)
        if not membership:
            raise HTTPException(403, "No active membership")
        return {"membership_id": membership.id, "tenant_id": membership.tenant_id, "role_code": membership.role_code, "department_id": membership.department_id, "status": membership.status}

    def membership_context_by_user(self, user_id: int):
        memberships = [m for m in self.repo.memberships_for_user(user_id) if m.status == "active"]
        if not memberships:
            raise HTTPException(404, "No active organization membership")
        membership = memberships[0]
        return {"membership_id": membership.id, "tenant_id": membership.tenant_id, "role_code": membership.role_code, "department_id": membership.department_id, "status": membership.status}

    def _valid_invitation(self, token: str):
        inv = self.repo.invitation_by_hash(self._token_hash(token))
        if not inv:
            raise HTTPException(404, "Invitation not found")
        if inv.status != "pending":
            raise HTTPException(409, f"Invitation is {inv.status}")
        if inv.expires_at <= datetime.utcnow():
            inv.status = "expired"
            self.repo.save(inv)
            raise HTTPException(410, "Invitation has expired")
        return inv

    async def _identity_by_email(self, email: str):
        response = await self.http.get(f"{settings.auth_service_url}/api/v1/auth/internal/users/by-email", params={"email": email}, headers={"X-Internal-API-Key": settings.internal_api_key})
        if response.status_code == 404:
            raise HTTPException(404, "Only registered ECWF users can be invited")
        if response.status_code >= 400:
            raise HTTPException(502, "Authentication Service user lookup failed")
        return response.json()

    async def _send_invitation(self, invitation, organization_name: str, token: str):
        preview_url = f"{settings.invitation_preview_url}?token={token}"
        body = f"You have been invited to join {organization_name}. Invitation token: {token}\nPreview: {preview_url}"
        await self._notify(invitation.email, f"Invitation to {organization_name}", body, "organization_invitation")

    async def _notify(self, to: str, subject: str, body: str, template: str):
        if not settings.enable_external_services:
            return
        response = await self.http.post(f"{settings.notification_service_url}/api/v1/notifications/internal/email", headers={"X-Internal-API-Key": settings.internal_api_key}, json={"to": to, "subject": subject, "body": body, "template": template})
        if response.status_code >= 400:
            raise HTTPException(502, "Notification delivery failed")

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or secrets.token_hex(4)
