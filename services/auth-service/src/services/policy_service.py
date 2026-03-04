"""
ABAC policy evaluation engine.

Usage:
    svc = PolicyService(db_session)
    allowed = await svc.is_allowed(
        user_id=uuid.UUID("..."),
        user_roles=["analyst"],
        action="read",
        resource="sample",
        context={"owner_id": uuid.UUID("...")},  # for ownership checks
    )
"""
import uuid

import structlog
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.policy import Policy

logger = structlog.get_logger()


class PolicyService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_applicable_policies(
        self,
        user_id: uuid.UUID,
        user_roles: list[str],
        action: str,
        resource: str,
    ) -> list[Policy]:
        """Retrieve all active policies that apply to this subject + resource + action."""
        user_id_str = str(user_id)
        role_filters = [
            (Policy.subject_type == "role") & (Policy.subject_id == role)
            for role in user_roles
        ]
        role_filters.append(
            (Policy.subject_type == "role") & (Policy.subject_id == "*")
        )

        stmt = (
            select(Policy)
            .where(
                Policy.is_active == True,
                Policy.resource.in_([resource, "*"]),
                Policy.action.in_([action, "*"]),
                or_(
                    (Policy.subject_type == "user") & (Policy.subject_id == user_id_str),
                    (Policy.subject_type == "user") & (Policy.subject_id == "*"),
                    *role_filters,
                ),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def _evaluate_conditions(
        self,
        policy: Policy,
        user_id: uuid.UUID,
        context: dict,
    ) -> bool:
        """
        Evaluate optional conditions on a policy.
        Returns True if conditions pass (or no conditions).
        """
        conditions = policy.conditions or {}

        if conditions.get("owner"):
            owner_id = context.get("owner_id")
            if owner_id is None:
                return False
            if isinstance(owner_id, str):
                owner_id = uuid.UUID(owner_id)
            if owner_id != user_id:
                return False

        return True

    async def is_allowed(
        self,
        user_id: uuid.UUID,
        user_roles: list[str],
        action: str,
        resource: str,
        context: dict | None = None,
    ) -> bool:
        """
        Evaluate whether the given user is allowed to perform `action` on `resource`.

        Deny policies take precedence over allow policies.
        Returns False if no matching allow policy exists.
        """
        context = context or {}
        policies = await self.get_applicable_policies(user_id, user_roles, action, resource)

        # Check for explicit denies first
        for policy in policies:
            if policy.effect == "deny" and self._evaluate_conditions(policy, user_id, context):
                logger.info(
                    "policy.deny",
                    user_id=str(user_id),
                    action=action,
                    resource=resource,
                    policy_id=str(policy.id),
                )
                return False

        # Then check for explicit allows
        for policy in policies:
            if policy.effect == "allow" and self._evaluate_conditions(policy, user_id, context):
                return True

        logger.debug(
            "policy.no_allow_found",
            user_id=str(user_id),
            action=action,
            resource=resource,
        )
        return False

    # ------------------------------------------------------------------
    # CRUD helpers for policy management
    # ------------------------------------------------------------------

    async def create_policy(
        self,
        subject_type: str,
        subject_id: str,
        resource: str,
        action: str,
        effect: str = "allow",
        conditions: dict | None = None,
    ) -> Policy:
        policy = Policy(
            subject_type=subject_type,
            subject_id=subject_id,
            resource=resource,
            action=action,
            effect=effect,
            conditions=conditions,
        )
        self.session.add(policy)
        await self.session.flush()
        logger.info("policy.created", policy_id=str(policy.id))
        return policy

    async def delete_policy(self, policy_id: uuid.UUID) -> bool:
        stmt = select(Policy).where(Policy.id == policy_id)
        result = await self.session.execute(stmt)
        policy = result.scalar_one_or_none()
        if policy is None:
            return False
        await self.session.delete(policy)
        await self.session.flush()
        return True

    async def list_policies(
        self,
        subject_type: str | None = None,
        resource: str | None = None,
    ) -> list[Policy]:
        stmt = select(Policy).where(Policy.is_active == True)
        if subject_type:
            stmt = stmt.where(Policy.subject_type == subject_type)
        if resource:
            stmt = stmt.where(Policy.resource == resource)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
