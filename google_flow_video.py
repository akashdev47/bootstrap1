"""
Google Flow Video Generator Client
----------------------------------
Google Flow is Google's creative studio powered by Google's state-of-the-art
video models (Veo). This module provides a programmatic interface to connect
to the Google GenAI API to generate high-fidelity videos from text instructions,
images, and video extensions.

Requires:
  - google-genai
  - GEMINI_API_KEY environment variable set or passed explicitly.
"""

import os
import time
from typing import Optional, Literal
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if available
load_dotenv()

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


class GoogleFlowVideoClient:
    """Client for generating videos using Google's Veo models (Google Flow engine)."""

    DEFAULT_MODEL = "veo-3.1-generate-preview"
    FALLBACK_MODEL = "veo-2.0-generate-001"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Google Flow Video client.
        
        Args:
            api_key: Optional Gemini / Google AI Studio API key. 
                     If omitted, reads from the GEMINI_API_KEY environment variable.
        """
        if genai is None:
            raise ImportError(
                "The 'google-genai' package is required. "
                "Install it using: pip install google-genai"
            )

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No API key provided. Set the 'GEMINI_API_KEY' environment variable "
                "or pass `api_key` directly to GoogleFlowVideoClient."
            )

        self.client = genai.Client(api_key=self.api_key)

    def generate_video(
        self,
        prompt: str,
        output_path: str = "generated_video.mp4",
        model: Optional[str] = None,
        duration_seconds: int = 5,
        aspect_ratio: Literal["16:9", "9:16"] = "16:9",
        resolution: Literal["720p", "1080p"] = "720p",
        enhance_prompt: bool = True,
        poll_interval_seconds: int = 10,
        verbose: bool = True,
    ) -> str:
        """
        Generate a video from a text instruction / prompt.

        Args:
            prompt: Text instruction describing the scene, camera movement, style, and lighting.
            output_path: Local file path where the generated .mp4 should be saved.
            model: Veo model name (defaults to 'veo-3.1-generate-preview').
            duration_seconds: Duration of generated video (typically 5-8 seconds).
            aspect_ratio: "16:9" (widescreen/landscape) or "9:16" (vertical/portrait).
            resolution: Output resolution ("720p" or "1080p").
            enhance_prompt: If True, uses Google's prompt enhancer to optimize instructions.
            poll_interval_seconds: Seconds between status polling requests.
            verbose: If True, prints generation status logs.

        Returns:
            The absolute path of the saved video file.
        """
        selected_model = model or self.DEFAULT_MODEL

        if verbose:
            print(f"[Google Flow] Initiating video generation job...")
            print(f"  - Model: {selected_model}")
            print(f"  - Prompt: '{prompt}'")
            print(f"  - Aspect Ratio: {aspect_ratio}, Duration: {duration_seconds}s, Resolution: {resolution}")
            print(f"  - Prompt Enhancement: {enhance_prompt}")

        config = types.GenerateVideosConfig(
            number_of_videos=1,
            duration_seconds=duration_seconds,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            enhance_prompt=enhance_prompt,
        )

        # Trigger long-running video generation
        operation = self.client.models.generate_videos(
            model=selected_model,
            prompt=prompt,
            config=config,
        )

        if verbose:
            print(f"[Google Flow] Operation started (ID: {operation.name}). Polling for completion...")

        start_time = time.time()
        # Poll until complete
        while not operation.done:
            time.sleep(poll_interval_seconds)
            operation = self.client.operations.get(operation)
            elapsed = int(time.time() - start_time)
            if verbose:
                print(f"[Google Flow] Still processing... ({elapsed}s elapsed)")

        if operation.error:
            raise RuntimeError(f"Video generation failed: {operation.error}")

        if not operation.response or not operation.response.generated_videos:
            raise RuntimeError("Operation completed but no video was returned in response.")

        # Download and persist the video file
        generated_item = operation.response.generated_videos[0]
        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if verbose:
            print(f"[Google Flow] Video generation successful! Downloading to {output_file}...")

        # Download via the genai Files client
        self.client.files.download(file=generated_item.video, destination=str(output_file))

        if verbose:
            print(f"[Google Flow] Saved video to: {output_file}")

        return str(output_file)

    def generate_from_image(
        self,
        image_path: str,
        prompt: str,
        output_path: str = "image_to_video.mp4",
        model: Optional[str] = None,
        duration_seconds: int = 5,
        aspect_ratio: Literal["16:9", "9:16"] = "16:9",
        resolution: Literal["720p", "1080p"] = "720p",
        poll_interval_seconds: int = 10,
        verbose: bool = True,
    ) -> str:
        """
        Generate a video starting from a reference image with action instructions.

        Args:
            image_path: Path to the starting frame image.
            prompt: Text instruction describing the movement or scene evolution.
            output_path: Local file path where the generated .mp4 should be saved.
            model: Veo model name.
            duration_seconds: Duration of the video.
            aspect_ratio: Aspect ratio for the video.
            resolution: Resolution ("720p" or "1080p").
            poll_interval_seconds: Polling interval.
            verbose: Enable status logs.

        Returns:
            The absolute path of the saved video file.
        """
        selected_model = model or self.DEFAULT_MODEL
        image_file = Path(image_path).resolve()
        if not image_file.exists():
            raise FileNotFoundError(f"Source image not found: {image_path}")

        image_input = types.Image.from_file(location=str(image_file))

        config = types.GenerateVideosConfig(
            number_of_videos=1,
            duration_seconds=duration_seconds,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            enhance_prompt=True,
        )

        source = types.GenerateVideosSource(
            prompt=prompt,
            image=image_input,
        )

        if verbose:
            print(f"[Google Flow] Starting Image-to-Video generation from {image_file.name}...")

        operation = self.client.models.generate_videos(
            model=selected_model,
            source=source,
            config=config,
        )

        start_time = time.time()
        while not operation.done:
            time.sleep(poll_interval_seconds)
            operation = self.client.operations.get(operation)
            elapsed = int(time.time() - start_time)
            if verbose:
                print(f"[Google Flow] Rendering video from image... ({elapsed}s elapsed)")

        if operation.error:
            raise RuntimeError(f"Video generation failed: {operation.error}")

        generated_item = operation.response.generated_videos[0]
        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)

        self.client.files.download(file=generated_item.video, destination=str(output_file))

        if verbose:
            print(f"[Google Flow] Saved image-to-video to: {output_file}")

        return str(output_file)
