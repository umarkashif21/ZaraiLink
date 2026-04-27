"""
AccessService — the single backend authority for token-based paywall logic.

Access States:
    FULL_ACCESS    → User bought HS_CODE-level access (unlocks all products under that HS)
    PRODUCT_ACCESS → User bought access to a specific product/sub-category only
    NO_ACCESS      → Default restricted state (preview only)

Pricing:
    HS_CODE access  → 5,000 tokens
    PRODUCT access  → 500 tokens

Rules:
    - FULL_ACCESS supersedes PRODUCT_ACCESS for the same HS code.
    - PRODUCT_ACCESS does NOT escalate to FULL_ACCESS.
    - Superusers and staff always receive FULL_ACCESS (bypass billing).
    - Anonymous / unauthenticated users → NO_ACCESS.
"""

from typing import Optional, Tuple
from django.db import transaction as db_transaction
from .models import UserAccess

# Token costs — change here if pricing ever changes
HS_CODE_PRICE  = 5000
PRODUCT_PRICE  = 500


# ─── Access States ─────────────────────────────────────────────────────────────
FULL_ACCESS    = 'FULL_ACCESS'
PRODUCT_ACCESS = 'PRODUCT_ACCESS'
NO_ACCESS      = 'NO_ACCESS'


def get_access_state(user, hscode: str, subcat_id: Optional[int] = None) -> str:
    """
    Determine the access state for a given user / HS code / product combination.

    Returns one of:  FULL_ACCESS | PRODUCT_ACCESS | NO_ACCESS
    """
    # Anonymous users always get NO_ACCESS
    if not user or not user.is_authenticated:
        return NO_ACCESS

    # Staff / superusers always get full access (admin bypass)
    if user.is_staff or user.is_superuser:
        return FULL_ACCESS

    grants = UserAccess.objects.filter(user=user, hscode=hscode)

    # 1. Check for full HS_CODE-level access (subcat_id=None)
    if grants.filter(access_type='HS_CODE').exists():
        return FULL_ACCESS

    # 2. If a specific product is being requested, check for PRODUCT access
    if subcat_id:
        if grants.filter(access_type='PRODUCT', subcat_id=subcat_id).exists():
            return PRODUCT_ACCESS

    return NO_ACCESS


def purchase_access(user, access_type: str, hscode: str, subcat_id: Optional[int] = None) -> Tuple[bool, str, Optional[int]]:
    """
    Attempt to purchase access for a user.

    Returns:
        (success: bool, message: str, new_balance: int | None)
    """
    if not user or not user.is_authenticated:
        return False, "Authentication required.", None

    if access_type not in ('HS_CODE', 'PRODUCT'):
        return False, "Invalid access_type. Must be 'HS_CODE' or 'PRODUCT'.", None

    if access_type == 'PRODUCT' and not subcat_id:
        return False, "subcat_id is required for PRODUCT access.", None

    price = HS_CODE_PRICE if access_type == 'HS_CODE' else PRODUCT_PRICE

    # Idempotency — don't charge twice for the same item
    already_exists = UserAccess.objects.filter(
        user=user,
        hscode=hscode,
        subcat_id=subcat_id if access_type == 'PRODUCT' else None,
    ).exists()

    if already_exists:
        return True, "Access already granted.", user.token_balance

    # Check balance
    if user.token_balance < price:
        return False, f"Insufficient tokens. Required: {price}, Available: {user.token_balance}.", None

    # Deduct and persist atomically
    with db_transaction.atomic():
        user.token_balance -= price
        user.save(update_fields=['token_balance'])

        UserAccess.objects.create(
            user=user,
            access_type=access_type,
            hscode=hscode,
            subcat_id=subcat_id if access_type == 'PRODUCT' else None,
            tokens_spent=price,
        )

    return True, "Access granted successfully.", user.token_balance
