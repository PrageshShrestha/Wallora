# Wallora - AI-Powered Art Discovery Platform

## Overview

Wallora is a production-ready backend system for an art discovery and marketplace platform. It combines AI-powered image processing, 3D model generation for AR previews, and a complete REST API for frontend applications (Flutter, React Native, etc.).

The system processes uploaded artwork through a GPU-accelerated pipeline that removes backgrounds, estimates depth, generates CLIP embeddings for similarity search, and creates lightweight GLB 3D models suitable for AR placement on mobile devices.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Web Framework | FastAPI (Python 3.10+) |
| Database | PostgreSQL 14+ |
| ORM | SQLAlchemy 2.0+ |
| Authentication | JWT with bcrypt hashing |
| Task Queue | BackgroundTasks (built into FastAPI) |
| AI/ML | PyTorch, Transformers, OpenCV, rembg |
| Vision Models | Depth-Anything-V2, CLIP, BiRefNet Lite |
| File Storage | Local filesystem (pluggable for S3) |
| Caching | Redis (optional, fallback to memory) |

## AI Model Pipeline

When an artist uploads artwork, the system performs the following operations asynchronously:

1. **Background Removal**: Uses BiRefNet Lite to isolate artwork from its background
2. **Depth Estimation**: Depth-Anything-V2 generates a depth map for pseudo-3D effects
3. **CLIP Embedding**: Generates vector embeddings for visual similarity search
4. **GLB Generation**: Creates a lightweight 3D model with frame extrusion and texture mapping
5. **Dimension Estimation**: AI-predicted dimensions when artist omits them
6. **Aesthetic Metadata**: Color palette extraction, mood classification, tag generation

All models are downloaded once and cached locally. No external API calls are made - everything runs on your own GPU/CPU.

## System Requirements

### Hardware
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: NVIDIA GPU with 6GB+ VRAM (optional, falls back to CPU)
- **Storage**: 20GB for models + variable for uploaded artwork

### Software
- **Operating System**: Linux (Ubuntu 20.04+), macOS 12+, or Windows WSL2
- **Python**: 3.10 or 3.11
- **PostgreSQL**: 14 or higher
- **Redis** (optional): For enhanced caching and future Celery integration

## Installation

### 1. Clone and Setup Environment

```bash
git clone https://github.com/your-org/wallora.git
cd wallora
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Requirements file content (`requirements.txt`):
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0
pillow==10.1.0
numpy==1.24.3
opencv-python==4.8.1.78
torch==2.1.0
torchvision==0.16.0
transformers==4.35.0
rembg==2.0.50
boto3==1.34.0
redis==5.0.1
```

### 3. Setup PostgreSQL Database

```sql
CREATE DATABASE wallora;
CREATE USER wallora WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE wallora TO wallora;
```

### 4. Configure Environment Variables

Create `.env` file in the project root:

```env
# Database
DB_USER=wallora
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=wallora

# JWT Authentication
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Server
BASE_URL=http://localhost:8000
DEBUG=False

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# For ngrok deployment
# BASE_URL=https://your-ngrok-subdomain.ngrok.io
```

### 5. Run Database Migrations

```bash
python -c "from main import init_db; init_db()"
```

### 6. Start the Server

```bash
# Development mode with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The server will automatically:
- Create all necessary directories (uploads/, models_cache/, etc.)
- Download AI models on first startup (approximately 3-5 minutes depending on connection)
- Initialize database tables

## API Documentation

Once running, interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Authentication Flow

All protected endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

**Token Refresh Flow:**
1. Client authenticates with `/auth/login` (receives access_token + refresh_token)
2. Use access_token for normal API calls
3. When access_token expires, call `/auth/refresh` with refresh_token
4. Receive new access_token

### Core Endpoints

#### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create new user account |
| POST | `/auth/login` | Login with email/password |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user info |

#### Artwork Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/artworks/` | Upload new artwork (multipart form) |
| GET | `/artworks/` | List artworks with pagination and filters |
| GET | `/artworks/{id}` | Get artwork details |
| PUT | `/artworks/{id}` | Update artwork metadata |
| DELETE | `/artworks/{id}` | Delete artwork |
| GET | `/artworks/swipe/next` | Get next artwork for discovery feed |
| POST | `/artworks/{id}/like` | Like/unlike artwork |
| POST | `/artworks/{id}/view` | Record artwork view |

