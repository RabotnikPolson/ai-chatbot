from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from db.models import User, FAQItem, RoleEnum
from schemas.faq import FAQCreate, FAQResponse
from api.auth import get_db
from api.conversations import get_current_user_id

router = APIRouter(prefix="/admin/faq", tags=["admin-faq"])


def get_current_admin(
        user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Denied, only for admin")
    return user

@router.post("/", response_model=FAQResponse)
def create_faq(
        faq_data: FAQCreate,
        db: Session = Depends(get_db),
        admin: User = Depends(get_current_admin)
):
    new_faq = FAQItem(title=faq_data.title, content=faq_data.content)
    db.add(new_faq)
    db.commit()
    db.refresh(new_faq)
    return new_faq

@router.get("/", response_model=List[FAQResponse])
def get_faqs(
        db: Session = Depends(get_db),
        admin: User = Depends(get_current_admin)
):
    return db.query(FAQItem).all()


@router.delete("/{id}")
def delete_faq(
        id: int,
        db: Session = Depends(get_db),
        admin: User = Depends(get_current_admin)
):
    # Ищем FAQ
    d_faq = db.query(FAQItem).filter(FAQItem.id == id).first()

    if not d_faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    db.delete(d_faq)
    db.commit()

    return {"message": "FAQ deleted."}