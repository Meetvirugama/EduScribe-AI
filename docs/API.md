# API Reference

The EduScribe AI backend exposes a RESTful API powered by FastAPI.

## Common Endpoints

![API Flow Diagram](images/api_flow_1785262383428.png)
*Figure 5. REST API Request Lifecycle.*

### 1. Videos
- `GET /videos/`: Fetch all videos for the authenticated user.
- `GET /videos/{id}`: Fetch detailed status and metadata for a specific video.
- `POST /videos/upload`: Upload a local `.mp4` file and initiate the pipeline.
- `POST /videos/youtube`: Provide a YouTube URL to trigger `yt-dlp` ingestion.
- `DELETE /videos/{id}`: Delete a video and all associated storage files.

### 2. Frames & OCR
- `GET /frames/video/{video_id}`: Fetch all extracted keyframes, sorted by their timestamp, along with their PaddleOCR results and visual scores.
- `POST /frames/video/{video_id}/extract`: Manually trigger the Vision Pipeline for a video that has already finished transcription.

### 3. Authentication
- `GET /auth/google/login`: Generates the Google OAuth consent URL.
- `GET /auth/google/callback`: Verifies the Google payload and issues a local JWT.

## Upcoming Endpoints (AI Images)
- `GET /notes/video/{video_id}`: Fetches the final generated educational notes, including embedded references to the **AI Generated Simple Images**.