#### Discovery & Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/search/` | Search by text, tags, color, style |
| GET | `/search/similar/{id}` | Find visually similar artworks |
| GET | `/recommendations/` | Personalized recommendations |

#### User Features
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/{id}/artworks` | Get artist's portfolio |
| GET | `/users/me/likes` | Get user's liked artworks |
| GET | `/users/me/saved` | Get saved artworks |

#### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/analytics/` | Platform statistics |
| PUT | `/admin/artworks/{id}/feature` | Feature/unfeature artwork |
| DELETE | `/admin/artworks/{id}` | Admin artwork deletion |

### Request/Response Examples

**Register User:**
```json
POST /auth/register
{
  "email": "artist@example.com",
  "username": "artista",
  "password": "securepassword",
  "full_name": "Artist Name",
  "is_artist": true
}
```

**Upload Artwork:**
```
POST /artworks/
Content-Type: multipart/form-data

- file: [image file]
- title: "Starry Night Over Paris"
- description: "A modern interpretation..."
- price: 450.00
- medium: "Oil on Canvas"
- tags: ["landscape", "impressionist"]
- height_cm: 60
- width_cm: 80
```

**Response:**
```json
{
  "id": 42,
  "title": "Starry Night Over Paris",
  "artist_id": 7,
  "artist_name": "artista",
  "status": "processing",
  "thumbnail_url": "/uploads/thumbnails/uuid_thumb.jpg",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## AI Processing Pipeline

### Model Caching Behavior

On first startup, models are automatically downloaded to `./models_cache/`:

| Model | Size | Download Source |
|-------|------|-----------------|
| BiRefNet Lite | 120MB | Internal (rembg) |
| Depth-Anything-V2-Small | 350MB | PyTorch Hub |
| CLIP ViT-B/32 | 610MB | HuggingFace |

After initial download, subsequent starts load models from cache (5-10 seconds total).

### Processing Queue

Artwork uploads are processed asynchronously. Check artwork status via GET `/artworks/{id}`:

- `processing`: AI pipeline running
- `ready`: All processing complete, GLB available
- `failed`: Processing error occurred

Typical processing time per image:
- CPU-only: 15-30 seconds
- GPU (6GB+ VRAM): 3-5 seconds

### GLB Model Output

The generated GLB file contains:
- Textured plane with artwork image
- Extruded frame matching artwork dimensions
- PBR materials for realistic lighting
- Scale calibrated to real-world centimeters

File size: 500KB - 2MB depending on texture resolution.

## Deployment Guide

### Local Development

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production with Gunicorn

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Ngrok Tunnel (Desktop Server)

For exposing your local server to the internet:

1. Install ngrok: https://ngrok.com/download
2. Run ngrok tunnel:
```bash
ngrok http 8000
```
3. Copy the HTTPS forwarding URL (e.g., `https://abc123.ngrok.io`)
4. Update `BASE_URL` in your .env file and restart the server

### Systemd Service (Linux)

Create `/etc/systemd/system/wallora.service`:

