"""
AI Artwork Processing Pipeline
Handles: background removal, depth estimation, embedding extraction
"""

import logging
import json
from pathlib import Path
from typing import Optional
from PIL import Image
import numpy as np
import cv2

from app.core.config import settings
from app.services.model_manager import model_manager
from app.services.file_service import FileService

logger = logging.getLogger(__name__)

class ArtworkProcessor:
    """Process artwork images with AI pipeline"""
    
    @staticmethod
    async def process_artwork(artwork, db):
        """Full AI processing pipeline for artwork"""
        try:
            artwork.status = "processing"
            db.commit()
            
            # Load original image
            image_path = FileService.get_file_path(artwork.original_images[0])
            original_image = Image.open(image_path).convert("RGB")
            
            logger.info(f"Processing artwork {artwork.id}: {artwork.title}")
            
            # 1. Remove background
            fg_image, mask = model_manager.remove_background(original_image)
            
            # Save mask
            mask_filename = f"mask_{artwork.id}.png"
            mask_path = settings.UPLOAD_DIR / "masks" / mask_filename
            mask_path.parent.mkdir(exist_ok=True)
            mask.save(str(mask_path))
            artwork.mask_url = f"masks/{mask_filename}"
            
            # 2. Estimate depth
            bgr_image = cv2.cvtColor(np.array(original_image), cv2.COLOR_RGB2BGR)
            depth_map = model_manager.estimate_depth(bgr_image)
            
            # Save depth map
            depth_filename = f"depth_{artwork.id}.npy"
            depth_path = settings.UPLOAD_DIR / "depth_maps" / depth_filename
            depth_path.parent.mkdir(exist_ok=True)
            np.save(str(depth_path), depth_map)
            artwork.depth_map_url = f"depth_maps/{depth_filename}"
            
            # 3. Extract CLIP embedding
            embedding = model_manager.extract_embedding(original_image)
            artwork.clip_embedding = embedding.tolist()  # Store as array
            
            # 4. Extract color palette
            color_palette = model_manager.extract_color_palette(original_image)
            artwork.color_palette = color_palette
            
            # 5. Generate thumbnail
            thumbnail = original_image.copy()
            thumbnail.thumbnail((500, 500), Image.Resampling.LANCZOS)
            thumbnail_filename = f"thumb_{artwork.id}.jpg"
            thumbnail_path = settings.UPLOAD_DIR / "thumbnails" / thumbnail_filename
            thumbnail.save(str(thumbnail_path), "JPEG", quality=85)
            artwork.thumbnail_url = f"thumbnails/{thumbnail_filename}"
            
            # Mark as ready
            artwork.status = "ready"
            db.commit()
            
            logger.info(f"Artwork {artwork.id} processed successfully")
            
        except Exception as e:
            logger.error(f"Failed to process artwork {artwork.id}: {e}")
            artwork.status = "failed"
            db.commit()

# Global processor instance
artwork_processor = ArtworkProcessor()