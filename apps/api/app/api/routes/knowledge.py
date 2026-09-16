import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlalchemy import select, or_

from app.core.deps import CurrentUser, DbSession, require_role, is_staff
from app.models.enums import UserRole
from app.models.knowledge_article import KnowledgeArticle
from app.models.user import User
from app.schemas.knowledge_article import KnowledgeArticleCreate, KnowledgeArticleOut

router = APIRouter(prefix="/knowledge-articles", tags=["knowledge"])

StaffUser = Annotated[User, Depends(require_role(UserRole.technician, UserRole.admin))]


@router.get("", response_model=list[KnowledgeArticleOut])
async def list_articles(user: CurrentUser, db: DbSession):
    stmt = select(KnowledgeArticle).order_by(KnowledgeArticle.title)
    if not is_staff(user):
        stmt = stmt.where(or_(KnowledgeArticle.client_id.is_(None), KnowledgeArticle.client_id == user.client_id))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=KnowledgeArticleOut, status_code=status.HTTP_201_CREATED)
async def create_article(payload: KnowledgeArticleCreate, user: StaffUser, db: DbSession):
    article = KnowledgeArticle(
        client_id=payload.client_id,
        title=payload.title,
        body=payload.body,
        category=payload.category,
        created_by_user_id=user.id,
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return article
