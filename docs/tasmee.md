# Tasmeeʿ (Memorization) Feature Documentation

## Overview

Tasmeeʿ (تسميع) is a Quran memorization practice feature that provides real-time feedback on recitation accuracy. The feature uses local, offline Speech-to-Text (STT) to transcribe audio, then aligns the transcription with expected Quranic text to detect mistakes.

**Key Design Principles:**
- **100% Free & Offline**: Uses faster-whisper (MIT license) - no cloud APIs, no credits
- **Arabic-First**: Optimized for Arabic text normalization and Quranic recitation
- **Real-Time Feedback**: Word-by-word highlighting as the user recites
- **Privacy**: All processing happens locally on the user's machine

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │     │     Backend     │     │  faster-whisper │
│   TasmeePage    │ ──▶ │  /tasmee/*      │ ──▶ │    (Local STT)  │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│    Arabic     │      │   Alignment   │      │   Database    │
│  Normalizer   │      │    Engine     │      │   (Sessions)  │
└───────────────┘      └───────────────┘      └───────────────┘
```

### Components

1. **Frontend (`TasmeePage.tsx`)**: React component with audio recording, word highlighting, and mistake alerts
2. **Backend API (`/api/v1/tasmee/*`)**: FastAPI endpoints for session management and transcription
3. **STT Provider (`stt/providers/`)**: Pluggable STT backend with faster-whisper as default
4. **Arabic Normalizer (`stt/arabic_normalizer.py`)**: Text normalization for matching
5. **Alignment Engine (`stt/alignment.py`)**: Word-level alignment and mistake detection
6. **Database Models (`models/tasmee.py`)**: Session and mistake storage

## Installation

### Prerequisites

- Python 3.10+
- 4GB+ RAM (8GB recommended for medium model)
- CUDA-capable GPU (optional but recommended for speed)

### Install faster-whisper

```bash
# Install with pip
pip install faster-whisper

# Or with poetry
poetry add faster-whisper
```

### Model Download

Models are downloaded automatically on first use. Available models:

| Model | Size | RAM Required | Speed (CPU) | Speed (GPU) | Accuracy |
|-------|------|--------------|-------------|-------------|----------|
| tiny | 39 MB | ~1 GB | ~10x realtime | ~30x realtime | Low |
| base | 74 MB | ~1 GB | ~5x realtime | ~20x realtime | Medium |
| small | 244 MB | ~2 GB | ~2x realtime | ~10x realtime | Good |
| medium | 769 MB | ~5 GB | ~1x realtime | ~5x realtime | Better |
| large-v2 | 1.5 GB | ~10 GB | ~0.5x realtime | ~3x realtime | Best |
| large-v3 | 1.5 GB | ~10 GB | ~0.5x realtime | ~3x realtime | Best |

**Recommended for Tasmeeʿ:**
- **Development/Testing**: `base` or `small`
- **Production (CPU)**: `small` (best balance)
- **Production (GPU)**: `medium` or `large-v2`

### Environment Variables

```bash
# STT Configuration
STT_MODEL_SIZE=small          # Model size (tiny|base|small|medium|large-v2|large-v3)
STT_DEVICE=auto               # Device (auto|cpu|cuda)
STT_COMPUTE_TYPE=default      # Compute type (default|int8|float16|float32)

# Alignment Configuration
TASMEE_MATCH_THRESHOLD=0.75   # Minimum similarity for word match (0.0-1.0)
TASMEE_MISMATCH_PATIENCE=2    # Consecutive mismatches before flagging
TASMEE_LOOKAHEAD_WINDOW=5     # Words to look ahead for deletion detection
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/tasmee/sessions` | POST | Create new practice session |
| `/api/v1/tasmee/sessions` | GET | List user's sessions |
| `/api/v1/tasmee/sessions/{id}` | GET | Get session details |
| `/api/v1/tasmee/sessions/{id}` | PUT | Update session |
| `/api/v1/tasmee/transcribe` | POST | Transcribe audio chunk |
| `/api/v1/tasmee/ws/{session_id}` | WS | WebSocket for streaming |
| `/api/v1/tasmee/health` | GET | Check STT service health |

## Running Locally

### 1. Start the Backend

```bash
cd backend

# Install dependencies
poetry install

# Run with default settings
python -m uvicorn app.main:app --reload

# Or with specific STT model
STT_MODEL_SIZE=small python -m uvicorn app.main:app --reload
```

### 2. Start the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### 3. Access Tasmeeʿ

Navigate to `http://localhost:5173/tasmee` in your browser.

## Usage Guide

### Basic Workflow

1. **Select Surah/Ayah**: Choose the verses you want to practice
2. **Start Recording**: Click the microphone button to begin
3. **Recite**: Read the verses aloud at a natural pace
4. **View Feedback**: Watch words highlight as they're recognized
5. **Review Mistakes**: See a summary of any mistakes detected

### Word Status Colors

| Color | Status | Meaning |
|-------|--------|---------|
| Green | Completed | Word matched correctly |
| Blue | Current | Word currently being recited |
| Gray | Pending | Word not yet reached |
| Red | Error | Mistake detected |
| Yellow | Warning | Low confidence match |

### Mistake Types

| Type | Arabic | Description |
|------|--------|-------------|
| Substitution | استبدال | Wrong word spoken |
| Deletion | حذف | Word skipped |
| Insertion | إضافة | Extra word added |
| Repetition | تكرار | Word repeated |
| Mispronunciation | خطأ نطق | Similar but incorrect pronunciation |

## Arabic Normalization

The normalizer handles common variations in Arabic text:

### Diacritics (Tashkeel)

All diacritics are removed for matching:
- Fatha (◌َ), Kasra (◌ِ), Damma (◌ُ)
- Sukun (◌ْ), Shadda (◌ّ)
- Tanween (ً ٌ ٍ)

### Letter Variants

| Original | Normalized | Example |
|----------|------------|---------|
| أ إ آ ٱ | ا | آدم → ادم |
| ى | ي | موسى → موسي |
| ة | ه (optional) | رحمة → رحمه |
| ـ (tatweel) | (removed) | اللـه → الله |

### Example

```python
from app.stt.arabic_normalizer import normalize_for_matching

text1 = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
text2 = "بسم الله الرحمن الرحيم"

assert normalize_for_matching(text1) == normalize_for_matching(text2)
# Both normalize to: "بسم الله الرحمن الرحيم"
```

## Troubleshooting

### Issue: Slow Transcription

**Symptoms:**
- Long delay between speaking and text appearing
- Audio buffer overflows

**Solutions:**

1. **Use smaller model:**
   ```bash
   STT_MODEL_SIZE=base python -m uvicorn app.main:app
   ```

2. **Enable GPU (if available):**
   ```bash
   STT_DEVICE=cuda python -m uvicorn app.main:app
   ```

3. **Reduce audio quality:**
   - Use 16kHz sample rate (default)
   - Use mono audio (single channel)

### Issue: Poor Accuracy

**Symptoms:**
- Many false mistake detections
- Words not matching despite correct recitation

**Solutions:**

1. **Use larger model:**
   ```bash
   STT_MODEL_SIZE=medium python -m uvicorn app.main:app
   ```

2. **Adjust match threshold:**
   ```bash
   TASMEE_MATCH_THRESHOLD=0.7 python -m uvicorn app.main:app
   ```

3. **Increase mismatch patience:**
   ```bash
   TASMEE_MISMATCH_PATIENCE=3 python -m uvicorn app.main:app
   ```

4. **Check microphone quality:**
   - Use headset mic for clearer audio
   - Reduce background noise
   - Speak clearly at moderate pace

### Issue: Model Not Loading

**Symptoms:**
- Error: "Could not load model"
- Startup timeout

**Debug Steps:**

1. Check disk space (models need up to 1.5 GB):
   ```bash
   df -h
   ```

2. Check model download:
   ```bash
   # Models are cached in ~/.cache/huggingface/hub/
   ls -la ~/.cache/huggingface/hub/models--*whisper*
   ```

3. Test model directly:
   ```python
   from faster_whisper import WhisperModel
   model = WhisperModel("small", device="cpu")
   print("Model loaded successfully")
   ```

### Issue: WebSocket Connection Failed

**Symptoms:**
- Real-time streaming not working
- Connection drops during recording

**Debug Steps:**

1. Check WebSocket endpoint:
   ```bash
   # Test with websocat
   websocat ws://localhost:8000/api/v1/tasmee/ws/test-session
   ```

2. Check browser console for errors

3. Verify CORS settings in backend

### Issue: High Memory Usage

**Symptoms:**
- Backend consuming too much RAM
- Out of memory errors

**Solutions:**

1. Use INT8 quantization:
   ```bash
   STT_COMPUTE_TYPE=int8 python -m uvicorn app.main:app
   ```

2. Use smaller model:
   ```bash
   STT_MODEL_SIZE=tiny python -m uvicorn app.main:app
   ```

3. Unload model when not in use (automatic after timeout)

## CPU vs GPU Performance

### CPU Recommendations

- **Intel Core i5/i7 (8th gen+)**: Use `small` model
- **AMD Ryzen 5/7**: Use `small` model
- **Apple M1/M2**: Use `medium` model (optimized)

### GPU Recommendations

- **NVIDIA GTX 1060+**: Use `medium` model with CUDA
- **NVIDIA RTX 2060+**: Use `large-v2` model with CUDA
- **AMD GPUs**: CPU-only (CUDA not supported)

### Performance Comparison

| Model | CPU (i7-10th) | GPU (RTX 3060) |
|-------|---------------|----------------|
| tiny | 10x realtime | 30x realtime |
| small | 2x realtime | 10x realtime |
| medium | 0.5x realtime | 5x realtime |
| large-v2 | 0.2x realtime | 3x realtime |

*"Nx realtime" means N seconds of audio processed per second*

## Testing

### Run Unit Tests

```bash
cd backend
PYTHONPATH=. pytest tests/unit/tasmee/ -v
```

### Run Integration Tests (Mock STT)

```bash
cd backend
PYTHONPATH=. pytest tests/integration/test_tasmee.py -v
```

### Run Real Integration Tests (Real STT + Audio)

These tests use real Quran recitation audio and the real faster-whisper model.

**Step 1: Download Audio Fixtures**

```bash
cd backend/tests/fixtures/audio

# Install ffmpeg (for WAV conversion)
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg      # macOS

# Download test audio from EveryAyah.com
python download_fixtures.py
```

This downloads verse-by-verse recitation of:
- Al-Fatiha (1:1-7)
- Surah Al-Ikhlas (112:1-4)

**Step 2: Run Real Tests**

```bash
cd backend

# Run with default settings (base model, CPU)
PYTHONPATH=. pytest tests/integration/test_tasmee_real.py -v -s

# Run with smaller model (faster, less accurate)
STT_MODEL_SIZE=tiny PYTHONPATH=. pytest tests/integration/test_tasmee_real.py -v -s

# Run with GPU (if available)
STT_DEVICE=cuda STT_MODEL_SIZE=small PYTHONPATH=. pytest tests/integration/test_tasmee_real.py -v -s

# Skip slow benchmark tests
PYTHONPATH=. pytest tests/integration/test_tasmee_real.py -v -m "not slow"
```

### Test Arabic Normalizer

```bash
cd backend
PYTHONPATH=. pytest tests/unit/tasmee/test_arabic_normalizer.py -v
```

### Test Alignment

```bash
cd backend
PYTHONPATH=. pytest tests/unit/tasmee/test_alignment.py -v
```

### Audio Fixtures

The test audio comes from [EveryAyah.com](https://everyayah.com/), a free resource providing verse-by-verse Quran recitation. Default reciter is Mishary Rashid Al Afasy.

| File | Verse | Text |
|------|-------|------|
| 001_001_bismillah.wav | 1:1 | بسم الله الرحمن الرحيم |
| 001_002_alhamdulillah.wav | 1:2 | الحمد لله رب العالمين |
| 001_003_arrahman.wav | 1:3 | الرحمن الرحيم |
| 001_004_maliki.wav | 1:4 | مالك يوم الدين |
| 001_005_iyyaka.wav | 1:5 | إياك نعبد وإياك نستعين |
| 001_006_ihdina.wav | 1:6 | اهدنا الصراط المستقيم |
| 001_007_sirat.wav | 1:7 | صراط الذين أنعمت عليهم... |
| 112_001_ikhlas_1.wav | 112:1 | قل هو الله أحد |
| 112_002_ikhlas_2.wav | 112:2 | الله الصمد |
| 112_003_ikhlas_3.wav | 112:3 | لم يلد ولم يولد |
| 112_004_ikhlas_4.wav | 112:4 | ولم يكن له كفوا أحد |

## Swapping STT Providers

The system supports pluggable STT providers. To add a new provider:

### 1. Create Provider Class

```python
# app/stt/providers/my_provider.py
from app.stt.providers.base import STTProvider, STTResult

class MyProvider(STTProvider):
    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def model_name(self) -> str:
        return "my-model"

    @property
    def supports_streaming(self) -> bool:
        return True

    def load_model(self):
        # Load your model
        pass

    def unload_model(self):
        # Unload your model
        pass

    def transcribe(self, audio, sample_rate=16000, word_timestamps=True) -> STTResult:
        # Transcribe audio
        pass

    def transcribe_stream(self, audio_chunks, sample_rate=16000, chunk_duration=2.0):
        # Stream transcription
        pass
```

### 2. Register Provider

```python
# app/stt/__init__.py
from .providers.my_provider import MyProvider

def get_stt_provider(provider_name: str = "faster-whisper", **kwargs) -> STTProvider:
    providers = {
        "faster-whisper": FasterWhisperProvider,
        "my-provider": MyProvider,  # Add here
    }
    return providers[provider_name](**kwargs)
```

### 3. Use Provider

```bash
STT_PROVIDER=my-provider python -m uvicorn app.main:app
```

### Future Provider: Vosk

Vosk is planned as an alternative provider for extremely low-resource environments:

```python
# Planned implementation
STT_PROVIDER=vosk python -m uvicorn app.main:app
```

## API Response Formats

### Create Session Response

```json
{
  "id": "uuid",
  "surah_number": 1,
  "start_ayah": 1,
  "end_ayah": 7,
  "expected_text": "بسم الله الرحمن الرحيم...",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Transcription Response

```json
{
  "text": "بسم الله الرحمن الرحيم",
  "segments": [
    {
      "text": "بسم الله",
      "start_time": 0.0,
      "end_time": 0.8,
      "words": [
        {"word": "بسم", "start": 0.0, "end": 0.4, "confidence": 0.95},
        {"word": "الله", "start": 0.4, "end": 0.8, "confidence": 0.98}
      ],
      "confidence": 0.96
    }
  ],
  "language": "ar",
  "duration": 2.5
}
```

### Alignment Result

```json
{
  "matched": true,
  "words_matched": 4,
  "mistakes": [],
  "highlighted_text": [
    {"word": "بسم", "status": "completed"},
    {"word": "الله", "status": "completed"},
    {"word": "الرحمن", "status": "current"},
    {"word": "الرحيم", "status": "pending"}
  ],
  "state": {
    "current_position": 2,
    "total_words": 4,
    "progress": 0.5,
    "is_complete": false,
    "confidence": 0.95
  }
}
```

### Mistake Object

```json
{
  "type": "substitution",
  "severity": "major",
  "position": 2,
  "expected_word": "رب",
  "actual_word": "ملك",
  "timestamp": 0.6,
  "confidence": 0.85,
  "context_before": ["الحمد", "لله"],
  "context_after": ["العالمين"]
}
```

## Health Check

```bash
# Check Tasmee service health
curl -s http://localhost:8000/api/v1/tasmee/health | python3 -m json.tool
```

### Health Response

```json
{
  "status": "ok",
  "stt_provider": "faster-whisper",
  "model_loaded": true,
  "model_name": "small",
  "device": "cuda",
  "supports_streaming": true
}
```

## Quick Reference

### Start Recording (JavaScript)

```javascript
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

mediaRecorder.ondataavailable = (e) => {
  // Send audio chunk to backend
  sendAudioChunk(e.data);
};

mediaRecorder.start(1000); // Chunk every 1 second
```

### Python Usage

```python
from app.stt import get_stt_provider
from app.stt.alignment import RecitationAligner

# Initialize
provider = get_stt_provider("faster-whisper", model_size="small")
aligner = RecitationAligner("بسم الله الرحمن الرحيم")

# Transcribe and align
result = provider.transcribe(audio_data)
for segment in result.segments:
    alignment = aligner.process_segment(segment)
    print(f"Progress: {aligner.state.progress * 100:.0f}%")
    print(f"Mistakes: {len(alignment.mistakes)}")
```

## Contact

For issues:
1. Check the troubleshooting section above
2. Include STT health status in bug reports
3. Capture browser console logs for frontend issues
4. Include backend logs with `request_id`
