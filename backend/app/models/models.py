# app/models/models.py
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime, 
    ForeignKey, Table, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from app.core.database import Base
import datetime


# ------------------------------
# User Model
# ------------------------------
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    profile_image_url = Column(String, nullable=True)
    is_artist = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    artworks = relationship("Artwork", back_populates="artist", cascade="all, delete-orphan")
    collections = relationship("Collection", back_populates="user", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    saves = relationship("Save", back_populates="user", cascade="all, delete-orphan")
    followers = relationship(
        "Follow",
        foreign_keys="Follow.followed_id",
        back_populates="followed",
        cascade="all, delete-orphan"
    )
    following = relationship(
        "Follow",
        foreign_keys="Follow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan"
    )


# ------------------------------
# Artwork Model
# ------------------------------
class Artwork(Base):
    __tablename__ = "artworks"
    
    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic Info
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    story = Column(Text, nullable=True)  # Emotional narrative behind the artwork
    
    # Physical Details
    height_cm = Column(Float, nullable=True)
    width_cm = Column(Float, nullable=True)
    depth_cm = Column(Float, nullable=True)  # For 3D/sculpture pieces
    
    # Commercial Info
    price = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    is_for_sale = Column(Boolean, default=True)
    
    # Art Details
    medium = Column(String, nullable=True)  # e.g., "Oil on Canvas", "Digital"
    frame_available = Column(Boolean, default=False)
    frame_types = Column(JSONB, nullable=True)  # ["black", "white", "wooden"]
    delivery_options = Column(JSONB, nullable=True)  # {"pickup": true, "shipping": true, "international": false}
    
    # Categorization
    tags = Column(ARRAY(String), default=[])
    categories = Column(ARRAY(String), default=[])
    room_style = Column(String, nullable=True)  # "minimalist", "bohemian", "modern"
    color_palette = Column(ARRAY(String), nullable=True)  # Hex codes
    emotional_vibe = Column(String, nullable=True)  # "calm", "energetic", "melancholic"
    
    # Image URLs
    original_images = Column(ARRAY(String), nullable=True)  # S3 keys for original uploads
    thumbnail_url = Column(String, nullable=True)
    glb_url = Column(String, nullable=True)  # S3 key for processed 3D model
    depth_map_url = Column(String, nullable=True)
    mask_url = Column(String, nullable=True)
    
    # Stats
    views = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    saves_count = Column(Integer, default=0)
    purchases_count = Column(Integer, default=0)
    
    # AI-Generated
    ai_caption = Column(Text, nullable=True)
    ai_tags = Column(ARRAY(String), nullable=True)
    estimated_dimensions = Column(JSONB, nullable=True)  # AI-estimated if missing
    
    # Status
    status = Column(String, default="processing")  # "processing", "ready", "failed"
    is_featured = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    artist = relationship("User", back_populates="artworks")
    likes = relationship("Like", back_populates="artwork", cascade="all, delete-orphan")
    saves = relationship("Save", back_populates="artwork", cascade="all, delete-orphan")
    collection_items = relationship("CollectionItem", back_populates="artwork", cascade="all, delete-orphan")


# ------------------------------
# Collection / Moodboard Model
# ------------------------------
class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    cover_image_url = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="collections")
    items = relationship("CollectionItem", back_populates="collection", cascade="all, delete-orphan")


class CollectionItem(Base):
    __tablename__ = "collection_items"
    
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False)
    artwork_id = Column(Integer, ForeignKey("artworks.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    collection = relationship("Collection", back_populates="items")
    artwork = relationship("Artwork", back_populates="collection_items")


# ------------------------------
# Interaction Models (Likes, Saves, Follows)
# ------------------------------
class Like(Base):
    __tablename__ = "likes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    artwork_id = Column(Integer, ForeignKey("artworks.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="likes")
    artwork = relationship("Artwork", back_populates="likes")


class Save(Base):
    __tablename__ = "saves"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    artwork_id = Column(Integer, ForeignKey("artworks.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="saves")
    artwork = relationship("Artwork", back_populates="saves")


class Follow(Base):
    __tablename__ = "follows"
    
    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    followed_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    followed = relationship("User", foreign_keys=[followed_id], back_populates="followers")


# ------------------------------
# Analytics / Views Tracking
# ------------------------------
class ArtworkView(Base):
    __tablename__ = "artwork_views"
    
    id = Column(Integer, primary_key=True, index=True)
    artwork_id = Column(Integer, ForeignKey("artworks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # nullable for anonymous
    viewed_at = Column(DateTime, default=datetime.datetime.utcnow)
    view_duration_seconds = Column(Integer, nullable=True)


# ------------------------------
# Reports / Moderation
# ------------------------------
class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    artwork_id = Column(Integer, ForeignKey("artworks.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # reported user
    reason = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="pending")  # "pending", "resolved", "dismissed"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)