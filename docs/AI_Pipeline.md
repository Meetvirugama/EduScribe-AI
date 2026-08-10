# AI Pipeline — Vision & Audio Models

EduScribe AI uses a combination of specialised AI models and computer vision algorithms to process multimedia content. The models described here run locally — no cloud API calls for audio or vision processing.

> **LLM content generation** (quiz, flashcards, concept extraction, etc.) is covered in [LLM & Content Generation](LLM_Content_Generation.md).

---

### 1. Speech-to-Text: faster-whisper (CTranslate2)

- **Engine:** CTranslate2 (NOT PyTorch — replaced for performance)
- **Quantization:** INT8 — halves memory usage, 4–8x faster inference on CPU
- **Purpose:** Converts 16kHz mono WAV audio into timestamped text segments
- **VAD filter:** Voice Activity Detection skips silence regions (~20% speed gain)
- **Memory management:** Model is lazy-loaded with a thread lock and **unloaded after each transcription** to free RAM for the OCR pipeline

```python
from faster_whisper import WhisperModel
model = WhisperModel("base", device="cpu", compute_type="int8")
segments, info = model.transcribe(audio_path, vad_filter=True, beam_size=5)
# After transcription:
del model; gc.collect()  # Frees ~75MB for OCR
```

**Performance (1-hour lecture, CPU):**
- openai-whisper (FP32): ~15 min
- faster-whisper base (INT8): ~3–4 min (**4–5x speedup**)

---

### 2. Scene Detection: PySceneDetect

- **Algorithm:** `ContentDetector` (pixel-level frame difference)
- **Threshold:** 27.0 (scene change sensitivity)
- **Adaptive downscaling:** `downscale = frame_width // 640` — reduces CPU cost by ~6x for HD/4K video
- **Fallback:** If no scenes detected (static slides), creates time-based segments every N seconds

```python
from scenedetect import SceneManager, ContentDetector
scene_manager.add_detector(ContentDetector(threshold=27.0))
video_manager.set_downscale_factor(downscale)
```

---

### 3. Frame Extraction: OpenCV

- **Strategy:** Best-of-2 adaptive sampling — evaluates midpoint and 66% position per scene, keeps the sharper frame
- **Sharpness metric:** Laplacian variance computed on 320px-wide resized frame (90% less CPU than full resolution)
- **Path format:** Web-relative paths stored in DB (`storage/frames/{video_id}/scene_xxxx.jpg`) for portable URL construction

```python
cv2.VideoCapture.set(cv2.CAP_PROP_POS_MSEC, timestamp_ms)
frame = cap.read()
gray_small = cv2.resize(frame, (320, ...))
score = cv2.Laplacian(gray_small, cv2.CV_16S).var()  # CV_16S = 4x less memory
```

---

### 4. Duplicate Detection: dHash (imagehash)

- **Algorithm:** Difference hash — integer pixel gradient comparisons
- **Faster than pHash** (DCT-based): 5–10x speed advantage with equivalent deduplication accuracy
- **Two-stage check:**
  - Stage 1: Compare vs. last unique frame — O(1)
  - Stage 2: Compare vs. `deque(maxlen=50)` of recent unique frames — O(50N) = O(N)

```python
from collections import deque
seen_hashes: deque = deque(maxlen=50)  # Prevents O(N²) worst case
```

**Pillow `.draft()` for low-cost decoding:**
```python
img.draft("RGB", (32, 32))  # libjpeg decodes at reduced resolution directly
```

---

### 5. Blur Detection: Laplacian Variance (OpenCV)

- **Operator:** 2nd derivative of image intensity — high variance = sharp edges = sharp frame
- **Precision:** `cv2.CV_16S` (16-bit signed) instead of default CV_64F — 4x less memory, better CPU cache locality
- **Adaptive threshold:**

```python
import statistics
def adaptive_blur_threshold(frames):
    scores = [f["blur_score"] for f in frames if "blur_score" in f]
    return max(BLUR_THRESHOLD, statistics.median(scores) * 0.5)
```

Prevents over-filtering for low-contrast content (dark slides, screen recordings).

**Score reuse:** Blur scores computed during Frame Extraction are **reused** in this stage — no redundant disk I/O.

---

### 6. Optical Character Recognition: PaddleOCR

- **Engine:** PaddlePaddle
- **Purpose:** Detects and recognizes text bounding boxes on frame images
- **Advantage over Tesseract:** Superior accuracy on non-standard backgrounds (presentation slides, whiteboards), and ~4x faster with GPU
- **Pre-filter:** Edge density check (`has_meaningful_text()`) skips ~40% of frames with no detectable text
- **Resize:** Frames >1280px are resized to 1280px before inference
- **Async lock:** Global `asyncio.Lock()` prevents concurrent inference

**LRU cache:**
```python
from cachetools import LRUCache
_backend = LRUCache(maxsize=500)  # Caps memory — replaces unbounded dict
```

| Configuration | Inference Time/Frame | VRAM |
|---|---|---|
| CPU (current) | 800ms–2s | 0 |
| GPU mode | 50–150ms | ~2 GB |

---

### 7. Transcript Matching: RapidFuzz

- **Algorithm:** `token_set_ratio` — robust to word reordering and partial matches
- **Purpose:** Links each frame to the transcript segment active at its timestamp
- **Output:** `transcript_similarity` score (0–100) used in the composite visual importance score

---

### 8. Frame Scoring & Selection

Each frame receives a composite `visual_importance_score`:

```
score = w1 * (1 - blur_score_normalized)   # Sharpness
      + w2 * transcript_similarity          # Semantic relevance
      + w3 * ocr_line_count_normalized      # Content richness
      + w4 * ocr_confidence                 # OCR quality
```

**Per-scene selection** (critical fix):
```python
from itertools import groupby

scored_frames.sort(key=lambda x: (x["scene_number"], -x["visual_importance_score"]))
for scene_num, scene_iter in groupby(scored_frames, key=lambda x: x["scene_number"]):
    scene_frames = list(scene_iter)
    for i, frame in enumerate(scene_frames):
        if i < top_n:
            frame["is_selected"] = True
```

1 best frame is selected per scene. A 30-scene lecture produces 30 selected frames.

---

## 📊 Performance Summary

| Model | CPU Cost | Memory | Notes |
|---|---|---|---|
| faster-whisper base INT8 | Medium (3–4 min/hr) | ~75MB | Freed after use |
| PySceneDetect | Low (1–2 min/hr) | Minimal | 640px downscale |
| OpenCV frame extractor | Very Low | Minimal | Best-of-2, 320px blur check |
| dHash dedup | Negligible | O(50) deque | Integer comparison |
| Laplacian blur | Negligible | CV_16S matrix | Score reused from extraction |
| PaddleOCR CPU | High (2–3 min total) | ~500MB peak | LRU cache, edge pre-filter |
| RapidFuzz | Negligible | Minimal | token_set_ratio |

---

## 🚀 GPU Upgrade Path

| Model | GPU Gain | Memory |
|---|---|---|
| faster-whisper large-v3 (CUDA, INT8) | 10–15x | 3–6 GB VRAM |
| PaddleOCR GPU mode | ~10x | ~2 GB VRAM |

Enable GPU:
```python
# Whisper
model = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")

# PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang="en", use_gpu=True)
```
