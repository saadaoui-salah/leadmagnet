#!/usr/bin/env python3
"""
Generate AI voiceover for YouTube Shorts using Ollama.

Usage:
    python generate_voiceover.py                          # Generate for all scenes
    python generate_voiceover.py --scene hook             # Generate for specific scene
    python generate_voiceover.py --model llama3.2         # Use specific Ollama model
    python generate_voiceover.py --voice-rpm              # Use ElevenLabs (if configured)

Requirements:
    pip install ollama requests pyttsx3

Ollama setup:
    1. Install Ollama: https://ollama.ai
    2. Pull model: ollama pull llama3.2
    3. Start server: ollama serve
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

# Try to import ollama
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Try to import pyttsx3 for local TTS
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# Try to import requests for ElevenLabs
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# Paths
CONTENT_DIR = Path(__file__).parent.parent
PUBLIC_DIR = CONTENT_DIR / "public" / "audio" / "shorts"
OUTPUT_DIR = CONTENT_DIR / "out" / "audio"

# Scene narration templates
SCENE_NARRATIONS = {
    "hook": {
        "winner-vs-runner-up": "Which of these two Atlanta ZIP codes should you invest in right now?",
        "winner-vs-loser": "This ZIP code is soaring while another one is crashing.",
    },
    "zipA": {
        "winner-vs-runner-up": "The number one ZIP code by investor score in Atlanta.",
        "winner-vs-loser": "The highest-scoring ZIP code in Atlanta right now.",
    },
    "zipB": {
        "winner-vs-runner-up": "The runner-up, still hot but not quite number one.",
        "winner-vs-loser": "The fastest-falling ZIP code in Atlanta.",
    },
    "headToHead": {
        "winner-vs-runner-up": "Both are hot. But only one is investable right now.",
        "winner-vs-loser": "One market is thriving. The other is collapsing.",
    },
    "keyDifference": {
        "winner-vs-runner-up": "This is the edge that separates good from great.",
        "winner-vs-loser": "The spread between these two is where the opportunity lives.",
    },
    "takeaway": {
        "winner-vs-runner-up": "High demand plus compressed inventory equals pricing power.",
        "winner-vs-loser": "When one ZIP drops while another gains, the spread is the opportunity.",
    },
    "cta": {
        "winner-vs-runner-up": "Comment REPORT to get the full ZIP code analysis with investor scores.",
        "winner-vs-loser": "Comment REPORT to get the full ZIP code analysis with investor scores.",
    },
}


def generate_with_ollama(text: str, model: str = "llama3.2") -> bool:
    """Generate speech using Ollama + local TTS."""
    if not OLLAMA_AVAILABLE:
        print("  ✗ ollama not installed. Run: pip install ollama")
        return False

    try:
        # Use Ollama to enhance the script (optional)
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a voiceover script editor. Make the text sound natural for a 3-second video narration. Keep it concise and punchy. Only return the edited text, nothing else.",
                },
                {
                    "role": "user",
                    "content": f"Edit this voiceover script: {text}",
                },
            ],
        )
        enhanced_text = response["message"]["content"]
        print(f"  Enhanced: {enhanced_text}")
        return True
    except Exception as e:
        print(f"  ✗ Ollama error: {e}")
        return False


def generate_with_pyttsx3(text: str, output_path: Path, voice_index: int = 0) -> bool:
    """Generate speech using pyttsx3 (local TTS)."""
    if not PYTTSX3_AVAILABLE:
        print("  ✗ pyttsx3 not installed. Run: pip install pyttsx3")
        return False

    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")

        if voice_index < len(voices):
            engine.setProperty("voice", voices[voice_index].id)

        engine.setProperty("rate", 150)  # Speed
        engine.setProperty("volume", 0.9)

        engine.save_to_file(text, str(output_path))
        engine.runAndWait()
        return True
    except Exception as e:
        print(f"  ✗ pyttsx3 error: {e}")
        return False


def generate_with_edge_tts(text: str, output_path: Path, voice: str = "en-US-GuyNeural") -> bool:
    """Generate speech using edge-tts (free, high quality)."""
    try:
        import asyncio
        import edge_tts

        async def _generate():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))

        asyncio.run(_generate())
        return True
    except ImportError:
        print("  ✗ edge-tts not installed. Run: pip install edge-tts")
        return False
    except Exception as e:
        print(f"  ✗ edge-tts error: {e}")
        return False


def generate_scene_voiceover(
    scene: str,
    mode: str,
    model: str,
    voice: str,
    output_dir: Path,
    use_edge: bool = True,
) -> Path:
    """Generate voiceover for a single scene."""
    text = SCENE_NARRATIONS.get(scene, {}).get(mode, "")
    if not text:
        print(f"  ✗ No narration found for scene: {scene}, mode: {mode}")
        return None

    print(f"\n  Scene: {scene}")
    print(f"  Text: {text}")

    output_path = output_dir / f"{scene}.mp3"

    # Try edge-tts first (best quality, free)
    if use_edge:
        success = generate_with_edge_tts(text, output_path, voice)
        if success:
            print(f"  ✓ Generated: {output_path}")
            return output_path

    # Fallback to pyttsx3
    if PYTTSX3_AVAILABLE:
        success = generate_with_pyttsx3(text, output_path)
        if success:
            print(f"  ✓ Generated: {output_path}")
            return output_path

    # Just save the text script
    script_path = output_dir / f"{scene}.txt"
    script_path.write_text(text)
    print(f"  ✓ Script saved: {script_path}")
    return script_path


def main():
    parser = argparse.ArgumentParser(description="Generate AI voiceover for YouTube Shorts")
    parser.add_argument("--scene", choices=list(SCENE_NARRATIONS.keys()), help="Generate for specific scene")
    parser.add_argument("--mode", default="winner-vs-runner-up", choices=["winner-vs-runner-up", "winner-vs-loser"])
    parser.add_argument("--model", default="llama3.2", help="Ollama model name")
    parser.add_argument("--voice", default="en-US-GuyNeural", help="Edge TTS voice name")
    parser.add_argument("--output-dir", type=Path, help="Output directory")
    parser.add_argument("--no-edge", action="store_true", help="Don't use edge-tts")
    args = parser.parse_args()

    # Create output directories
    public_dir = PUBLIC_DIR
    output_dir = args.output_dir or OUTPUT_DIR
    public_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  YouTube Shorts Voiceover Generator")
    print("=" * 60)
    print(f"  Model: {args.model}")
    print(f"  Voice: {args.voice}")
    print(f"  Mode: {args.mode}")
    print(f"  Output: {output_dir}")

    # Determine which scenes to generate
    scenes = [args.scene] if args.scene else list(SCENE_NARRATIONS.keys())

    print(f"\n  Generating {len(scenes)} scene(s)...")

    for scene in scenes:
        generate_scene_voiceover(
            scene=scene,
            mode=args.mode,
            model=args.model,
            voice=args.voice,
            output_dir=output_dir,
            use_edge=not args.no_edge,
        )

    # Copy to public directory for Remotion
    print(f"\n  Copying to {public_dir}...")
    import shutil
    for scene in scenes:
        src = output_dir / f"{scene}.mp3"
        if src.exists():
            shutil.copy2(src, public_dir / f"{scene}.mp3")
            print(f"    ✓ {scene}.mp3")

    print("\n" + "=" * 60)
    print("  Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
