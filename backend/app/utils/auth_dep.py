# Auth skipped for V1 — single default user, no login required.
# Will be restored in V2 with JWT + multi-user support.

DEFAULT_USER_ID = "default-user-v1"


def get_current_user_id() -> str:
    return DEFAULT_USER_ID
