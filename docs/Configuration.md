# Configuration

EduScribe AI requires several environment variables to function correctly. These are passed to the backend via a `.env` file located in the `/backend` directory.

## Environment Variables

### Core Settings
- `DATABASE_URL`: The PostgreSQL connection string. (e.g., `postgresql+asyncpg://user:password@host/dbname`)
- `SECRET_KEY`: A long, random string used to sign JWT tokens.
- `ALGORITHM`: Usually `HS256`.

### Google OAuth
Required for the authentication system.
- `GOOGLE_CLIENT_ID`: Obtained from the Google Cloud Console.
- `GOOGLE_CLIENT_SECRET`: Obtained from the Google Cloud Console.
- `FRONTEND_URL`: Usually `http://localhost:5173`. Used to redirect the user after a successful login.

### Hardware Tuning
- `WHISPER_MODEL`: The size of the model to load (`tiny`, `base`, `small`, `medium`, `large`). Defaults to `base`.
- `OCR_LANG`: The primary language for PaddleOCR. Defaults to `en`.

## Upcoming Configuration
To support the **AI Generated Simple Images** feature, you will soon need an API key for the image generation provider:
- `IMAGE_GEN_API_KEY`: The secret key for the selected AI image generation service.
