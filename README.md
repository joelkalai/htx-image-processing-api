# HTX Image Processing Pipeline API

A production-ready image processing pipeline API that automatically processes images, generates thumbnails, extracts metadata, and provides AI-powered image captioning through RESTful endpoints.

**Developed for**: HTX Digital Forensics Internship - Software Engineering Assessment

## 🚀 Quick Start (Docker - Recommended)

The fastest way to run this application is using Docker:

```bash
# Clone the repository
git clone <repository-url>
cd htx-image-processing-api

# Start with Docker Compose (recommended)
docker-compose up --build

# Or build and run with Docker directly
docker build -t htx-image-api .
docker run -p 8000:8000 -v $(pwd)/storage:/app/storage htx-image-api
```

The API will be available at http://localhost:8000

## ✨ Features

### Core Functionality
- **Asynchronous Image Upload**: Non-blocking processing with immediate response
- **Automatic Thumbnail Generation**: Creates small (256px) and medium (768px) versions
- **Metadata Extraction**: Width, height, format, file size, and EXIF data (when available)
- **AI-Powered Captioning**: Automatic image description using Hugging Face BLIP model
- **RESTful API**: Clean, well-documented endpoints
- **Persistent Storage**: SQLite database with organized file storage

### Technical Highlights
- Built with **FastAPI** for high performance
- **SQLAlchemy** ORM for database operations
- **Pillow** for image processing
- **Transformers** for AI captioning
- **Loguru** for structured logging (no print statements)
- Comprehensive error handling and validation
- Docker support for easy deployment

## 📚 API Documentation

### Interactive Documentation
Once running, visit http://localhost:8000/docs for interactive Swagger UI

### Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/images` | Upload and process image |
| GET | `/api/images` | List all images |
| GET | `/api/images/{id}` | Get image details with caption |
| GET | `/api/images/{id}/thumbnails/{size}` | Download thumbnail |
| GET | `/api/stats` | Processing statistics |

### Example Usage

#### Upload an Image
```bash
curl -X POST -F "file=@/path/to/image.jpg" http://localhost:8000/api/images
```

**Response:**
```json
{
  "status": "accepted",
  "data": {
    "image_id": "550e8400-e29b-41d4-a716-446655440000",
    "original_name": "image.jpg",
    "status": "queued",
    "thumbnails": {
      "small": "http://localhost:8000/api/images/550e8400-e29b-41d4-a716-446655440000/thumbnails/small",
      "medium": "http://localhost:8000/api/images/550e8400-e29b-41d4-a716-446655440000/thumbnails/medium"
    }
  }
}
```

#### Get Image Details with AI Caption
```bash
curl http://localhost:8000/api/images/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "original_name": "image.jpg",
  "status": "done",
  "caption": "a cat sitting on a windowsill looking outside",
  "metadata": {
    "width": 1920,
    "height": 1080,
    "format": "jpeg",
    "size_bytes": 2048576,
    "exif": {...}
  },
  "thumbnails": {...}
}
```

## 🛠 Installation

### Option 1: Docker (Recommended)

```bash
# Using Docker Compose
docker-compose up --build

# Or using Docker directly
docker build -t htx-image-api .
docker run -p 8000:8000 htx-image-api
```

### Option 2: Local Installation

**Requirements:**
- Python 3.12 (with lzma support)
- pip

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔧 Configuration

The application can be configured via environment variables in `.env`:

```env
# Application settings
APP_NAME=HTX Image Pipeline
BASE_URL=http://localhost:8000
DATABASE_URL=sqlite:///./data.db

# AI Captioning Model (Hugging Face)
CAPTION_MODEL=Salesforce/blip-image-captioning-base
# Options:
# - Salesforce/blip-image-captioning-base (default, balanced)
# - Salesforce/blip-image-captioning-large (better quality, slower)
# - nlpconnect/vit-gpt2-image-captioning (faster, smaller)
# - disabled (turn off captioning)
```

## 📂 Project Structure

```
htx-image-processing-api/
├── app/
│   ├── main.py              # FastAPI application
│   ├── models.py             # Database models
│   ├── schemas.py            # Pydantic schemas
│   ├── processing.py         # Image processing logic
│   ├── caption.py            # AI captioning
│   ├── config.py             # Configuration
│   └── database.py           # Database setup
├── storage/
│   ├── originals/            # Original uploaded images
│   └── thumbs/
│       ├── small/            # 256px thumbnails
│       └── medium/           # 768px thumbnails
├── tests/
│   └── test_api.py          # Unit tests
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile               # Docker image definition
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── README.md              # This file
```

## 🧪 Testing

Run the test suite:

```bash
# With pytest
pytest tests/

# With Docker
docker-compose run api pytest tests/
```

## 📝 Requirements Met

This implementation fulfills all requirements from the HTX assessment:

### Core Requirements ✅
- [x] POST /api/images - Upload with async processing
- [x] GET /api/images - List all images
- [x] GET /api/images/{id} - Get details with metadata
- [x] GET /api/images/{id}/thumbnails/{size} - Serve thumbnails
- [x] GET /api/stats - Processing statistics
- [x] Two thumbnail sizes (256px, 768px)
- [x] Metadata extraction (dimensions, format, size)
- [x] AI captioning with Hugging Face
- [x] SQLite database storage
- [x] JPG/PNG format support
- [x] Error handling
- [x] Logging with loguru
- [x] Unit tests
- [x] Clear documentation

### Bonus Features ✅
- [x] EXIF data extraction
- [x] Non-blocking async processing with job queue
- [x] Processing status tracking
- [x] Docker support
- [x] File size validation (10MB limit)

## ⚠️ Important Notes

1. **Python Version**: Requires Python 3.12 with lzma support. Use Docker if you encounter issues with local Python installation.

2. **First Run**: The AI model will be downloaded on first use (~1GB). Ensure you have internet connectivity and sufficient disk space.

3. **Storage**: Uploaded images and thumbnails are stored in the `storage/` directory. This can be mounted as a volume in Docker for persistence.

## 🐛 Troubleshooting

### Captioning Returns Null
- Ensure CAPTION_MODEL is not set to "disabled"
- Check internet connection for model download
- Verify Python has lzma support (use Docker if issues persist)

### Port Already in Use
```bash
# Change port in docker-compose.yml or use:
docker-compose run -p 8001:8000 api
```

### Slow First Image
The AI model loads on first use. Subsequent images process much faster.

## 📄 License

Developed for HTX Digital Forensics Internship Assessment

---

**Assessment**: HTX Digital Forensics Internship - Challenge 1 (Software Engineering)