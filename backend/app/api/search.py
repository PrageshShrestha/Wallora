from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_

from app.core.database import get_db
from app.models.models import Artwork
from app.schemas.artwork import ArtworkResponse

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/", response_model=List[ArtworkResponse])
async def search_artworks(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = None,
    room_style: Optional[str] = None,
    emotional_vibe: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    medium: Optional[str] = None,
    color: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Advanced search for artworks"""
    
    query = db.query(Artwork).filter(Artwork.is_public == True, Artwork.status == "ready")
    
    # Text search
    if q:
        search_filter = or_(
            Artwork.title.ilike(f"%{q}%"),
            Artwork.description.ilike(f"%{q}%"),
            Artwork.story.ilike(f"%{q}%"),
            Artwork.medium.ilike(f"%{q}%")
        )
        query = query.filter(search_filter)
    
    # Filters
    if category:
        query = query.filter(Artwork.categories.contains([category]))
    if room_style:
        query = query.filter(Artwork.room_style == room_style)
    if emotional_vibe:
        query = query.filter(Artwork.emotional_vibe == emotional_vibe)
    if medium:
        query = query.filter(Artwork.medium == medium)
    if min_price is not None:
        query = query.filter(Artwork.price >= min_price)
    if max_price is not None:
        query = query.filter(Artwork.price <= max_price)
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        for tag in tag_list:
            query = query.filter(Artwork.tags.contains([tag]))
    if color:
        query = query.filter(Artwork.color_palette.contains([color]))
    
    artworks = (
        query
        .options(joinedload(Artwork.artist))
        .order_by(desc(Artwork.likes_count))
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return artworks