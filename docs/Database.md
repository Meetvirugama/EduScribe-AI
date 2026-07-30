# Database Schema

EduScribe AI uses **PostgreSQL** to securely store relational data across users, videos, and generated AI metadata.

## Entity Relationship Diagram

![Database Schema](images/database_schema_1785262327655.png)
*Figure 4. PostgreSQL Database Schema.*

```mermaid
erDiagram
    USERS ||--o{ VIDEOS : owns
    VIDEOS ||--o{ TRANSCRIPTS : has
    VIDEOS ||--o{ VIDEO_FRAMES : has
    VIDEO_FRAMES ||--o| FRAME_METADATA : analyzes
    VIDEO_FRAMES ||--o| OCR_RESULTS : extracts
    VIDEO_FRAMES ||--o| FRAME_SCORES : grades
    
    USERS {
        uuid id PK
        string email
        string google_id
    }
    
    VIDEOS {
        uuid id PK
        string user_id FK
        string title
        string status
        int progress_percent
    }
    
    TRANSCRIPTS {
        uuid id PK
        uuid video_id FK
        string transcript_path
        int word_count
    }
    
    VIDEO_FRAMES {
        uuid id PK
        uuid video_id FK
        int timestamp_ms
        string frame_path
    }
```

## Upcoming Schema Changes
To support the **AI Generated Simple Images** feature, a new table will be introduced to track the mapping between transcript concepts and their generated illustrations:

```mermaid
erDiagram
    TRANSCRIPTS ||--o{ AI_GENERATED_IMAGES : contains
    
    AI_GENERATED_IMAGES {
        uuid id PK
        uuid transcript_id FK
        int start_timestamp_ms
        int end_timestamp_ms
        string concept_topic
        string prompt_used
        string image_path
    }
```
