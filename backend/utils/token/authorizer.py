from fastapi import Depends, HTTPException, status

from utils.token.authentication_util import get_current_user


def require_roles(allowed_roles: list[str]):
    async def inner(user: dict = Depends(get_current_user)):
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission",
            )
        return user

    return inner
