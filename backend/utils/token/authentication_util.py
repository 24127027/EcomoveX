from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import secrets
import string
from datetime import datetime, timedelta

from utils.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    user_data = decode_access_token(token)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return user_data


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        exp: int = payload.get("exp")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )
        if datetime.utcnow().timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
            )
        return {"user_id": int(user_id), "role": role}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or corrupted token",
        )

def generate_temporary_password() -> str:
    try:
        password_length = secrets.randbelow(12) + 8
        
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        symbols = string.punctuation

        password_chars = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(symbols),
        ]

        all_chars = lowercase + uppercase + digits + symbols
        password_chars += [secrets.choice(all_chars) for _ in range(password_length - 4)]

        secrets.SystemRandom().shuffle(password_chars)
        
        return ''.join(password_chars)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating temporary password: {e}",
        )

def generate_verification_token(email: str, username: str, password: str) -> str:
    try:
        expiration = datetime.utcnow() + timedelta(hours=24)
        payload = {
            "email": email,
            "username": username,
            "password": password,
            "exp": expiration,
            "type": "email_verification"
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating verification token: {e}",
        )

def verify_email_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")
        username = payload.get("username")
        password = payload.get("password")
        token_type = payload.get("type")
        
        if token_type != "email_verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )
        
        if not email or not username or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token payload"
            )
        
        return {
            "email": email,
            "username": username,
            "password": password
        }
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )