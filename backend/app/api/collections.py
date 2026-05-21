from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import Collection, CollectionItem, Artwork
from app.schemas.artwork import CollectionCreate, CollectionResponse, ArtworkResponse

router = APIRouter(prefix="/collections", tags=["Collections"])

@router.post("/", response_model=CollectionResponse, status_code=201)
async def create_collection(
    collection_data: CollectionCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new collection/moodboard"""
    
    collection = Collection(
        user_id=current_user.id,
        **collection_data.model_dump()
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection

@router.get("/", response_model=List[CollectionResponse])
async def get_collections(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's collections"""
    return db.query(Collection).filter(Collection.user_id == current_user.id).all()

@router.get("/{collection_id}/artworks", response_model=List[ArtworkResponse])
async def get_collection_artworks(
    collection_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get artworks in a collection"""
    
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id
    ).first()
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    artworks = (
        db.query(Artwork)
        .join(CollectionItem)
        .options(joinedload(Artwork.artist))
        .filter(CollectionItem.collection_id == collection_id)
        .all()
    )
    
    return artworks