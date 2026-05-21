import uuid
import numpy as np
from pathlib import Path
from typing import List
from fastapi import UploadFile
from PIL import Image
import trimesh
from app.core.config import settings

class FileService:
    @staticmethod
    async def save_upload_images(images: List[UploadFile]) -> List[str]:
        """Save uploaded images and return relative paths"""
        saved_files = []
        
        for image in images:
            file_extension = Path(image.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = settings.ORIGINALS_DIR / unique_filename
            
            with open(file_path, "wb") as buffer:
                content = await image.read()
                buffer.write(content)
            
            relative_path = str(file_path.relative_to(settings.UPLOAD_DIR))
            saved_files.append(relative_path)
        
        return saved_files
    
    @staticmethod
    def get_file_path(relative_path: str) -> Path:
        """Get full file path from relative path"""
        return settings.UPLOAD_DIR / relative_path
    
    @staticmethod
    def generate_glb_model(
        artwork_image_path: Path,
        mask_path: Path,
        depth_map: np.ndarray,
        width_cm: float,
        height_cm: float,
        artwork_id: int
    ) -> str:
        """Generate GLB 3D model for AR preview"""
        
        # Load textures
        rgba_image = Image.open(artwork_image_path).convert("RGBA")
        tex = np.array(rgba_image)
        
        # Convert cm to meters
        w = width_cm / 100.0 if width_cm else 0.6  # default 60cm
        h = height_cm / 100.0 if height_cm else 0.9  # default 90cm
        frame_thickness = 0.02
        frame_depth = 0.015
        
        # Create painting plane
        painting_verts = np.array([
            [-w/2, -h/2, 0],
            [w/2, -h/2, 0],
            [w/2, h/2, 0],
            [-w/2, h/2, 0],
        ], dtype=np.float32)
        
        painting_faces = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.uint32)
        painting_uvs = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)
        
        # Create mesh
        painting_mesh = trimesh.Trimesh(
            vertices=painting_verts,
            faces=painting_faces,
            process=False
        )
        
        # Apply texture
        painting_mesh.visual = trimesh.visual.texture.TextureVisuals(
            uv=painting_uvs,
            image=tex
        )
        
        # Save GLB
        glb_filename = f"model_{artwork_id}.glb"
        glb_path = settings.UPLOAD_DIR / "glb_models" / glb_filename
        glb_path.parent.mkdir(exist_ok=True)
        
        scene = trimesh.Scene()
        scene.add_geometry(painting_mesh, node_name="painting")
        scene.export(str(glb_path), file_type='glb')
        
        return f"glb_models/{glb_filename}"