```ini
[Unit]
Description=Wallora API Server
After=network.target postgresql.service

[Service]
User=youruser
WorkingDirectory=/path/to/wallora
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## Database Schema

### Core Tables

**users**
- id (PK), email, username, hashed_password, full_name
- bio, profile_image, is_artist, is_admin
- created_at, updated_at

**artworks**
- id (PK), artist_id (FK -> users)
- title, description, story
- height_cm, width_cm, depth_cm
- price, currency, is_for_sale
- medium, tags (ARRAY), categories (ARRAY)
- room_style, color_palette (ARRAY), emotional_vibe
- original_images (ARRAY), thumbnail_url, glb_url
- views, likes_count, saves_count
- status (processing/ready/failed)
- clip_embedding (JSONB)
- created_at, updated_at

**likes**
- id (PK), user_id (FK), artwork_id (FK)
- created_at

**collections**
- id (PK), user_id (FK), name, description
- cover_image_url, is_public, created_at

**collection_items**
- id (PK), collection_id (FK), artwork_id (FK)
- added_at

## Performance Optimization

### GPU Recommendations

For optimal AI processing speed:
- **Minimum**: NVIDIA GTX 1060 6GB
- **Recommended**: RTX 3060 12GB or better
- **Processing capacity**: 30-50 uploads per hour on RTX 3060

### Database Indexing

Create these indexes for production:

```sql
CREATE INDEX idx_artworks_status ON artworks(status);
CREATE INDEX idx_artworks_artist ON artworks(artist_id);
CREATE INDEX idx_artworks_created ON artworks(created_at DESC);
CREATE INDEX idx_likes_user_artwork ON likes(user_id, artwork_id);
CREATE INDEX idx_users_artist ON users(is_artist);
```

### Caching Strategy

Redis integration (when configured) caches:
- Artwork metadata (5 minutes TTL)
- Search results (2 minutes TTL)
- User recommendations (15 minutes TTL)

## Security Considerations

### Production Hardening

1. **Change default SECRET_KEY**: Generate a strong random key
```python
import secrets
print(secrets.token_urlsafe(32))
```

2. **Database credentials**: Use environment variables or secrets manager
3. **HTTPS**: Always use HTTPS in production (ngrok provides this automatically)
4. **Rate limiting**: Implement using slowapi or similar:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
limiter = Limiter(key_func=get_remote_address)
```

5. **File validation**: Enforce maximum file size and scan for malware

### Input Validation

The API validates:
- Image dimensions (max 4096x4096)
- File size (max 50MB)
- Price ranges (positive numbers)
- SQL injection prevention (SQLAlchemy parameterized queries)

## Monitoring and Logging

Logs are written to console by default. For production, configure file logging:

```python
import logging
logging.basicConfig(
    filename='wallora.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Monitor these metrics:
- API response times (p95, p99)
- AI processing queue length
- Database connection pool usage
- GPU memory utilization

## Troubleshooting

### Common Issues

**Models fail to download:**
- Check internet connection
- Set `HF_ENDPOINT=https://hf-mirror.com` for China-based deployments
- Manually download models and place in `models_cache/`

**Database connection errors:**
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check credentials in .env file
- Test connection: `psql -U wallora -h localhost -d wallora`

**Out of memory on GPU:**
- Reduce batch size in AI processing
- Set `CUDA_VISIBLE_DEVICES=""` to force CPU fallback
- Add swap space if running on limited RAM

**Slow file uploads:**
- Increase `MAX_UPLOAD_SIZE_MB` if needed
- Consider implementing chunked uploads for large files

## API Client Examples

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000"

# Login
response = requests.post(f"{BASE_URL}/auth/login", 
    data={"username": "user@example.com", "password": "pass"})
token = response.json()["access_token"]

# Upload artwork
headers = {"Authorization": f"Bearer {token}"}
files = {"file": open("artwork.jpg", "rb")}
data = {"title": "My Artwork", "price": 299.99}
response = requests.post(f"{BASE_URL}/artworks/", 
    headers=headers, files=files, data=data)
```

### Flutter/Dart

```dart
// Using dio package
final dio = Dio();
dio.options.headers['Authorization'] = 'Bearer $token';

FormData formData = FormData.fromMap({
  'file': await MultipartFile.fromFile('artwork.jpg'),
  'title': 'My Artwork',
  'price': '299.99',
});

final response = await dio.post('$baseUrl/artworks/', 
    data: formData);
```

