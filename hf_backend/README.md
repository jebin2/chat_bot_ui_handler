# Image Caption Generator

A Python-based image captioning service with a neobrutalist web interface. Upload image files via API, process them with AI-powered caption generation, and view results in a stunning UI.

## Features

- 🖼️ Image file upload via REST API
- 🤖 Automatic caption generation using BraveAISearch
- 💾 SQLite database for queue management
- 🎨 Neobrutalist UI with smooth animations
- 🔄 Real-time status updates
- 📱 Fully responsive design

## Project Structure

```
caption-generator/
├── app.py              # Flask API server
├── worker.py           # Background caption processing service
├── index.html          # Frontend UI
├── requirements.txt    # Python dependencies
├── image_captions.db   # SQLite database (auto-created)
└── uploads/            # Uploaded image files (auto-created)
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
python app.py
```

The server will start on `http://localhost:7860`

### 3. Access the Web Interface

Open your browser and navigate to:
```
http://localhost:7860
```

The worker thread starts automatically on first upload.

## Usage

### Via Web Interface

1. Click or drag-and-drop an image file onto the upload zone
2. Click "Upload & Generate Caption"
3. Watch the status update in real-time
4. View the generated caption once processing completes

### Via API

**Upload Image File:**
```bash
curl -X POST http://localhost:7860/api/upload \
  -F "image=@/path/to/your/image.png"
```

**Get All Files:**
```bash
curl http://localhost:7860/api/files
```

**Get Specific File:**
```bash
curl http://localhost:7860/api/files/<file_id>
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload image file |
| `/api/files` | GET | Get all files |
| `/api/files/<id>` | GET | Get specific file |
| `/health` | GET | Health check |

---

### `POST /api/upload`

Upload an image file for caption generation.

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | File | Yes | Image file (png, jpg, jpeg, gif, webp, bmp) |

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "image.png",
  "status": "not_started",
  "message": "File uploaded successfully"
}
```

**Error Responses:**

| Status | Response |
|--------|----------|
| 400 | `{"error": "No image file provided"}` |
| 400 | `{"error": "No file selected"}` |
| 400 | `{"error": "Invalid file type"}` |

---

### `GET /api/files`

Retrieve all uploaded files with their status and captions.

**Request:** No parameters required.

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "image.png",
    "status": "completed",
    "caption": "A serene landscape showing...",
    "created_at": "2024-01-15T10:30:00.000000",
    "processed_at": "2024-01-15T10:30:45.000000",
    "queue_position": null,
    "estimated_start_seconds": null
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "filename": "photo.jpg",
    "status": "processing",
    "caption": null,
    "created_at": "2024-01-15T10:35:00.000000",
    "processed_at": null,
    "queue_position": null,
    "estimated_start_seconds": null
  },
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "filename": "screenshot.png",
    "status": "not_started",
    "caption": null,
    "created_at": "2024-01-15T10:40:00.000000",
    "processed_at": null,
    "queue_position": 1,
    "estimated_start_seconds": 60
  }
]
```

---

### `GET /api/files/<file_id>`

Retrieve a specific file by its ID.

**Request:**

| Parameter | Type | Location | Description |
|-----------|------|----------|-------------|
| `file_id` | string | URL path | UUID of the file |

**Response (200 OK):**

*Example 1: Completed file*
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "image.png",
  "status": "completed",
  "caption": "A serene landscape showing mountains at sunset...",
  "created_at": "2024-01-15T10:30:00.000000",
  "processed_at": "2024-01-15T10:30:45.000000",
  "queue_position": null,
  "estimated_start_seconds": null
}
```

*Example 2: File in queue (3rd position)*
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "filename": "screenshot.png",
  "status": "not_started",
  "caption": null,
  "created_at": "2024-01-15T10:40:00.000000",
  "processed_at": null,
  "queue_position": 3,
  "estimated_start_seconds": 180
}
```

**Error Responses:**

| Status | Response |
|--------|----------|
| 404 | `{"error": "File not found"}` |

---

### `GET /health`

Check the health status of the service.

**Request:** No parameters required.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "image-caption-generator",
  "worker_running": true
}
```

## Database Schema

```sql
CREATE TABLE image_files (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    status TEXT NOT NULL,
    caption TEXT,
    created_at TEXT NOT NULL,
    processed_at TEXT
);
```

## Status Values

| Status | Description | `queue_position` | `estimated_start_seconds` |
|--------|-------------|------------------|---------------------------|
| `not_started` | File uploaded, waiting in queue for processing | **Integer (1-based)** - Position in queue (1 = next to be processed) | **Integer** - Estimated seconds until processing starts |
| `processing` | Currently being captioned by the worker | `null` | `null` |
| `completed` | Successfully captioned | `null` | `null` |
| `failed` | Error occurred during captioning | `null` | `null` |

> **Note:** 
> - `queue_position`: Indicates the file's position in the processing queue. A value of `1` means this file is next to be processed.
> - `estimated_start_seconds`: Calculated based on the average processing time of the last 20 completed files. If no files have been processed yet, defaults to 60 seconds per file. The estimate accounts for both files ahead in the queue and any file currently being processed.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `7860` | Server port |
| `BROWSER_PATH` | `/usr/bin/chromium` | Path to browser executable |

## Supported Image Formats

- PNG
- JPG/JPEG
- GIF
- WEBP
- BMP

## Troubleshooting

**Worker not processing files:**
- Ensure browser is properly installed
- Check that the temp_dir exists for output
- Verify the image file path is correct

**CORS errors:**
- Make sure flask-cors is installed
- Check that the API server is running

**Database errors:**
- Delete `image_captions.db` and restart the API server to recreate it

**Browser errors:**
- Ensure Chromium is installed: `apt-get install chromium`
- Check `BROWSER_PATH` environment variable

## Tech Stack

- **Backend:** Flask (Python)
- **Database:** SQLite
- **Frontend:** Vanilla HTML/CSS/JavaScript
- **Caption Generation:** BraveAISearch with headless browser
- **Design:** Neobrutalism with warm amber accents

## License

MIT