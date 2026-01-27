from fastapi import Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.models import User

def admin_only(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to allow only admins.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access only"
        )
    return current_user
