from fastapi import Depends, HTTPException, status

from models.user import User
from utils.token.authentication_util import get_current_user


async def require_roles(allowed_roles: list[str]):
    async def inner(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission"
            )
        return user

    return inner
