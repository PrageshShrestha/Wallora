from pathlib import Path
from app.core.config import settings

class ModelConfig:
    # Model cache directory
    CACHE_DIR: Path = settings.BASE_DIR.parent / "models_cache"
    
    # Models to download
    MODELS = {
        "birefnet_lite": {
            "type": "rembg",
            "model_name": "birefnet_lite",
            "size_mb": 50,
            "description": "Background removal"
        },
        "depth_anything_v2_small": {
            "type": "torch_hub",
            "repo": "LiheYoung/Depth-Anything-V2",
            "model_name": "DepthAnythingV2Small",
            "size_mb": 100,
            "description": "Depth estimation"
        },
        "clip_vit_base": {
            "type": "transformers",
            "model_name": "openai/clip-vit-base-patch32",
            "size_mb": 600,
            "description": "Visual embeddings & similarity"
        }
    }
    
    # Create cache directory
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

model_config = ModelConfig()