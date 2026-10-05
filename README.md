# Google Flow / Veo Video Generation Client

This project provides a Python integration to generate videos according to natural language instructions using the **Veo** models (the generative engine behind **Google Flow**).

---

## 🚀 Features

- **Text-to-Video**: Generate cinematic videos directly from natural language prompts and direction notes.
- **Image-to-Video**: Start from a keyframe image and animate it based on instructions.
- **Prompt Enhancement**: Leverage Google's automated prompt optimization to expand scene details, camera movement, and lighting.
- **Aspect Ratio Control**: Supports both `16:9` (widescreen/cinematic) and `9:16` (vertical video / YouTube Shorts / TikTok).
- **Resolution Control**: `720p` or `1080p`.

---

## 🛠️ Setup Instructions

### 1. Get an API Key
Obtain an API key from [Google AI Studio](https://aistudio.google.com/).

### 2. Set Your Environment Variable
Create a `.env` file in the project root:
```env
GEMINI_API_KEY="your-google-ai-studio-api-key"
```

Or set it in your terminal:
```powershell
$env:GEMINI_API_KEY="your-google-ai-studio-api-key"
```

### 3. Install Dependencies
```powershell
.venv\Scripts\pip install -r requirements.txt
```

---

## 💻 Usage

### Command Line (CLI)

#### 1. Text-to-Video:
```powershell
.venv\Scripts\python main.py --prompt "Cinematic aerial shot of waves crashing against Icelandic black sand beach at sunrise, dramatic lighting, 4k" --output ocean.mp4 --aspect-ratio 16:9
```

#### 2. Vertical Video (Shorts / Reels):
```powershell
.venv\Scripts\python main.py --prompt "Cyberpunk street with neon reflections in rain puddles, slow tracking camera" --output cyberpunk.mp4 --aspect-ratio 9:16
```

#### 3. Image-to-Video:
```powershell
.venv\Scripts\python main.py --image "input_frame.png" --prompt "The character slowly turns to look at the camera and smiles, gentle breeze blowing hair" --output character_animation.mp4
```

---

## 🐍 Python Code Example

```python
from google_flow_video import GoogleFlowVideoClient

# Initialize client (picks up GEMINI_API_KEY from environment or .env)
client = GoogleFlowVideoClient()

# Generate video from prompt instructions
video_path = client.generate_video(
    prompt="A majestic eagle soaring over snow-capped mountains, cinematic 35mm lens, golden hour glow",
    output_path="eagle_flight.mp4",
    duration_seconds=5,
    aspect_ratio="16:9",
    resolution="720p",
    enhance_prompt=True,
)

print(f"Generated video saved to: {video_path}")
```
