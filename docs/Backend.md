# Backend Architecture

The EduScribe AI backend is designed for high concurrency and asynchronous task execution, ensuring that long-running AI models do not block incoming API requests from the frontend.

## Core Technologies
- **FastAPI**: Provides the REST API interface.
- **Uvicorn**: The ASGI web server.
- **BackgroundTasks**: A FastAPI utility used to immediately return a 200/202 response while processing AI jobs in the background.

## Backend Workflow

![Backend Architecture](images/backend_architecture_1785262438708.png)
*Figure 8. FastAPI, Redis, and Background Worker Sequence Diagram.*

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI Router
    participant DB as PostgreSQL
    participant Worker as Background Task
    
    C->>API: POST /videos/upload
    API->>DB: Create initial record (Status: UPLOADING)
    API-->>C: Return 202 Accepted (Video ID)
    
    API->>Worker: Dispatch start_pipeline(video_id)
    
    loop Polling
        C->>API: GET /videos/{id}
        API->>DB: Fetch progress
        API-->>C: Status Update
    end
```

## Structure
- `/api/routers/`: Contains the REST endpoints (Auth, Videos, Frames).
- `/services/`: Contains the heavy business logic and API wrappers (YouTube fetching, Whisper, OpenCV).
- `/models/`: SQLAlchemy database schemas.
- `/schemas/`: Pydantic models for request/response validation.

## (Upcoming) Image Generation Service
A new service will be added to the backend (`/services/image_gen.py`). It will be triggered at the end of the transcription phase to generate educational images and save them to `/storage/images/`.
