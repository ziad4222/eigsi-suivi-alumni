import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request, Response
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import AuthSession, Role, User

# A configured key keeps sessions valid across restarts. Otherwise sessions are local/ephemeral.
SIGNING_KEY = settings.secret_key or secrets.token_urlsafe(48)
COOKIE = "alumni_session"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, salt, digest = stored.split("$")
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
        return hmac.compare_digest(actual.hex(), digest)
    except (ValueError, TypeError):
        return False


def issue_session(user: User, db: Session, response: Response):
    now = datetime.now(UTC)
    expiry = now + timedelta(minutes=settings.access_token_expire_minutes)
    session_id = secrets.token_hex(32)
    db.add(AuthSession(id=session_id, user_id=user.id, expires_at=expiry.replace(tzinfo=None)))
    db.commit()
    token = jwt.encode(
        {"sub": user.id, "jti": session_id, "iat": now, "exp": expiry, "iss": "eigsi-alumni"},
        SIGNING_KEY,
        algorithm="HS256",
    )
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.access_token_expire_minutes * 60,
        path="/api",
    )


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    try:
        claims = jwt.decode(
            request.cookies.get(COOKIE, ""),
            SIGNING_KEY,
            algorithms=["HS256"],
            issuer="eigsi-alumni",
            options={"require_exp": True, "require_sub": True, "require_jti": True},
        )
        session = db.get(AuthSession, claims["jti"])
        if (
            not session
            or session.user_id != claims["sub"]
            or session.expires_at < datetime.now(UTC).replace(tzinfo=None)
        ):
            raise ValueError("Session expirée")
        user = db.get(User, claims["sub"])
        if not user:
            raise ValueError("Utilisateur absent")
        request.state.session_id = session.id
        return user
    except (JWTError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(401, "Connexion requise") from exc


def require_roles(*allowed: Role):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(403, "Accès refusé")
        return user

    return dependency
