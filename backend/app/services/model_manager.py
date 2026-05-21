"""
AI Model Manager - Handles downloading, caching, and inference
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
import cv2

from app.core.config import settings
from app.core.model_config import model_config

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages AI model lifecycle and inference"""
    
    def __init__(self):
        self.device = settings.GPU_DEVICE if torch.cuda.is_available() else "cpu"
        self.models: Dict[str, Any] = {}
        self._loaded = False
        
    def load_models(self):
        """Load all AI models into VRAM"""
        if self._loaded:
            logger.info("Models already loaded")
            return
            
        logger.info(f"Loading AI models on {self.device}...")
        
        try:
            # 1. Background Removal (BiRefNet Lite)
            self._load_background_removal()
            
            # 2. Depth Estimation (Depth-Anything-V2)
            self._load_depth_estimation()
            
            # 3. CLIP for embeddings
            self._load_clip()
            
            self._loaded = True
            logger.info("✅ All AI models loaded successfully!")
            
            # Log VRAM usage
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated() / 1024**3
                reserved = torch.cuda.memory_reserved() / 1024**3
                logger.info(f"GPU Memory: {allocated:.2f}GB allocated, {reserved:.2f}GB reserved")
                
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise
    
    def _load_background_removal(self):
        """Load background removal model"""
        try:
            import rembg
            from rembg import new_session
            
            logger.info("Downloading/Loading BiRefNet Lite...")
            self.models['bg_removal'] = new_session("birefnet_lite")
            logger.info("Background removal model ready")
        except Exception as e:
            logger.warning(f"Failed to load background removal: {e}")
            self.models['bg_removal'] = None
    
    def _load_depth_estimation(self):
        """Load depth estimation model"""
        try:
            cache_path = model_config.CACHE_DIR / "depth_anything_v2_small.pth"
            
            if cache_path.exists():
                logger.info("Loading cached depth model...")
                model = torch.hub.load(
                    'LiheYoung/Depth-Anything-V2',
                    'DepthAnythingV2Small',
                    pretrained=False,
                    trust_repo=True
                )
                model.load_state_dict(torch.load(cache_path, map_location=self.device))
            else:
                logger.info("Downloading Depth-Anything-V2 Small...")
                model = torch.hub.load(
                    'LiheYoung/Depth-Anything-V2',
                    'DepthAnythingV2Small',
                    pretrained=True,
                    trust_repo=True
                )
                torch.save(model.state_dict(), cache_path)
                logger.info(f"Model cached at {cache_path}")
            
            model.to(self.device)
            model.eval()
            self.models['depth'] = model
            logger.info("Depth estimation model ready")
            
        except Exception as e:
            logger.warning(f"Failed to load depth model: {e}")
            self.models['depth'] = None
    
    def _load_clip(self):
        """Load CLIP model"""
        try:
            from transformers import CLIPModel, CLIPProcessor
            
            cache_path = model_config.CACHE_DIR / "clip_model"
            
            if cache_path.exists():
                logger.info("Loading cached CLIP model...")
                self.models['clip'] = CLIPModel.from_pretrained(str(cache_path))
                self.models['clip_processor'] = CLIPProcessor.from_pretrained(str(cache_path))
            else:
                logger.info("Downloading CLIP ViT-B/32...")
                self.models['clip'] = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                self.models['clip_processor'] = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                
                # Cache the model
                self.models['clip'].save_pretrained(str(cache_path))
                self.models['clip_processor'].save_pretrained(str(cache_path))
                logger.info(f"Model cached at {cache_path}")
            
            self.models['clip'].to(self.device)
            self.models['clip'].eval()
            logger.info("CLIP model ready")
            
        except Exception as e:
            logger.warning(f"Failed to load CLIP: {e}")
            self.models['clip'] = None
            self.models['clip_processor'] = None
    
    def remove_background(self, image: Image.Image) -> tuple:
        """Remove background from artwork"""
        if not self.models.get('bg_removal'):
            raise RuntimeError("Background removal model not loaded")
        
        import rembg
        
        # Remove background
        result = rembg.remove(image, session=self.models['bg_removal'])
        
        # Get mask
        mask = rembg.remove(image, session=self.models['bg_removal'], only_mask=True)
        
        return result, mask
    
    def estimate_depth(self, image: np.ndarray) -> np.ndarray:
        """Estimate depth map from image"""
        if not self.models.get('depth'):
            raise RuntimeError("Depth model not loaded")
        
        # Prepare image (Depth-Anything expects 518x518)
        h, w = image.shape[:2]
        image_resized = cv2.resize(image, (518, 518))
        image_tensor = torch.from_numpy(image_resized).permute(2, 0, 1).unsqueeze(0).float() / 255.0
        
        with torch.no_grad():
            depth = self.models['depth'](image_tensor.to(self.device))
            depth = F.interpolate(
                depth.unsqueeze(1), 
                size=(h, w), 
                mode='bilinear', 
                align_corners=False
            )
            depth = depth.squeeze().cpu().numpy()
        
        return depth
    
    def extract_embedding(self, image: Image.Image) -> np.ndarray:
        """Extract CLIP embedding for similarity search"""
        if not self.models.get('clip'):
            logger.warning("CLIP not available, returning zero embedding")
            return np.zeros(512)
        
        inputs = self.models['clip_processor'](images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            image_features = self.models['clip'].get_image_features(**inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        return image_features.cpu().numpy()[0]
    
    def extract_color_palette(self, image: Image.Image, n_colors: int = 5) -> list:
        """Extract dominant colors from artwork"""
        from sklearn.cluster import KMeans
        
        # Resize for faster processing
        img = image.resize((150, 150))
        pixels = np.array(img).reshape(-1, 3)
        
        # K-means clustering
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        # Get colors
        colors = kmeans.cluster_centers_.astype(int)
        
        # Convert to hex
        hex_colors = ['#{:02x}{:02x}{:02x}'.format(r, g, b) for r, g, b in colors]
        
        return hex_colors
    
    def is_loaded(self) -> bool:
        """Check if models are loaded"""
        return self._loaded
    
    def unload_models(self):
        """Free up VRAM by unloading models"""
        self.models.clear()
        self._loaded = False
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Models unloaded from memory")

# Global model manager instance
model_manager = ModelManager()