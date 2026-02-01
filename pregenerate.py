"""
Pre-generate audio clips for quick launch prompts.

Run this script once to cache audio for the 5 demo prompts.
The cached clips will load in 4-6 seconds each during demos.

Usage:
    python pregenerate.py
"""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from loopism_core import LoopismEngine

# Quick launch prompts to pre-generate
QUICK_PROMPTS = [
    "happy summer vibes",
    "epic cinematic trailer",
    "chill lofi study beats",
    "energetic workout music",
    "ambient night atmosphere",
]

CACHE_DIR = Path("precached")
ITERATIONS = 3
DURATION = 5


def pregenerate_all():
    """Pre-generate audio for all quick prompts."""

    print("\n" + "="*70)
    print("🎵 LOOPISM PRE-GENERATION")
    print("="*70)
    print(f"   Prompts: {len(QUICK_PROMPTS)}")
    print(f"   Iterations per prompt: {ITERATIONS}")
    print(f"   Audio duration: {DURATION}s")
    print("="*70 + "\n")

    # Create cache directory
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Track all cached data
    cache_index = {}

    for i, prompt in enumerate(QUICK_PROMPTS):
        print(f"\n{'─'*50}")
        print(f"PROMPT {i+1}/{len(QUICK_PROMPTS)}: \"{prompt}\"")
        print(f"{'─'*50}\n")

        # Create prompt-specific directory
        prompt_key = prompt.lower().replace(" ", "_")
        prompt_dir = CACHE_DIR / prompt_key
        prompt_dir.mkdir(parents=True, exist_ok=True)

        # Run the engine
        engine = LoopismEngine(
            max_iterations=ITERATIONS,
            audio_duration=DURATION,
            output_dir=str(prompt_dir),
            enable_learning=True  # Still learn from these
        )

        results = engine.run(prompt)

        # Save iteration data
        iterations_data = []
        for iteration in results:
            # Copy audio to cache with consistent naming
            cached_audio_name = f"iter_{iteration.iteration_num}.wav"
            cached_audio_path = prompt_dir / cached_audio_name

            # If audio was saved elsewhere, copy it
            if iteration.audio_path and Path(iteration.audio_path).exists():
                if str(cached_audio_path) != iteration.audio_path:
                    import shutil
                    shutil.copy(iteration.audio_path, cached_audio_path)

            iteration_dict = iteration.to_dict()
            iteration_dict['cached_audio_path'] = str(cached_audio_path)
            iterations_data.append(iteration_dict)

        # Save metadata
        metadata = {
            "prompt": prompt,
            "prompt_key": prompt_key,
            "iterations": ITERATIONS,
            "duration": DURATION,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "comparison_data": engine.get_comparison_data(),
            "iterations_data": iterations_data
        }

        metadata_path = prompt_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        cache_index[prompt] = {
            "prompt_key": prompt_key,
            "path": str(prompt_dir),
            "metadata_path": str(metadata_path)
        }

        print(f"\n✅ Cached: {prompt_dir}")

    # Save cache index
    index_path = CACHE_DIR / "index.json"
    with open(index_path, "w") as f:
        json.dump(cache_index, f, indent=2)

    print(f"\n{'='*70}")
    print("✅ PRE-GENERATION COMPLETE")
    print(f"   Cache directory: {CACHE_DIR}")
    print(f"   Index: {index_path}")
    print(f"   Total prompts cached: {len(cache_index)}")
    print("="*70 + "\n")

    return cache_index


def verify_cache():
    """Verify that cache exists and is valid."""
    index_path = CACHE_DIR / "index.json"

    if not index_path.exists():
        return False, "No cache index found"

    with open(index_path) as f:
        index = json.load(f)

    missing = []
    for prompt, info in index.items():
        metadata_path = Path(info["metadata_path"])
        if not metadata_path.exists():
            missing.append(prompt)
            continue

        with open(metadata_path) as f:
            metadata = json.load(f)

        for it in metadata.get("iterations_data", []):
            audio_path = it.get("cached_audio_path")
            if not audio_path or not Path(audio_path).exists():
                missing.append(f"{prompt} (iter {it.get('iteration_num', '?')})")

    if missing:
        return False, f"Missing: {', '.join(missing)}"

    return True, f"Cache valid: {len(index)} prompts"


if __name__ == "__main__":
    # Check if already cached
    valid, msg = verify_cache()
    if valid:
        print(f"✅ {msg}")
        print("   Run with --force to regenerate")
        import sys
        if "--force" not in sys.argv:
            exit(0)

    pregenerate_all()
