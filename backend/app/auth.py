import jwt as pyjwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from app.settings import get_nextauth_secret

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer = HTTPBearer()


def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def decode_service_token(token: str) -> dict:
    """Verify HS256 JWT signed with NEXTAUTH_SECRET. Raises PyJWTError on failure."""
    secret = get_nextauth_secret()
    return pyjwt.decode(token, secret, algorithms=["HS256"], options={"require": ["exp"]})


def require_role(*roles: str):
    """FastAPI dependency factory. Usage: Depends(require_role('admin', 'staff'))"""
    def _check(credentials: HTTPAuthorizationCredentials = Security(_bearer)) -> dict:
        try:
            payload = decode_service_token(credentials.credentials)
        except pyjwt.PyJWTError as exc:
            raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
        if payload.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return payload
    return _check
