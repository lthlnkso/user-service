from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.services.security import hash_password, verify_password


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(
        namespace=payload.namespace,
        username=payload.username,
        password_hash=hash_password(payload.password),
        email=payload.email,
        full_name=payload.full_name,
        avatar_url=payload.avatar_url,
        extra=payload.extra,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, namespace: str, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.namespace == namespace, User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
