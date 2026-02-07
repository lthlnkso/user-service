from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.userspace import UserSpace
from app.schemas.userspace import UserSpaceCreate, UserSpaceOut

router = APIRouter(prefix="/userspaces", tags=["userspaces"])


@router.post("", response_model=UserSpaceOut, status_code=status.HTTP_201_CREATED)
async def create_userspace(payload: UserSpaceCreate, db: Session = Depends(get_db)):
    existing = db.query(UserSpace).filter(UserSpace.namespace == payload.namespace).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Namespace already exists")

    userspace = UserSpace(namespace=payload.namespace, name=payload.name, description=payload.description)
    db.add(userspace)
    db.commit()
    db.refresh(userspace)
    return userspace
