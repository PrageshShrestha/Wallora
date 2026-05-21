from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .user import UserResponse

class ArtworkCreate(BaseModel):
    title: str
    description: Optional[str] = None
    story: Optional[str] = None
    height_cm: Optional[float] = None
    width_cm: Optional[float] = None
    price: Optional[float] = None
    medium: Optional[str] = None
    frame_available: bool = False
    delivery_options: Optional[dict] = None
    tags: List[str] = []
    categories: List[str] = []
    room_style: Optional[str] = None
    emotional_vibe: Optional[str] = None

class ArtworkResponse(BaseModel):
    id: int
    artist_id: int
    title: str
    description: Optional[str]
    story: Optional[str]
    height_cm: Optional[float]
    width_cm: Optional[float]
    price: Optional[float]
    medium: Optional[str]
    frame_available: bool
    tags: List[str]
    categories: List[str]
    room_style: Optional[str]
    emotional_vibe: Optional[str]
    thumbnail_url: Optional[str]
    glb_url: Optional[str]
    views: int
    likes_count: int
    saves_count: int
    status: str
    is_featured: bool
    created_at: datetime
    artist: UserResponse
    
    class Config:
        from_attributes = True

class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = False

class CollectionResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    is_public: bool
    created_at: datetime
    
    class Config:
        from_attributes = True