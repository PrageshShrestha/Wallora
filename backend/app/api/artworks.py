import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_artist
from app.models.models import Artwork, Like, Collection, CollectionItem
from app.schemas.artwork import ArtworkCreate, ArtworkResponse
from app.services.file_service import FileService

router = APIRouter(prefix="/artworks", tags=["Artworks"])

@router.post("/", response_model=ArtworkResponse, status_code=201)
async def create_artwork(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    story: Optional[str] = Form(None),
    height_cm: Optional[float] = Form(None),
    width_cm: Optional[float] = Form(None),
    price: Optional[float] = Form(None),
    medium: Optional[str] = Form(None),
    frame_available: bool = Form(False),
    tags: Optional[str] = Form("[]"),
    categories: Optional[str] = Form("[]"),
    room_style: Optional[str] = Form(None),
    emotional_vibe: Optional[str] = Form(None),
    images: List[UploadFile] = File(...),
    current_user = Depends(get_current_artist),
    db: Session = Depends(get_db)
):
    """Upload new artwork"""
    
    tags_list = json.loads(tags) if tags else []
    categories_list = json.loads(categories) if categories else []
    
    # Save images
    saved_files = await FileService.save_upload_images(images)
    
    # Create artwork
    artwork = Artwork(
        artist_id=current_user.id,
        title=title,
        description=description,
        story=story,
        height_cm=height_cm,
        width_cm=width_cm,
        price=price,
        medium=medium,
        frame_available=frame_available,
        tags=tags_list,
        categories=categories_list,
        room_style=room_style,
        emotional_vibe=emotional_vibe,
        original_images=saved_files,
        thumbnail_url=saved_files[0] if saved_files else None,
        status="ready"
    )
    
    db.add(artwork)
    db.commit()
    db.refresh(artwork)
    return artwork

@router.get("/", response_model=List[ArtworkResponse])
async def get_artworks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    room_style: Optional[str] = None,
    emotional_vibe: Optional[str] = None,
    artist_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get artworks with filters"""
    
    query = db.query(Artwork).filter(Artwork.is_public == True, Artwork.status == "ready")
    
    if category:
        query = query.filter(Artwork.categories.contains([category]))
    if room_style:
        query = query.filter(Artwork.room_style == room_style)
    if emotional_vibe:
        query = query.filter(Artwork.emotional_vibe == emotional_vibe)
    if artist_id:
        query = query.filter(Artwork.artist_id == artist_id)
    
    artworks = (
        query
        .options(joinedload(Artwork.artist))
        .order_by(desc(Artwork.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return artworks

@router.get("/swipe", response_model=List[ArtworkResponse])
async def get_swipe_artworks(
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get artworks for swipe feed"""
    
    liked_ids = [like.artwork_id for like in db.query(Like.artwork_id).filter(Like.user_id == current_user.id).all()]
    
    artworks = (
        db.query(Artwork)
        .filter(
            Artwork.is_public == True,
            Artwork.status == "ready",
            Artwork.id.notin_(liked_ids) if liked_ids else True,
            Artwork.artist_id != current_user.id
        )
        .options(joinedload(Artwork.artist))
        .order_by(func.random())
        .limit(limit)
        .all()
    )
    
    return artworks

@router.get("/{artwork_id}", response_model=ArtworkResponse)
async def get_artwork(artwork_id: int, db: Session = Depends(get_db)):
    """Get artwork by ID"""
    
    artwork = (
        db.query(Artwork)
        .options(joinedload(Artwork.artist))
        .filter(Artwork.id == artwork_id)
        .first()
    )
    
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    
    artwork.views += 1
    db.commit()
    return artwork

@router.post("/{artwork_id}/like")
async def like_artwork(
    artwork_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Like/unlike artwork"""
    
    artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    
    existing_like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.artwork_id == artwork_id
    ).first()
    
    if existing_like:
        db.delete(existing_like)
        artwork.likes_count -= 1
        db.commit()
        return {"liked": False}
    else:
        like = Like(user_id=current_user.id, artwork_id=artwork_id)
        db.add(like)
        artwork.likes_count += 1
        db.commit()
        return {"liked": True}

@router.post("/{artwork_id}/save")
async def save_artwork(
    artwork_id: int,
    collection_id: Optional[int] = Form(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save artwork to collection"""
    
    artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    
    # Get or create default collection
    if not collection_id:
        default_collection = db.query(Collection).filter(
            Collection.user_id == current_user.id,
            Collection.name == "Saved"
        ).first()
        
        if not default_collection:
            default_collection = Collection(user_id=current_user.id, name="Saved")
            db.add(default_collection)
            db.commit()
            db.refresh(default_collection)
        
        collection_id = default_collection.id
    
    # Toggle save
    existing_item = db.query(CollectionItem).filter(
        CollectionItem.collection_id == collection_id,
        CollectionItem.artwork_id == artwork_id
    ).first()
    
    if existing_item:
        db.delete(existing_item)
        artwork.saves_count -= 1
        db.commit()
        return {"saved": False}
    else:
        item = CollectionItem(collection_id=collection_id, artwork_id=artwork_id)
        db.add(item)
        artwork.saves_count += 1
        db.commit()
        return {"saved": True}