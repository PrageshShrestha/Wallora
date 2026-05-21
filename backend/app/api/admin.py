from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.models import User, Artwork, Like

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/stats")
async def get_stats(
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get platform statistics"""
    
    total_users = db.query(func.count(User.id)).scalar()
    total_artworks = db.query(func.count(Artwork.id)).scalar()
    total_artists = db.query(func.count(User.id)).filter(User.is_artist == True).scalar()
    total_likes = db.query(func.count(Like.id)).scalar()
    
    top_categories = (
        db.query(
            func.unnest(Artwork.categories).label('category'),
            func.count().label('count')
        )
        .group_by('category')
        .order_by(desc('count'))
        .limit(10)
        .all()
    )
    
    return {
        "total_users": total_users,
        "total_artworks": total_artworks,
        "total_artists": total_artists,
        "total_likes": total_likes,
        "top_categories": [{"name": cat, "count": count} for cat, count in top_categories]
    }

@router.put("/artworks/{artwork_id}/feature")
async def toggle_feature(
    artwork_id: int,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Toggle artwork featured status"""
    
    artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    
    artwork.is_featured = not artwork.is_featured
    db.commit()
    
    return {"is_featured": artwork.is_featured}

@router.delete("/artworks/{artwork_id}")
async def delete_artwork(
    artwork_id: int,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin delete artwork"""
    
    artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    
    db.delete(artwork)
    db.commit()
    return {"message": "Artwork deleted"}